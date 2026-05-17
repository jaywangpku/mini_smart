from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import os
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

from .config import PROJECT_ROOT
from .models import Candle


PERIOD_MAP = {
    "1min": "Min_1",
    "2min": "Min_2",
    "3min": "Min_3",
    "5min": "Min_5",
    "10min": "Min_10",
    "15min": "Min_15",
    "20min": "Min_20",
    "30min": "Min_30",
    "45min": "Min_45",
    "60min": "Min_60",
    "120min": "Min_120",
    "180min": "Min_180",
    "240min": "Min_240",
    "day": "Day",
    "week": "Week",
    "month": "Month",
}

ADJUST_TYPE_MAP = {
    "no_adjust": "NoAdjust",
    "forward": "ForwardAdjust",
}


def _env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip().strip('"').strip("'")
    return value or None


def _to_float(value: Decimal | float | int | str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_epoch(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.astimezone(timezone.utc).timestamp())


def _normalize_timestamp(timestamp: int, period: str) -> int:
    if period.endswith("min"):
        minutes = int(period.removesuffix("min"))
        bucket = minutes * 60
        return timestamp - (timestamp % bucket)
    return timestamp


class LongbridgeClient:
    def __init__(self) -> None:
        load_dotenv(PROJECT_ROOT / ".env")
        try:
            from longbridge.openapi import Config, QuoteContext
        except ImportError as exc:
            raise RuntimeError("未安装 longbridge SDK，请先执行 pip install -e .") from exc

        self._openapi = __import__("longbridge.openapi", fromlist=["Period", "AdjustType", "TradeSessions"])
        self._ctx = QuoteContext(self._config(Config))

    def _config(self, config_type):
        app_key = _env("LONGPORT_APP_KEY") or _env("LONGBRIDGE_APP_KEY")
        app_secret = _env("LONGPORT_APP_SECRET") or _env("LONGBRIDGE_APP_SECRET")
        access_token = _env("LONGPORT_ACCESS_TOKEN") or _env("LONGBRIDGE_ACCESS_TOKEN")
        http_url = _env("LONGPORT_HTTP_URL") or _env("LONGBRIDGE_HTTP_URL")

        missing = [
            name
            for name, value in (
                ("LONGBRIDGE_APP_KEY / LONGPORT_APP_KEY", app_key),
                ("LONGBRIDGE_APP_SECRET / LONGPORT_APP_SECRET", app_secret),
                ("LONGBRIDGE_ACCESS_TOKEN / LONGPORT_ACCESS_TOKEN", access_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("Longbridge 认证信息缺失: " + ", ".join(missing))

        if http_url:
            return config_type.from_apikey(app_key, app_secret, access_token, http_url)
        return config_type.from_apikey(app_key, app_secret, access_token)

    def _period(self, period: str):
        key = PERIOD_MAP.get(period)
        if not key:
            raise ValueError(f"不支持的 period: {period}")
        return getattr(self._openapi.Period, key)

    def _adjust_type(self, adjust_type: str):
        key = ADJUST_TYPE_MAP.get(adjust_type)
        if not key:
            raise ValueError(f"不支持的 adjust_type: {adjust_type}")
        return getattr(self._openapi.AdjustType, key)

    def _trade_sessions(self, trade_session: str):
        if trade_session != "intraday":
            raise ValueError("第一版仅支持 intraday 交易时段")
        return self._openapi.TradeSessions.Intraday

    def fetch_history_by_offset(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        forward: bool,
        count: int,
        time: datetime | None = None,
        trade_session: str = "intraday",
    ) -> list[Candle]:
        raw = self._ctx.history_candlesticks_by_offset(
            symbol.upper(),
            self._period(period),
            self._adjust_type(adjust_type),
            forward,
            count,
            time,
            self._trade_sessions(trade_session),
        )
        return self._normalize(symbol, period, adjust_type, raw)

    def fetch_recent(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        count: int = 1000,
        trade_session: str = "intraday",
    ) -> list[Candle]:
        raw = self._ctx.candlesticks(
            symbol.upper(),
            self._period(period),
            min(count, 1000),
            self._adjust_type(adjust_type),
            self._trade_sessions(trade_session),
        )
        return self._normalize(symbol, period, adjust_type, raw)

    def _normalize(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        raw_candles: Iterable[object],
    ) -> list[Candle]:
        candles: list[Candle] = []
        for item in raw_candles:
            timestamp = getattr(item, "timestamp")
            epoch = _normalize_timestamp(_to_epoch(timestamp), period)
            candles.append(
                Candle(
                    symbol=symbol.upper(),
                    period=period,
                    adjust_type=adjust_type,
                    timestamp=epoch,
                    open=float(getattr(item, "open")),
                    high=float(getattr(item, "high")),
                    low=float(getattr(item, "low")),
                    close=float(getattr(item, "close")),
                    volume=getattr(item, "volume", None),
                    turnover=_to_float(getattr(item, "turnover", None)),
                )
            )
        return sorted(candles, key=lambda candle: candle.timestamp)

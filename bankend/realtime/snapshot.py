from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from ..schemas import RealtimeSubscription
from ..storage import Storage
from .factor_engine import RealtimeFactorEngine
from .provider import RealtimeProvider
from .strategy_engine import RealtimeStrategyEngine


logger = logging.getLogger(__name__)


class RealtimeSnapshotBuilder:
    def __init__(self, storage: Storage, provider: RealtimeProvider) -> None:
        self._storage = storage
        self._provider = provider
        self._factor_engine = RealtimeFactorEngine(storage)
        self._strategy_engine = RealtimeStrategyEngine(storage)

    def build(self, payload: RealtimeSubscription) -> dict[str, Any]:
        source = "sqlite"
        warning: str | None = None
        limit = max(20, min(payload.warmup_bars, 20000))

        try:
            recent = self._provider.fetch_recent(
                payload.symbol,
                payload.period,
                payload.adjust_type,
                count=min(limit, 1000),
                user_id=payload.user_id,
            )
            self._storage.upsert_candles(recent)
            source = "longbridge"
        except Exception as exc:
            warning = str(exc)
            logger.warning(
                "realtime longbridge fetch failed, fallback to sqlite symbol=%s period=%s adjust=%s error=%s",
                payload.symbol,
                payload.period,
                payload.adjust_type,
                warning,
            )

        candles = self._storage.get_candles(
            symbol=payload.symbol,
            period=payload.period,
            adjust_type=payload.adjust_type,
            limit=limit,
        )

        return {
            "type": "snapshot",
            "status": {
                "symbol": payload.symbol.upper(),
                "period": payload.period,
                "adjust_type": payload.adjust_type,
                "source": source,
                "warning": warning,
                "updated_at": now_iso(),
                "candle_count": len(candles),
            },
            "candles": candles,
            "factors": self._factor_engine.calculate(candles, payload),
            "strategy_result": self._strategy_engine.run(candles, payload),
        }


def empty_snapshot(payload: RealtimeSubscription) -> dict[str, Any]:
    return {
        "type": "snapshot",
        "status": {
            "symbol": payload.symbol.upper(),
            "period": payload.period,
            "adjust_type": payload.adjust_type,
            "source": "-",
            "warning": None,
            "updated_at": None,
            "candle_count": 0,
        },
        "candles": [],
        "factors": [],
        "strategy_result": None,
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


MARKET_TIMEZONES = {
    "US": "America/New_York",
    "HK": "Asia/Hong_Kong",
    "SH": "Asia/Shanghai",
    "SZ": "Asia/Shanghai",
}


def market_timezone(symbol: str) -> ZoneInfo:
    suffix = symbol.upper().rsplit(".", 1)[-1] if "." in symbol else "US"
    return ZoneInfo(MARKET_TIMEZONES.get(suffix, "America/New_York"))


def trading_day(timestamp: int, symbol: str) -> str:
    return datetime.fromtimestamp(timestamp, tz=market_timezone(symbol)).date().isoformat()

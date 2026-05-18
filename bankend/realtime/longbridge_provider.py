from __future__ import annotations

from ..longbridge_client import LongbridgeClient
from ..models import Candle
from .provider import RealtimeProvider


class LongbridgePollingProvider(RealtimeProvider):
    def fetch_recent(self, symbol: str, period: str, adjust_type: str, count: int) -> list[Candle]:
        return LongbridgeClient().fetch_recent(symbol, period, adjust_type, count=count)

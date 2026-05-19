from __future__ import annotations

import logging
import threading

from ..longbridge_client import LongbridgeClient
from ..models import Candle
from .provider import RealtimeProvider


logger = logging.getLogger(__name__)


class LongbridgePollingProvider(RealtimeProvider):
    def __init__(self) -> None:
        self._client: LongbridgeClient | None = None
        self._lock = threading.Lock()

    def _get_client(self) -> LongbridgeClient:
        if self._client is not None:
            return self._client
        with self._lock:
            if self._client is None:
                logger.info("initializing longbridge realtime quote client")
                self._client = LongbridgeClient()
        return self._client

    def fetch_recent(self, symbol: str, period: str, adjust_type: str, count: int) -> list[Candle]:
        logger.info(
            "fetch realtime candles from longbridge symbol=%s period=%s adjust=%s count=%s",
            symbol,
            period,
            adjust_type,
            count,
        )
        return self._get_client().fetch_recent(symbol, period, adjust_type, count=count)

from __future__ import annotations

import logging
import threading

from ..longbridge_client import LongbridgeClient
from ..models import Candle
from ..storage import Storage
from .provider import RealtimeProvider


logger = logging.getLogger(__name__)


class LongbridgePollingProvider(RealtimeProvider):
    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._clients: dict[str, LongbridgeClient] = {}
        self._lock = threading.Lock()

    def _get_client(self, user_id: str | None = None) -> LongbridgeClient:
        credentials = self._storage.get_user_api_key(user_id, masked=False) if user_id else None
        cache_key = self._cache_key(user_id, credentials)
        if cache_key in self._clients:
            return self._clients[cache_key]
        with self._lock:
            if cache_key not in self._clients:
                logger.info("initializing longbridge realtime quote client user_id=%s has_user_key=%s", user_id, bool(credentials))
                self._clients[cache_key] = LongbridgeClient(credentials)
        return self._clients[cache_key]

    def fetch_recent(self, symbol: str, period: str, adjust_type: str, count: int, user_id: str | None = None) -> list[Candle]:
        logger.info(
            "fetch realtime candles from longbridge user_id=%s symbol=%s period=%s adjust=%s count=%s",
            user_id,
            symbol,
            period,
            adjust_type,
            count,
        )
        return self._get_client(user_id).fetch_recent(symbol, period, adjust_type, count=count)

    def _cache_key(self, user_id: str | None, credentials: dict | None) -> str:
        if not credentials:
            return "env"
        return ":".join(
            [
                user_id or "env",
                str(credentials.get("updated_at") or ""),
                str(credentials.get("app_key") or ""),
                str(credentials.get("http_url") or ""),
            ]
        )

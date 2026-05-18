from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Candle


class RealtimeProvider(ABC):
    @abstractmethod
    def fetch_recent(self, symbol: str, period: str, adjust_type: str, count: int) -> list[Candle]:
        raise NotImplementedError

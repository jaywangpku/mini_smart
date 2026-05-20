from __future__ import annotations

from ..schemas import RealtimeSubscription
from ..storage import Storage
from ..strategies import run_custom_strategy
from .params import merged_params


class RealtimeStrategyEngine:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def run(self, candles: list[dict], payload: RealtimeSubscription) -> dict | None:
        if not payload.strategy_id:
            return None
        strategy = self._storage.get_custom_strategy(payload.strategy_id, user_id=payload.user_id)
        if strategy is None:
            return None
        return run_custom_strategy(
            strategy["source_code"],
            candles,
            merged_params(strategy, payload.strategy_params),
            self._storage.list_custom_factors(enabled_only=True, user_id=payload.user_id),
            payload.backtest.dict(),
        )

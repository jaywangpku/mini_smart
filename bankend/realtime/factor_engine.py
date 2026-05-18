from __future__ import annotations

from typing import Any

from ..factors.custom_runner import run_custom_factor
from ..schemas import RealtimeSubscription
from ..storage import Storage
from .params import merged_params


class RealtimeFactorEngine:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def calculate(self, candles: list[dict], payload: RealtimeSubscription) -> list[dict]:
        by_time: dict[int, dict[str, Any]] = {}

        for factor_key in payload.factor_ids:
            factor_id = factor_key.removeprefix("custom:")
            factor = self._storage.get_custom_factor(factor_id)
            if factor is None:
                continue
            params = merged_params(
                factor,
                payload.factor_params.get(factor_key) or payload.factor_params.get(factor_id) or {},
            )
            values = run_custom_factor(factor["source_code"], candles, params)
            for row in values:
                time = int(row["time"])
                point = by_time.setdefault(time, {"time": time})
                point[factor_key] = row.get("value")

        return [by_time[key] for key in sorted(by_time)]

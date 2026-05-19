from __future__ import annotations

import json
import logging
import math
import multiprocessing as mp
import statistics
import time
import traceback
from queue import Empty
from typing import Any

from ..factors.custom_runner import ALLOWED_BUILTINS, _normalize_points
from .backtest import run_backtest


logger = logging.getLogger(__name__)


def run_custom_strategy(
    source_code: str,
    candles: list[dict],
    params: dict[str, Any],
    custom_factors: list[dict],
    backtest_options: dict[str, Any] | None = None,
    timeout_seconds: float = 15.0,
) -> dict:
    started = time.perf_counter()
    logger.info(
        "run custom strategy start candles=%s params_keys=%s factors=%s",
        len(candles),
        sorted(params.keys()),
        [row.get("code") for row in custom_factors],
    )
    queue: mp.Queue = mp.Queue(maxsize=1)
    process = mp.Process(target=_worker, args=(source_code, candles, params, custom_factors, backtest_options or {}, queue))
    process.start()
    try:
        status, payload = queue.get(timeout=timeout_seconds)
    except Empty as exc:
        process.terminate()
        process.join(0.2)
        logger.exception("run custom strategy timeout after %.2fs", timeout_seconds)
        raise TimeoutError("自定义策略执行超时") from exc
    process.join(0.2)

    if status == "error":
        logger.error("run custom strategy failed elapsed=%.3fs error=%s", time.perf_counter() - started, payload)
        raise RuntimeError(str(payload))
    logger.info(
        "run custom strategy success elapsed=%.3fs signals=%s trades=%s",
        time.perf_counter() - started,
        len(payload.get("signals", [])) if isinstance(payload, dict) else "-",
        len(payload.get("trades", [])) if isinstance(payload, dict) else "-",
    )
    return payload


class StrategyContext:
    def __init__(self, candles: list[dict], custom_factors: list[dict]):
        self.candles = candles
        self.open = [row["open"] for row in candles]
        self.high = [row["high"] for row in candles]
        self.low = [row["low"] for row in candles]
        self.close = [row["close"] for row in candles]
        self.volume = [row.get("volume") for row in candles]
        self.turnover = [row.get("turnover") for row in candles]
        self._custom_factors = {row["id"]: row for row in custom_factors}
        self._custom_factors.update({row["code"]: row for row in custom_factors})
        self._cache: dict[str, list[dict]] = {}

    def factor(self, code: str, params: dict[str, Any] | None = None) -> list[dict]:
        params = params or {}
        cache_key = f"{code}:{json.dumps(params, sort_keys=True, ensure_ascii=False)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        factor_code = code.removeprefix("custom:")
        factor = self._custom_factors.get(factor_code)
        if factor is None:
            logger.warning("strategy factor missing requested=%s available=%s", code, sorted(self._custom_factors.keys()))
            raise ValueError(f"找不到因子: {code}")
        base = _json_object(factor.get("default_params") or "{}")
        result = _run_factor_inline(factor["source_code"], self.candles, {**base, **params})

        self._cache[cache_key] = result
        return result


def _worker(
    source_code: str,
    candles: list[dict],
    params: dict[str, Any],
    custom_factors: list[dict],
    backtest_options: dict[str, Any],
    queue: mp.Queue,
) -> None:
    globals_dict = {
        "__builtins__": ALLOWED_BUILTINS,
        "math": math,
        "statistics": statistics,
    }
    locals_dict: dict[str, Any] = {}
    try:
        exec(source_code, globals_dict, locals_dict)
        generate_signals = locals_dict.get("generate_signals") or globals_dict.get("generate_signals")
        if not callable(generate_signals):
            raise ValueError("代码必须定义 generate_signals(ctx, params) 函数")
        ctx = StrategyContext(candles, custom_factors)
        raw_signals = generate_signals(ctx, params)
        signals = _normalize_signals(raw_signals, candles)
        queue.put(("ok", run_backtest(candles, signals, backtest_options)))
    except Exception as exc:
        logger.error("custom strategy worker failed\n%s", traceback.format_exc())
        queue.put(("error", f"{type(exc).__name__}: {exc}"))


def _normalize_signals(raw: Any, candles: list[dict]) -> list[dict]:
    if not isinstance(raw, list):
        raise ValueError("generate_signals 必须返回 list")

    valid_times = {int(row["time"]) for row in candles}
    signals: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("策略信号列表中的每一项必须是 dict")
        if "time" not in item:
            raise ValueError("策略信号缺少 time 字段")
        time = int(item["time"])
        if time not in valid_times:
            continue
        action = str(item.get("action", "")).lower()
        if action not in {"buy", "sell"}:
            raise ValueError("策略信号 action 只能是 buy 或 sell")
        quantity = float(item.get("quantity") or 0)
        if not math.isfinite(quantity) or quantity <= 0:
            continue
        price = item.get("price")
        signals.append(
            {
                "time": time,
                "action": action,
                "quantity": quantity,
                "price": float(price) if price is not None else None,
                "reason": str(item.get("reason") or ""),
            }
        )
    return sorted(signals, key=lambda row: row["time"])


def _run_factor_inline(source_code: str, candles: list[dict], params: dict[str, Any]) -> list[dict]:
    logger.info("run inline factor start candles=%s params_keys=%s", len(candles), sorted(params.keys()))
    globals_dict = {
        "__builtins__": ALLOWED_BUILTINS,
        "math": math,
        "statistics": statistics,
    }
    locals_dict: dict[str, Any] = {}
    exec(source_code, globals_dict, locals_dict)
    compute = locals_dict.get("compute") or globals_dict.get("compute")
    if not callable(compute):
        raise ValueError("因子代码必须定义 compute(candles, params) 函数")
    result = _normalize_points(compute(candles, params), candles)
    logger.info("run inline factor success points=%s", len(result))
    return result


def _json_object(raw: str) -> dict:
    value = json.loads(raw or "{}")
    if not isinstance(value, dict):
        raise ValueError("参数必须是 JSON object")
    return value

from __future__ import annotations

import math
import multiprocessing as mp
import logging
import statistics
import time
import traceback
from queue import Empty
from typing import Any


logger = logging.getLogger(__name__)


ALLOWED_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "sum": sum,
    "zip": zip,
}


def run_custom_factor(source_code: str, candles: list[dict], params: dict[str, Any], timeout_seconds: float = 2.0) -> list[dict]:
    started = time.perf_counter()
    logger.info("run custom factor start candles=%s params_keys=%s", len(candles), sorted(params.keys()))
    queue: mp.Queue = mp.Queue(maxsize=1)
    process = mp.Process(target=_worker, args=(source_code, candles, params, queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(0.2)
        logger.exception("run custom factor timeout after %.2fs", timeout_seconds)
        raise TimeoutError("自定义因子执行超时")

    try:
        status, payload = queue.get_nowait()
    except Empty as exc:
        logger.exception("run custom factor returned no payload")
        raise RuntimeError("自定义因子没有返回结果") from exc

    if status == "error":
        logger.error("run custom factor failed elapsed=%.3fs error=%s", time.perf_counter() - started, payload)
        raise RuntimeError(str(payload))
    result = _normalize_points(payload, candles)
    logger.info("run custom factor success elapsed=%.3fs points=%s", time.perf_counter() - started, len(result))
    return result


def _worker(source_code: str, candles: list[dict], params: dict[str, Any], queue: mp.Queue) -> None:
    globals_dict = {
        "__builtins__": ALLOWED_BUILTINS,
        "math": math,
        "statistics": statistics,
    }
    locals_dict: dict[str, Any] = {}
    try:
        exec(source_code, globals_dict, locals_dict)
        compute = locals_dict.get("compute") or globals_dict.get("compute")
        if not callable(compute):
            raise ValueError("代码必须定义 compute(candles, params) 函数")
        result = compute(candles, params)
        queue.put(("ok", result))
    except Exception as exc:
        logger.error("custom factor worker failed\n%s", traceback.format_exc())
        queue.put(("error", f"{type(exc).__name__}: {exc}"))


def _normalize_points(raw: Any, candles: list[dict]) -> list[dict]:
    if not isinstance(raw, list):
        raise ValueError("compute 必须返回 list")

    valid_times = {int(row["time"]) for row in candles}
    points: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("compute 返回列表中的每一项必须是 dict")
        if "time" not in item:
            raise ValueError("因子点缺少 time 字段")
        time = int(item["time"])
        if time not in valid_times:
            continue
        value = item.get("value")
        if value is None:
            points.append({"time": time, "value": None})
            continue
        number = float(value)
        if not math.isfinite(number):
            points.append({"time": time, "value": None})
            continue
        points.append({"time": time, "value": number})

    return sorted(points, key=lambda row: row["time"])

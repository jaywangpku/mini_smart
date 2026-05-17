from __future__ import annotations

import json
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pydantic import BaseModel

from .config import load_settings
from .factors.custom_runner import run_custom_factor
from .factors import compute_derivative_factors
from .longbridge_client import LongbridgeClient
from .models import SyncRequest
from .storage import Storage
from .strategies import run_custom_strategy
from .sync import TaskRunner, parse_date_or_datetime


settings = load_settings()
storage = Storage(settings.db_path)
app = FastAPI(title="mini_smart API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SymbolCreate(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None


class SymbolPatch(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None
    market: Optional[str] = None


class PoolCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PoolPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PoolSymbolCreate(BaseModel):
    symbol: str
    name: Optional[str] = None
    note: Optional[str] = None


class PoolSymbolPatch(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None
    market: Optional[str] = None


class CustomFactorCreate(BaseModel):
    code: str
    name: str
    source_code: str
    description: Optional[str] = None
    default_params: dict = {}
    enabled: bool = True


class CustomFactorPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    source_code: Optional[str] = None
    description: Optional[str] = None
    default_params: Optional[dict] = None
    enabled: Optional[bool] = None


class CustomFactorPreview(BaseModel):
    symbol: str
    period: str = "1min"
    adjust_type: str = "forward"
    params: dict = {}
    limit: int = 200


class CustomStrategyCreate(BaseModel):
    code: str
    name: str
    source_code: str
    description: Optional[str] = None
    default_params: dict = {}
    enabled: bool = True


class CustomStrategyPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    source_code: Optional[str] = None
    description: Optional[str] = None
    default_params: Optional[dict] = None
    enabled: Optional[bool] = None


class BacktestOptions(BaseModel):
    initial_cash: float = 100000
    fee_rate: float = 0.0003
    slippage_rate: float = 0.0002


class CustomStrategyRun(BaseModel):
    symbol: str
    period: str = "1min"
    adjust_type: str = "forward"
    params: dict = {}
    limit: int = 1000
    start: Optional[int] = None
    end: Optional[int] = None
    backtest: BacktestOptions = BacktestOptions()


class BatchSyncCreate(BaseModel):
    symbols: list[str]
    period: str = "1min"
    adjust_type: str = "forward"
    start: Optional[str] = None
    end: Optional[str] = None
    trade_session: str = "intraday"

    def requests(self) -> list[SyncRequest]:
        return [
            SyncRequest(
                symbol=symbol.upper(),
                period=self.period,
                adjust_type=self.adjust_type,
                start=parse_date_or_datetime(self.start),
                end=parse_date_or_datetime(self.end),
                trade_session=self.trade_session,
            )
            for symbol in self.symbols
        ]


class SyncCreate(BaseModel):
    symbol: str
    period: str = "1min"
    adjust_type: str = "no_adjust"
    start: Optional[str] = None
    end: Optional[str] = None
    trade_session: str = "intraday"

    def to_request(self) -> SyncRequest:
        return SyncRequest(
            symbol=self.symbol.upper(),
            period=self.period,
            adjust_type=self.adjust_type,
            start=parse_date_or_datetime(self.start),
            end=parse_date_or_datetime(self.end),
            trade_session=self.trade_session,
        )


ALL_SYNC_PERIODS = ["1min", "5min", "15min", "30min", "60min", "day"]


@app.on_event("startup")
def startup() -> None:
    storage.init_db()


@app.post("/api/db/init")
def init_db() -> dict:
    storage.init_db()
    return {"ok": True, "db_path": str(settings.db_path)}


@app.get("/api/symbols")
def list_symbols() -> list[dict]:
    storage.init_db()
    return storage.list_symbols()


@app.post("/api/symbols")
def add_symbol(payload: SymbolCreate) -> dict:
    storage.init_db()
    return storage.add_symbol(payload.symbol, payload.name, payload.market)


@app.patch("/api/symbols/{symbol}")
def patch_symbol(symbol: str, payload: SymbolPatch) -> dict:
    result = storage.update_symbol(symbol, name=payload.name, market=payload.market, enabled=payload.enabled)
    if result is None:
        raise HTTPException(status_code=404, detail="symbol not found")
    return result


@app.get("/api/securities")
def search_securities(
    market: str = Query("US", description="US/HK/CN/SG"),
    q: str = Query("", description="股票代码或名称关键字"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    try:
        return LongbridgeClient().search_securities(market=market, query=q, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/securities/{symbol}")
def get_security_info(symbol: str) -> dict:
    try:
        result = LongbridgeClient().static_info(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="security not found")
    return result


@app.get("/api/pools")
def list_pools() -> list[dict]:
    storage.init_db()
    return storage.list_pools()


@app.post("/api/pools")
def create_pool(payload: PoolCreate) -> dict:
    storage.init_db()
    return storage.create_pool(payload.name, payload.description)


@app.patch("/api/pools/{pool_id}")
def patch_pool(pool_id: str, payload: PoolPatch) -> dict:
    result = storage.update_pool(pool_id, payload.name, payload.description)
    if result is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return result


@app.delete("/api/pools/{pool_id}")
def delete_pool(pool_id: str) -> dict:
    deleted = storage.delete_pool(pool_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="pool cannot be deleted or not found")
    return {"ok": True}


@app.get("/api/pools/{pool_id}/symbols")
def list_pool_symbols(pool_id: str, enabled_only: bool = False) -> list[dict]:
    storage.init_db()
    if storage.get_pool(pool_id) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return storage.list_pool_symbols(pool_id, enabled_only=enabled_only)


@app.post("/api/pools/{pool_id}/symbols")
def add_pool_symbol(pool_id: str, payload: PoolSymbolCreate) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return storage.add_pool_symbol(pool_id, payload.symbol, payload.note, payload.name)


@app.patch("/api/pools/{pool_id}/symbols/{symbol}")
def patch_pool_symbol(pool_id: str, symbol: str, payload: PoolSymbolPatch) -> dict:
    if payload.enabled is not None:
        result = storage.set_pool_symbol_enabled(pool_id, symbol, payload.enabled)
    else:
        result = storage.get_pool_symbol(pool_id, symbol)
    if result is None:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    if payload.name is not None or payload.market is not None:
        storage.update_symbol(symbol, name=payload.name, market=payload.market)
        result = storage.get_pool_symbol(pool_id, symbol)
    if result is None:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    return result


@app.delete("/api/pools/{pool_id}/symbols/{symbol}")
def delete_pool_symbol(pool_id: str, symbol: str) -> dict:
    deleted = storage.remove_pool_symbol(pool_id, symbol)
    if not deleted:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    return {"ok": True}


@app.get("/api/factors/custom")
def list_custom_factors(enabled_only: bool = False) -> list[dict]:
    storage.init_db()
    return storage.list_custom_factors(enabled_only=enabled_only)


@app.post("/api/factors/custom")
def create_custom_factor(payload: CustomFactorCreate) -> dict:
    storage.init_db()
    try:
        return storage.create_custom_factor(
            code=payload.code.strip(),
            name=payload.name.strip(),
            description=payload.description,
            source_code=payload.source_code,
            default_params=json.dumps(payload.default_params, ensure_ascii=False),
            enabled=payload.enabled,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/factors/custom/{factor_id}")
def patch_custom_factor(factor_id: str, payload: CustomFactorPatch) -> dict:
    storage.init_db()
    result = storage.update_custom_factor(
        factor_id,
        code=payload.code.strip() if payload.code is not None else None,
        name=payload.name.strip() if payload.name is not None else None,
        description=payload.description,
        source_code=payload.source_code,
        default_params=json.dumps(payload.default_params, ensure_ascii=False) if payload.default_params is not None else None,
        enabled=payload.enabled,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="custom factor not found")
    return result


@app.delete("/api/factors/custom/{factor_id}")
def delete_custom_factor(factor_id: str) -> dict:
    storage.init_db()
    deleted = storage.delete_custom_factor(factor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="custom factor not found")
    return {"ok": True}


@app.get("/api/strategies/custom")
def list_custom_strategies(enabled_only: bool = False) -> list[dict]:
    storage.init_db()
    return storage.list_custom_strategies(enabled_only=enabled_only)


@app.post("/api/strategies/custom")
def create_custom_strategy(payload: CustomStrategyCreate) -> dict:
    storage.init_db()
    try:
        return storage.create_custom_strategy(
            code=payload.code.strip(),
            name=payload.name.strip(),
            description=payload.description,
            source_code=payload.source_code,
            default_params=json.dumps(payload.default_params, ensure_ascii=False),
            enabled=payload.enabled,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/strategies/custom/{strategy_id}")
def patch_custom_strategy(strategy_id: str, payload: CustomStrategyPatch) -> dict:
    storage.init_db()
    result = storage.update_custom_strategy(
        strategy_id,
        code=payload.code.strip() if payload.code is not None else None,
        name=payload.name.strip() if payload.name is not None else None,
        description=payload.description,
        source_code=payload.source_code,
        default_params=json.dumps(payload.default_params, ensure_ascii=False) if payload.default_params is not None else None,
        enabled=payload.enabled,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="custom strategy not found")
    return result


@app.delete("/api/strategies/custom/{strategy_id}")
def delete_custom_strategy(strategy_id: str) -> dict:
    storage.init_db()
    deleted = storage.delete_custom_strategy(strategy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="custom strategy not found")
    return {"ok": True}


@app.post("/api/strategies/custom/{strategy_id}/run")
def run_strategy(strategy_id: str, payload: CustomStrategyRun) -> dict:
    strategy = storage.get_custom_strategy(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="custom strategy not found")
    candles = storage.get_candles(
        symbol=payload.symbol,
        period=payload.period,
        adjust_type=payload.adjust_type,
        limit=max(1, min(payload.limit, 20000)),
        start_ts=payload.start,
        end_ts=payload.end,
    )
    params = _merged_default_params(strategy, payload.params)
    try:
        return run_custom_strategy(
            strategy["source_code"],
            candles,
            params,
            storage.list_custom_factors(enabled_only=True),
            payload.backtest.dict(),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/factors/custom/{factor_id}/preview")
def preview_custom_factor(factor_id: str, payload: CustomFactorPreview) -> list[dict]:
    factor = storage.get_custom_factor(factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="custom factor not found")
    candles = storage.get_candles(
        symbol=payload.symbol,
        period=payload.period,
        adjust_type=payload.adjust_type,
        limit=max(1, min(payload.limit, 1000)),
    )
    params = _merged_factor_params(factor, payload.params)
    try:
        return run_custom_factor(factor["source_code"], candles, params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sync")
def create_sync_task(payload: SyncCreate, background_tasks: BackgroundTasks) -> dict:
    storage.init_db()
    request = payload.to_request()
    runner = TaskRunner(storage)
    task_id, created = runner.enqueue(request)
    if created:
        background_tasks.add_task(runner.run_task, task_id, request)
    task = storage.get_task(task_id)
    return {"task_id": task_id, "status": task["status"] if task else "queued", "created": created}


@app.post("/api/sync/batch")
def create_batch_sync_task(payload: BatchSyncCreate, background_tasks: BackgroundTasks) -> dict:
    storage.init_db()
    runner = TaskRunner(storage)
    tasks = []
    for request in payload.requests():
        task_id, created = runner.enqueue(request)
        if created:
            background_tasks.add_task(runner.run_task, task_id, request)
        task = storage.get_task(task_id)
        tasks.append({"task_id": task_id, "symbol": request.symbol, "status": task["status"] if task else "queued", "created": created})
    return {"tasks": tasks}


@app.post("/api/pools/{pool_id}/sync")
def sync_pool(pool_id: str, payload: SyncCreate, background_tasks: BackgroundTasks) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    symbols = [row["symbol"] for row in storage.list_pool_symbols(pool_id, enabled_only=True)]
    batch = BatchSyncCreate(
        symbols=symbols,
        period=payload.period,
        adjust_type=payload.adjust_type,
        start=payload.start,
        end=payload.end,
        trade_session=payload.trade_session,
    )
    return create_batch_sync_task(batch, background_tasks)


@app.post("/api/pools/{pool_id}/sync/all-periods")
def sync_pool_all_periods(pool_id: str, payload: SyncCreate, background_tasks: BackgroundTasks) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    symbols = [row["symbol"] for row in storage.list_pool_symbols(pool_id, enabled_only=True)]
    runner = TaskRunner(storage)
    tasks = []
    for period in ALL_SYNC_PERIODS:
        batch = BatchSyncCreate(
            symbols=symbols,
            period=period,
            adjust_type=payload.adjust_type,
            start=payload.start,
            end=payload.end,
            trade_session=payload.trade_session,
        )
        for request in batch.requests():
            task_id, created = runner.enqueue(request)
            if created:
                background_tasks.add_task(runner.run_task, task_id, request)
            task = storage.get_task(task_id)
            tasks.append({
                "task_id": task_id,
                "symbol": request.symbol,
                "period": request.period,
                "status": task["status"] if task else "queued",
                "created": created,
            })
    return {"tasks": tasks}


@app.get("/api/sync/tasks")
def list_tasks(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return storage.list_tasks(limit=limit)


@app.get("/api/sync/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    task = storage.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.get("/api/sync/status")
def sync_status() -> list[dict]:
    return storage.list_sync_state()


@app.get("/api/candles")
def get_candles(
    symbol: str,
    period: str = "1min",
    adjust_type: str = "no_adjust",
    limit: int = Query(default=1000, ge=1, le=20000),
    start: Optional[int] = None,
    end: Optional[int] = None,
    latest_session: bool = False,
) -> list[dict]:
    if latest_session:
        return storage.get_latest_session_candles(
            symbol=symbol,
            period=period,
            adjust_type=adjust_type,
            limit=limit,
        )
    return storage.get_candles(
        symbol=symbol,
        period=period,
        adjust_type=adjust_type,
        limit=limit,
        start_ts=start,
        end_ts=end,
    )


@app.get("/api/factors/derivative")
def get_derivative_factor(
    symbol: str,
    period: str = "1min",
    adjust_type: str = "forward",
    n: int = Query(default=5, ge=1, le=240),
    m: int = Query(default=5, ge=1, le=240),
    limit: int = Query(default=2000, ge=1, le=20000),
    start: Optional[int] = None,
    end: Optional[int] = None,
    latest_session: bool = False,
) -> list[dict]:
    if latest_session:
        candles = storage.get_latest_session_candles(symbol, period, adjust_type, limit=limit)
    else:
        candles = storage.get_candles(
            symbol=symbol,
            period=period,
            adjust_type=adjust_type,
            limit=limit,
            start_ts=start,
            end_ts=end,
        )
    points = compute_derivative_factors(candles, symbol=symbol, n_minutes=n, m_minutes=m, reset_daily=period != "day")
    return [
        {
            "time": point.time,
            "first_derivative": point.first_derivative,
            "second_derivative": point.second_derivative,
        }
        for point in points
    ]


@app.get("/api/factors/custom/{factor_id}/values")
def get_custom_factor_values(
    factor_id: str,
    symbol: str,
    period: str = "1min",
    adjust_type: str = "forward",
    params: str = "{}",
    limit: int = Query(default=2000, ge=1, le=20000),
    start: Optional[int] = None,
    end: Optional[int] = None,
    latest_session: bool = False,
) -> list[dict]:
    factor = storage.get_custom_factor(factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="custom factor not found")
    if latest_session:
        candles = storage.get_latest_session_candles(symbol, period, adjust_type, limit=limit)
    else:
        candles = storage.get_candles(
            symbol=symbol,
            period=period,
            adjust_type=adjust_type,
            limit=limit,
            start_ts=start,
            end_ts=end,
        )
    try:
        return run_custom_factor(factor["source_code"], candles, _merged_factor_params(factor, _json_object(params)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _json_object(raw: str) -> dict:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"参数 JSON 不合法: {exc}") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail="参数必须是 JSON object")
    return value


def _merged_factor_params(factor: dict, override: dict) -> dict:
    base = _json_object(factor.get("default_params") or "{}")
    return {**base, **override}


def _merged_default_params(row: dict, override: dict) -> dict:
    base = _json_object(row.get("default_params") or "{}")
    return {**base, **override}

from __future__ import annotations

from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pydantic import BaseModel

from .config import load_settings
from .factors import compute_derivative_factors
from .models import SyncRequest
from .storage import Storage
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
    enabled: bool


class PoolCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PoolPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PoolSymbolCreate(BaseModel):
    symbol: str
    note: Optional[str] = None


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
    result = storage.set_symbol_enabled(symbol, payload.enabled)
    if result is None:
        raise HTTPException(status_code=404, detail="symbol not found")
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
    return storage.add_pool_symbol(pool_id, payload.symbol, payload.note)


@app.patch("/api/pools/{pool_id}/symbols/{symbol}")
def patch_pool_symbol(pool_id: str, symbol: str, payload: SymbolPatch) -> dict:
    result = storage.set_pool_symbol_enabled(pool_id, symbol, payload.enabled)
    if result is None:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    return result


@app.delete("/api/pools/{pool_id}/symbols/{symbol}")
def delete_pool_symbol(pool_id: str, symbol: str) -> dict:
    deleted = storage.remove_pool_symbol(pool_id, symbol)
    if not deleted:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    return {"ok": True}


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
    points = compute_derivative_factors(candles, symbol=symbol, n_minutes=n, m_minutes=m)
    return [
        {
            "time": point.time,
            "first_derivative": point.first_derivative,
            "second_derivative": point.second_derivative,
        }
        for point in points
    ]

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query

from .config import load_settings
from .auth import create_token, decode_token, hash_password, verify_password
from .factors.custom_runner import run_custom_factor
from .longbridge_client import LongbridgeClient
from .schemas import (
    BatchSyncCreate,
    ApiKeyPatch,
    AdminPasswordReset,
    CustomFactorCreate,
    CustomFactorPatch,
    CustomFactorPreview,
    CustomStrategyCreate,
    CustomStrategyPatch,
    CustomStrategyRun,
    LoginRequest,
    PasswordChange,
    PoolCreate,
    PoolPatch,
    PoolSymbolCreate,
    PoolSymbolPatch,
    RealtimeSubscription,
    SymbolCreate,
    SymbolPatch,
    SyncCreate,
    UserCreate,
)
from .storage import Storage
from .realtime import RealtimeManager
from .strategies import run_custom_strategy
from .sync import TaskRunner


logger = logging.getLogger(__name__)
settings = load_settings()
storage = Storage(settings.db_path)
realtime_manager = RealtimeManager(storage)
app = FastAPI(title="mini_smart API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALL_SYNC_PERIODS = ["1min", "5min", "15min", "30min", "60min", "day"]


@app.on_event("startup")
def startup() -> None:
    storage.init_db()


@app.post("/api/db/init")
def init_db() -> dict:
    storage.init_db()
    return {"ok": True, "db_path": str(settings.db_path)}


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token, settings.jwt_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user = storage.get_user(str(payload.get("sub") or ""))
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return user


def _longbridge_client_for_user(user: dict) -> LongbridgeClient:
    credentials = storage.get_user_api_key(user["id"], masked=False)
    logger.info("initializing longbridge client user=%s has_user_key=%s", user.get("username"), bool(credentials))
    return LongbridgeClient(credentials)


@app.post("/api/auth/register")
def register(payload: UserCreate) -> dict:
    storage.init_db()
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    try:
        user = storage.create_user(username, hash_password(payload.password))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    token = create_token({"sub": user["id"], "username": user["username"]}, settings.jwt_secret, settings.token_expire_hours)
    return {"token": token, "user": user}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict:
    storage.init_db()
    user = storage.get_user_by_username(payload.username.strip(), include_hash=True)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    clean = {key: value for key, value in user.items() if key != "password_hash"}
    token = create_token({"sub": user["id"], "username": user["username"]}, settings.jwt_secret, settings.token_expire_hours)
    return {"token": token, "user": clean}


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@app.post("/api/auth/change-password")
def change_password(payload: PasswordChange, user: dict = Depends(current_user)) -> dict:
    current = storage.get_user_by_username(user["username"], include_hash=True)
    if current is None or not verify_password(payload.old_password, current["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")
    storage.update_user_password(user["id"], hash_password(payload.new_password))
    return {"ok": True}


@app.post("/api/auth/admin/reset-password")
def admin_reset_password(payload: AdminPasswordReset, user: dict = Depends(current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可重置密码")
    target = storage.get_user_by_username(payload.username.strip())
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")
    storage.update_user_password(target["id"], hash_password(payload.new_password))
    return {"ok": True}


@app.get("/api/auth/admin/users")
def admin_list_users(user: dict = Depends(current_user)) -> list[dict]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看用户")
    return storage.list_users()


@app.delete("/api/auth/admin/users/{user_id}")
def admin_delete_user(user_id: str, user: dict = Depends(current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除用户")
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    deleted = storage.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"ok": True}


@app.get("/api/me/api-keys/longbridge")
def get_longbridge_key(user: dict = Depends(current_user)) -> dict:
    return storage.get_user_api_key(user["id"]) or {"provider": "longbridge", "configured": False}


@app.put("/api/me/api-keys/longbridge")
def save_longbridge_key(payload: ApiKeyPatch, user: dict = Depends(current_user)) -> dict:
    key = storage.upsert_user_api_key(
        user["id"],
        app_key=payload.app_key.strip(),
        app_secret=payload.app_secret.strip(),
        access_token=payload.access_token.strip(),
        http_url=payload.http_url.strip() if payload.http_url else None,
    )
    return {**storage.get_user_api_key(user["id"]), "configured": True}


@app.delete("/api/me/api-keys/longbridge")
def delete_longbridge_key(user: dict = Depends(current_user)) -> dict:
    storage.delete_user_api_key(user["id"])
    return {"ok": True}


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
    user: dict = Depends(current_user),
) -> list[dict]:
    try:
        return _longbridge_client_for_user(user).search_securities(market=market, query=q, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/securities/{symbol}")
def get_security_info(symbol: str, user: dict = Depends(current_user)) -> dict:
    try:
        result = _longbridge_client_for_user(user).static_info(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="security not found")
    return result


@app.get("/api/pools")
def list_pools(user: dict = Depends(current_user)) -> list[dict]:
    storage.init_db()
    return storage.list_pools(user_id=user["id"])


@app.post("/api/pools")
def create_pool(payload: PoolCreate, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    return storage.create_pool(payload.name, payload.description, user_id=user["id"])


@app.patch("/api/pools/{pool_id}")
def patch_pool(pool_id: str, payload: PoolPatch, user: dict = Depends(current_user)) -> dict:
    result = storage.update_pool(pool_id, payload.name, payload.description, user_id=user["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return result


@app.delete("/api/pools/{pool_id}")
def delete_pool(pool_id: str, user: dict = Depends(current_user)) -> dict:
    deleted = storage.delete_pool(pool_id, user_id=user["id"])
    if not deleted:
        raise HTTPException(status_code=400, detail="pool cannot be deleted or not found")
    return {"ok": True}


@app.get("/api/pools/{pool_id}/symbols")
def list_pool_symbols(pool_id: str, enabled_only: bool = False, user: dict = Depends(current_user)) -> list[dict]:
    storage.init_db()
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return storage.list_pool_symbols(pool_id, enabled_only=enabled_only)


@app.post("/api/pools/{pool_id}/symbols")
def add_pool_symbol(pool_id: str, payload: PoolSymbolCreate, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    return storage.add_pool_symbol(pool_id, payload.symbol, payload.note, payload.name)


@app.patch("/api/pools/{pool_id}/symbols/{symbol}")
def patch_pool_symbol(pool_id: str, symbol: str, payload: PoolSymbolPatch, user: dict = Depends(current_user)) -> dict:
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
        raise HTTPException(status_code=404, detail="pool not found")
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
def delete_pool_symbol(pool_id: str, symbol: str, user: dict = Depends(current_user)) -> dict:
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    deleted = storage.remove_pool_symbol(pool_id, symbol)
    if not deleted:
        raise HTTPException(status_code=404, detail="pool symbol not found")
    return {"ok": True}


@app.get("/api/factors/custom")
def list_custom_factors(enabled_only: bool = False, user: dict = Depends(current_user)) -> list[dict]:
    storage.init_db()
    return storage.list_custom_factors(enabled_only=enabled_only, user_id=user["id"])


@app.post("/api/factors/custom")
def create_custom_factor(payload: CustomFactorCreate, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    try:
        factor = storage.create_custom_factor(
            code=payload.code.strip(),
            name=payload.name.strip(),
            description=payload.description,
            source_code=payload.source_code,
            default_params=json.dumps(payload.default_params, ensure_ascii=False),
            enabled=payload.enabled,
            user_id=user["id"],
        )
        logger.info("custom factor created id=%s code=%s name=%s enabled=%s", factor["id"], factor["code"], factor["name"], factor["enabled"])
        return factor
    except Exception as exc:
        logger.exception("custom factor create failed code=%s name=%s", payload.code, payload.name)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/factors/custom/{factor_id}")
def patch_custom_factor(factor_id: str, payload: CustomFactorPatch, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    result = storage.update_custom_factor(
        factor_id,
        code=payload.code.strip() if payload.code is not None else None,
        name=payload.name.strip() if payload.name is not None else None,
        description=payload.description,
        source_code=payload.source_code,
        default_params=json.dumps(payload.default_params, ensure_ascii=False) if payload.default_params is not None else None,
        enabled=payload.enabled,
        user_id=user["id"],
    )
    if result is None:
        raise HTTPException(status_code=404, detail="custom factor not found")
    logger.info("custom factor updated id=%s code=%s name=%s enabled=%s", result["id"], result["code"], result["name"], result["enabled"])
    return result


@app.delete("/api/factors/custom/{factor_id}")
def delete_custom_factor(factor_id: str, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    deleted = storage.delete_custom_factor(factor_id, user_id=user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="custom factor not found")
    logger.info("custom factor deleted id=%s", factor_id)
    return {"ok": True}


@app.get("/api/strategies/custom")
def list_custom_strategies(enabled_only: bool = False, user: dict = Depends(current_user)) -> list[dict]:
    storage.init_db()
    return storage.list_custom_strategies(enabled_only=enabled_only, user_id=user["id"])


@app.post("/api/strategies/custom")
def create_custom_strategy(payload: CustomStrategyCreate, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    try:
        strategy = storage.create_custom_strategy(
            code=payload.code.strip(),
            name=payload.name.strip(),
            description=payload.description,
            source_code=payload.source_code,
            default_params=json.dumps(payload.default_params, ensure_ascii=False),
            enabled=payload.enabled,
            user_id=user["id"],
        )
        logger.info("custom strategy created id=%s code=%s name=%s enabled=%s", strategy["id"], strategy["code"], strategy["name"], strategy["enabled"])
        return strategy
    except Exception as exc:
        logger.exception("custom strategy create failed code=%s name=%s", payload.code, payload.name)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/strategies/custom/{strategy_id}")
def patch_custom_strategy(strategy_id: str, payload: CustomStrategyPatch, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    result = storage.update_custom_strategy(
        strategy_id,
        code=payload.code.strip() if payload.code is not None else None,
        name=payload.name.strip() if payload.name is not None else None,
        description=payload.description,
        source_code=payload.source_code,
        default_params=json.dumps(payload.default_params, ensure_ascii=False) if payload.default_params is not None else None,
        enabled=payload.enabled,
        user_id=user["id"],
    )
    if result is None:
        raise HTTPException(status_code=404, detail="custom strategy not found")
    logger.info("custom strategy updated id=%s code=%s name=%s enabled=%s", result["id"], result["code"], result["name"], result["enabled"])
    return result


@app.delete("/api/strategies/custom/{strategy_id}")
def delete_custom_strategy(strategy_id: str, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    deleted = storage.delete_custom_strategy(strategy_id, user_id=user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="custom strategy not found")
    logger.info("custom strategy deleted id=%s", strategy_id)
    return {"ok": True}


@app.post("/api/strategies/custom/{strategy_id}/run")
def run_strategy(strategy_id: str, payload: CustomStrategyRun, user: dict = Depends(current_user)) -> dict:
    strategy = storage.get_custom_strategy(strategy_id, user_id=user["id"])
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
    logger.info(
        "custom strategy run start id=%s code=%s name=%s symbol=%s period=%s adjust=%s candles=%s params_keys=%s",
        strategy_id,
        strategy["code"],
        strategy["name"],
        payload.symbol,
        payload.period,
        payload.adjust_type,
        len(candles),
        sorted(params.keys()),
    )
    try:
        result = run_custom_strategy(
            strategy["source_code"],
            candles,
            params,
            storage.list_custom_factors(enabled_only=True, user_id=user["id"]),
            payload.backtest.dict(),
        )
        logger.info(
            "custom strategy run success id=%s signals=%s trades=%s",
            strategy_id,
            len(result.get("signals", [])),
            len(result.get("trades", [])),
        )
        return result
    except Exception as exc:
        logger.exception("custom strategy run failed id=%s code=%s name=%s", strategy_id, strategy["code"], strategy["name"])
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/factors/custom/{factor_id}/preview")
def preview_custom_factor(factor_id: str, payload: CustomFactorPreview, user: dict = Depends(current_user)) -> list[dict]:
    factor = storage.get_custom_factor(factor_id, user_id=user["id"])
    if factor is None:
        raise HTTPException(status_code=404, detail="custom factor not found")
    candles = storage.get_candles(
        symbol=payload.symbol,
        period=payload.period,
        adjust_type=payload.adjust_type,
        limit=max(1, min(payload.limit, 1000)),
        start_ts=payload.start,
        end_ts=payload.end,
    )
    params = _merged_factor_params(factor, payload.params)
    logger.info(
        "custom factor preview start id=%s code=%s name=%s symbol=%s period=%s adjust=%s candles=%s params_keys=%s",
        factor_id,
        factor["code"],
        factor["name"],
        payload.symbol,
        payload.period,
        payload.adjust_type,
        len(candles),
        sorted(params.keys()),
    )
    try:
        result = run_custom_factor(factor["source_code"], candles, params)
        logger.info("custom factor preview success id=%s points=%s", factor_id, len(result))
        return result
    except Exception as exc:
        logger.exception("custom factor preview failed id=%s code=%s name=%s", factor_id, factor["code"], factor["name"])
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sync")
def create_sync_task(payload: SyncCreate, background_tasks: BackgroundTasks, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    request = payload.to_request()
    runner = TaskRunner(storage, user_id=user["id"])
    task_id, created = runner.enqueue(request)
    if created:
        background_tasks.add_task(runner.run_task, task_id, request)
    task = storage.get_task(task_id)
    return {"task_id": task_id, "status": task["status"] if task else "queued", "created": created}


@app.post("/api/sync/batch")
def create_batch_sync_task(payload: BatchSyncCreate, background_tasks: BackgroundTasks, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    runner = TaskRunner(storage, user_id=user["id"])
    tasks = []
    for request in payload.requests():
        task_id, created = runner.enqueue(request)
        if created:
            background_tasks.add_task(runner.run_task, task_id, request)
        task = storage.get_task(task_id)
        tasks.append({"task_id": task_id, "symbol": request.symbol, "status": task["status"] if task else "queued", "created": created})
    return {"tasks": tasks}


@app.post("/api/pools/{pool_id}/sync")
def sync_pool(pool_id: str, payload: SyncCreate, background_tasks: BackgroundTasks, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
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
    return create_batch_sync_task(batch, background_tasks, user)


@app.post("/api/pools/{pool_id}/sync/all-periods")
def sync_pool_all_periods(pool_id: str, payload: SyncCreate, background_tasks: BackgroundTasks, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    if storage.get_pool(pool_id, user_id=user["id"]) is None:
        raise HTTPException(status_code=404, detail="pool not found")
    symbols = [row["symbol"] for row in storage.list_pool_symbols(pool_id, enabled_only=True)]
    runner = TaskRunner(storage, user_id=user["id"])
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
def list_tasks(limit: int = Query(default=50, ge=1, le=200), user: dict = Depends(current_user)) -> list[dict]:
    return storage.list_tasks(limit=limit, user_id=user["id"])


@app.get("/api/sync/tasks/{task_id}")
def get_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = storage.get_task(task_id, user_id=user["id"])
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.get("/api/sync/status")
def sync_status() -> list[dict]:
    return storage.list_sync_state()


@app.post("/api/realtime/subscriptions")
def create_realtime_subscription(payload: RealtimeSubscription, user: dict = Depends(current_user)) -> dict:
    storage.init_db()
    try:
        payload.user_id = user["id"]
        return realtime_manager.create(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/realtime/subscriptions/{subscription_id}")
def update_realtime_subscription(subscription_id: str, payload: RealtimeSubscription, user: dict = Depends(current_user)) -> dict:
    try:
        payload.user_id = user["id"]
        return realtime_manager.update(subscription_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="realtime subscription not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/realtime/subscriptions/{subscription_id}")
def delete_realtime_subscription(subscription_id: str, user: dict = Depends(current_user)) -> dict:
    try:
        return realtime_manager.delete(subscription_id, user_id=user["id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="realtime subscription not found") from exc


@app.get("/api/realtime/subscriptions/{subscription_id}/status")
def get_realtime_subscription_status(subscription_id: str, user: dict = Depends(current_user)) -> dict:
    try:
        return realtime_manager.status(subscription_id, user_id=user["id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="realtime subscription not found") from exc


@app.get("/api/realtime/subscriptions/{subscription_id}/snapshot")
def get_realtime_subscription_snapshot(subscription_id: str, user: dict = Depends(current_user)) -> dict:
    try:
        return realtime_manager.snapshot(subscription_id, user_id=user["id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="realtime subscription not found") from exc


@app.get("/api/realtime/subscriptions/{subscription_id}/updates")
def get_realtime_subscription_updates(subscription_id: str, since: Optional[int] = None, user: dict = Depends(current_user)) -> dict:
    try:
        return realtime_manager.updates(subscription_id, since, user_id=user["id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="realtime subscription not found") from exc


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
    user: dict = Depends(current_user),
) -> list[dict]:
    factor = storage.get_custom_factor(factor_id, user_id=user["id"])
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
        merged_params = _merged_factor_params(factor, _json_object(params))
        logger.info(
            "custom factor values start id=%s code=%s symbol=%s period=%s adjust=%s candles=%s params_keys=%s",
            factor_id,
            factor["code"],
            symbol,
            period,
            adjust_type,
            len(candles),
            sorted(merged_params.keys()),
        )
        result = run_custom_factor(factor["source_code"], candles, merged_params)
        logger.info("custom factor values success id=%s points=%s", factor_id, len(result))
        return result
    except Exception as exc:
        logger.exception("custom factor values failed id=%s code=%s", factor_id, factor["code"])
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

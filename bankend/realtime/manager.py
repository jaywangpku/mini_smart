from __future__ import annotations

import threading
import time
from typing import Any
from uuid import uuid4

from ..schemas import RealtimeSubscription
from ..storage import Storage
from .longbridge_provider import LongbridgePollingProvider
from .snapshot import RealtimeSnapshotBuilder, empty_snapshot, now_iso


class RealtimeManager:
    def __init__(self, storage: Storage) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._snapshot_builder = RealtimeSnapshotBuilder(storage, LongbridgePollingProvider(storage))

    def create(self, payload: RealtimeSubscription) -> dict:
        subscription_id = f"rt_{uuid4().hex[:12]}"
        item = {
            "id": subscription_id,
            "user_id": payload.user_id,
            "payload": payload,
            "status": "running",
            "created_at": now_iso(),
            "updated_at": None,
            "snapshot": empty_snapshot(payload),
            "last_error": None,
        }
        with self._lock:
            self._items[subscription_id] = item
        threading.Thread(target=self._run_loop, args=(subscription_id,), daemon=True).start()
        self.refresh(subscription_id)
        return self.status(subscription_id)

    def update(self, subscription_id: str, payload: RealtimeSubscription) -> dict:
        with self._lock:
            item = self._require(subscription_id)
            self._ensure_owner(item, payload.user_id)
            item["payload"] = payload
            item["user_id"] = payload.user_id
            item["status"] = "running"
        self.refresh(subscription_id)
        return self.status(subscription_id)

    def delete(self, subscription_id: str, user_id: str | None = None) -> dict:
        with self._lock:
            item = self._require(subscription_id)
            self._ensure_owner(item, user_id)
            item["status"] = "stopped"
        return {"ok": True}

    def status(self, subscription_id: str, user_id: str | None = None) -> dict:
        with self._lock:
            item = self._require(subscription_id)
            self._ensure_owner(item, user_id)
            snapshot = item["snapshot"]
            return {
                "id": subscription_id,
                "status": item["status"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "last_error": item["last_error"],
                "symbol": item["payload"].symbol.upper(),
                "period": item["payload"].period,
                "adjust_type": item["payload"].adjust_type,
                "source": snapshot.get("status", {}).get("source", "-"),
                "candle_count": snapshot.get("status", {}).get("candle_count", 0),
            }

    def snapshot(self, subscription_id: str, user_id: str | None = None) -> dict:
        with self._lock:
            item = self._require(subscription_id)
            self._ensure_owner(item, user_id)
            return item["snapshot"]

    def updates(self, subscription_id: str, since: int | None = None, user_id: str | None = None) -> dict:
        snapshot = self.snapshot(subscription_id, user_id=user_id)
        if since is None:
            return snapshot
        strategy_result = snapshot.get("strategy_result") or {}
        return {
            "type": "updates",
            "status": snapshot.get("status"),
            "candles": [row for row in snapshot.get("candles", []) if int(row["time"]) >= since],
            "factors": [row for row in snapshot.get("factors", []) if int(row["time"]) >= since],
            "strategy_result": {
                **strategy_result,
                "signals": [row for row in strategy_result.get("signals", []) if int(row["time"]) >= since],
            } if strategy_result else None,
        }

    def refresh(self, subscription_id: str) -> dict:
        with self._lock:
            payload = self._require(subscription_id)["payload"]
        try:
            snapshot = self._snapshot_builder.build(payload)
            with self._lock:
                item = self._require(subscription_id)
                item["snapshot"] = snapshot
                item["updated_at"] = snapshot["status"]["updated_at"]
                item["last_error"] = None
                item["status"] = "running"
            return snapshot
        except Exception as exc:
            with self._lock:
                self._require(subscription_id)["last_error"] = str(exc)
            raise

    def _run_loop(self, subscription_id: str) -> None:
        while True:
            with self._lock:
                item = self._items.get(subscription_id)
                if item is None or item["status"] == "stopped":
                    return
                interval = max(1, min(float(item["payload"].poll_interval), 60))
            time.sleep(interval)
            try:
                self.refresh(subscription_id)
            except Exception:
                continue

    def _require(self, subscription_id: str) -> dict[str, Any]:
        item = self._items.get(subscription_id)
        if item is None:
            raise KeyError(subscription_id)
        return item

    def _ensure_owner(self, item: dict[str, Any], user_id: str | None) -> None:
        if user_id is not None and item.get("user_id") != user_id:
            raise KeyError(item["id"])

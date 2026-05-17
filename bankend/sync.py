from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .longbridge_client import LongbridgeClient
from .models import Candle, SyncRequest
from .storage import Storage


MAX_HISTORY_COUNT = 1000


def parse_date_or_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    if len(value) == 10:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def datetime_to_ts(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.astimezone(timezone.utc).timestamp())


class SyncService:
    def __init__(self, storage: Storage, client: LongbridgeClient | None = None):
        self.storage = storage
        self.client = client or LongbridgeClient()

    def run(self, request: SyncRequest) -> int:
        self.storage.add_symbol(request.symbol)
        candles = self._fetch_range(request)
        rows = self.storage.upsert_candles(candles)
        latest = max((c.timestamp for c in candles), default=None)
        self.storage.update_sync_state(request.symbol, request.period, request.adjust_type, latest)
        return rows

    def _fetch_range(self, request: SyncRequest) -> list[Candle]:
        start = request.start
        end = request.end or datetime.now(timezone.utc)
        if start is None:
            latest_ts = self.storage.latest_timestamp(request.symbol, request.period, request.adjust_type)
            if latest_ts is not None:
                start = datetime.fromtimestamp(latest_ts + 1, tz=timezone.utc)

        if start is None:
            return self.client.fetch_recent(
                request.symbol,
                request.period,
                request.adjust_type,
                count=MAX_HISTORY_COUNT,
                trade_session=request.trade_session,
            )

        cursor = start
        all_candles: list[Candle] = []
        seen: set[int] = set()

        while cursor <= end:
            batch = self.client.fetch_history_by_offset(
                request.symbol,
                request.period,
                request.adjust_type,
                forward=True,
                count=MAX_HISTORY_COUNT,
                time=cursor,
                trade_session=request.trade_session,
            )
            batch = [c for c in batch if c.timestamp <= datetime_to_ts(end)]
            fresh = [c for c in batch if c.timestamp not in seen]
            all_candles.extend(fresh)
            seen.update(c.timestamp for c in fresh)

            if not batch or len(batch) < MAX_HISTORY_COUNT:
                break
            next_ts = max(c.timestamp for c in batch) + 60
            next_cursor = datetime.fromtimestamp(next_ts, tz=timezone.utc)
            if next_cursor <= cursor:
                next_cursor = cursor + timedelta(minutes=1)
            cursor = next_cursor

        return sorted(all_candles, key=lambda candle: candle.timestamp)


class TaskRunner:
    def __init__(self, storage: Storage):
        self.storage = storage

    def enqueue(self, request: SyncRequest) -> tuple[str, bool]:
        active = self.storage.get_active_task(request.symbol, request.period, request.adjust_type)
        if active is not None:
            return active["id"], False

        task_id = f"sync_{uuid4().hex[:12]}"
        try:
            self.storage.create_task(
                task_id,
                request.symbol,
                request.period,
                request.adjust_type,
                datetime_to_ts(request.start),
                datetime_to_ts(request.end),
            )
        except sqlite3.IntegrityError:
            active = self.storage.get_active_task(request.symbol, request.period, request.adjust_type)
            if active is not None:
                return active["id"], False
            raise
        return task_id, True

    def run_task(self, task_id: str, request: SyncRequest) -> None:
        self.storage.update_task(task_id, "running")
        try:
            rows = SyncService(self.storage).run(request)
        except Exception as exc:
            message = str(exc)
            self.storage.update_task(task_id, "failed", error=message)
            self.storage.update_sync_state(request.symbol, request.period, request.adjust_type, None, error=message)
            return
        self.storage.update_task(task_id, "success", rows_written=rows)

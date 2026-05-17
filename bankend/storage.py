from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .config import ensure_data_dir
from .factors.common import trading_day
from .models import Candle


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        ensure_data_dir(db_path)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                  symbol TEXT PRIMARY KEY,
                  name TEXT,
                  market TEXT,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candles (
                  symbol TEXT NOT NULL,
                  period TEXT NOT NULL,
                  adjust_type TEXT NOT NULL,
                  timestamp INTEGER NOT NULL,
                  open REAL NOT NULL,
                  high REAL NOT NULL,
                  low REAL NOT NULL,
                  close REAL NOT NULL,
                  volume INTEGER,
                  turnover REAL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (symbol, period, adjust_type, timestamp)
                );

                CREATE INDEX IF NOT EXISTS idx_candles_lookup
                  ON candles(symbol, period, adjust_type, timestamp DESC);

                CREATE TABLE IF NOT EXISTS sync_state (
                  symbol TEXT NOT NULL,
                  period TEXT NOT NULL,
                  adjust_type TEXT NOT NULL,
                  last_synced_timestamp INTEGER,
                  last_success_at TEXT,
                  last_error TEXT,
                  PRIMARY KEY (symbol, period, adjust_type)
                );

                CREATE TABLE IF NOT EXISTS sync_tasks (
                  id TEXT PRIMARY KEY,
                  symbol TEXT NOT NULL,
                  period TEXT NOT NULL,
                  adjust_type TEXT NOT NULL,
                  start_time INTEGER,
                  end_time INTEGER,
                  status TEXT NOT NULL,
                  rows_written INTEGER NOT NULL DEFAULT 0,
                  error TEXT,
                  created_at TEXT NOT NULL,
                  started_at TEXT,
                  finished_at TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_tasks_active_unique
                  ON sync_tasks(symbol, period, adjust_type)
                  WHERE status IN ('queued', 'running');

                CREATE TABLE IF NOT EXISTS stock_pools (
                  id TEXT PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stock_pool_members (
                  pool_id TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  note TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (pool_id, symbol),
                  FOREIGN KEY(pool_id) REFERENCES stock_pools(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS custom_factors (
                  id TEXT PRIMARY KEY,
                  code TEXT NOT NULL UNIQUE,
                  name TEXT NOT NULL,
                  description TEXT,
                  source_code TEXT NOT NULL,
                  default_params TEXT NOT NULL DEFAULT '{}',
                  enabled INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                """
            )
            now = utc_now_iso()
            conn.execute(
                """
                INSERT INTO stock_pools(id, name, description, created_at, updated_at)
                VALUES ('default', '默认股票池', '系统默认股票池', ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (now, now),
            )

    def add_symbol(self, symbol: str, name: str | None = None, market: str | None = None) -> dict:
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO symbols(symbol, name, market, enabled, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                  name = COALESCE(excluded.name, symbols.name),
                  market = COALESCE(excluded.market, symbols.market),
                  enabled = 1,
                  updated_at = excluded.updated_at
                """,
                (symbol.upper(), name, market, now, now),
            )
        return self.get_symbol(symbol)

    def set_symbol_enabled(self, symbol: str, enabled: bool) -> dict | None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE symbols SET enabled = ?, updated_at = ? WHERE symbol = ?",
                (1 if enabled else 0, utc_now_iso(), symbol.upper()),
            )
        return self.get_symbol(symbol)

    def update_symbol(self, symbol: str, name: str | None = None, market: str | None = None, enabled: bool | None = None) -> dict | None:
        fields: list[str] = []
        params: list[object] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if market is not None:
            fields.append("market = ?")
            params.append(market)
        if enabled is not None:
            fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        if not fields:
            return self.get_symbol(symbol)
        fields.append("updated_at = ?")
        params.append(utc_now_iso())
        params.append(symbol.upper())
        with self.connect() as conn:
            cursor = conn.execute(
                f"UPDATE symbols SET {', '.join(fields)} WHERE symbol = ?",
                params,
            )
        return self.get_symbol(symbol) if cursor.rowcount else None

    def get_symbol(self, symbol: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM symbols WHERE symbol = ?", (symbol.upper(),)).fetchone()
            return dict(row) if row else None

    def list_symbols(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM symbols ORDER BY symbol").fetchall()
            return [dict(row) for row in rows]

    def list_custom_factors(self, enabled_only: bool = False) -> list[dict]:
        clauses: list[str] = []
        if enabled_only:
            clauses.append("enabled = 1")
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM custom_factors
                {'WHERE ' + ' AND '.join(clauses) if clauses else ''}
                ORDER BY updated_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_custom_factor(self, factor_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM custom_factors WHERE id = ?", (factor_id,)).fetchone()
            return dict(row) if row else None

    def create_custom_factor(
        self,
        code: str,
        name: str,
        source_code: str,
        description: str | None = None,
        default_params: str = "{}",
        enabled: bool = True,
    ) -> dict:
        factor_id = f"factor_{uuid4().hex[:12]}"
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO custom_factors(
                  id, code, name, description, source_code, default_params, enabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (factor_id, code, name, description, source_code, default_params, 1 if enabled else 0, now, now),
            )
        factor = self.get_custom_factor(factor_id)
        if factor is None:
            raise ValueError("自定义因子创建失败")
        return factor

    def update_custom_factor(
        self,
        factor_id: str,
        code: str | None = None,
        name: str | None = None,
        source_code: str | None = None,
        description: str | None = None,
        default_params: str | None = None,
        enabled: bool | None = None,
    ) -> dict | None:
        fields: list[str] = []
        params: list[object] = []
        for column, value in (
            ("code", code),
            ("name", name),
            ("source_code", source_code),
            ("description", description),
            ("default_params", default_params),
        ):
            if value is not None:
                fields.append(f"{column} = ?")
                params.append(value)
        if enabled is not None:
            fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        if not fields:
            return self.get_custom_factor(factor_id)
        fields.append("updated_at = ?")
        params.append(utc_now_iso())
        params.append(factor_id)
        with self.connect() as conn:
            cursor = conn.execute(f"UPDATE custom_factors SET {', '.join(fields)} WHERE id = ?", params)
        return self.get_custom_factor(factor_id) if cursor.rowcount else None

    def delete_custom_factor(self, factor_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM custom_factors WHERE id = ?", (factor_id,))
            return cursor.rowcount > 0

    def list_pools(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.*, COUNT(m.symbol) AS symbol_count
                FROM stock_pools p
                LEFT JOIN stock_pool_members m ON m.pool_id = p.id
                GROUP BY p.id
                ORDER BY p.created_at
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def create_pool(self, name: str, description: str | None = None) -> dict:
        pool_id = f"pool_{uuid4().hex[:12]}"
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_pools(id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pool_id, name, description, now, now),
            )
        return self.get_pool(pool_id)

    def get_pool(self, pool_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM stock_pools WHERE id = ?", (pool_id,)).fetchone()
            return dict(row) if row else None

    def update_pool(self, pool_id: str, name: str | None = None, description: str | None = None) -> dict | None:
        current = self.get_pool(pool_id)
        if current is None:
            return None
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE stock_pools
                SET name = COALESCE(?, name),
                    description = COALESCE(?, description),
                    updated_at = ?
                WHERE id = ?
                """,
                (name, description, utc_now_iso(), pool_id),
            )
        return self.get_pool(pool_id)

    def delete_pool(self, pool_id: str) -> bool:
        if pool_id == "default":
            return False
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM stock_pools WHERE id = ?", (pool_id,))
            return cursor.rowcount > 0

    def add_pool_symbol(self, pool_id: str, symbol: str, note: str | None = None, name: str | None = None) -> dict:
        self.add_symbol(symbol, name=name)
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_pool_members(pool_id, symbol, enabled, note, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?)
                ON CONFLICT(pool_id, symbol) DO UPDATE SET
                  enabled = 1,
                  note = COALESCE(excluded.note, stock_pool_members.note),
                  updated_at = excluded.updated_at
                """,
                (pool_id, symbol.upper(), note, now, now),
            )
        member = self.get_pool_symbol(pool_id, symbol)
        if member is None:
            raise ValueError("股票池不存在")
        return member

    def get_pool_symbol(self, pool_id: str, symbol: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT m.*, s.name, s.market
                FROM stock_pool_members m
                LEFT JOIN symbols s ON s.symbol = m.symbol
                WHERE m.pool_id = ? AND m.symbol = ?
                """,
                (pool_id, symbol.upper()),
            ).fetchone()
            return dict(row) if row else None

    def list_pool_symbols(self, pool_id: str, enabled_only: bool = False) -> list[dict]:
        clauses = ["m.pool_id = ?"]
        params: list[object] = [pool_id]
        if enabled_only:
            clauses.append("m.enabled = 1")
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT m.*, s.name, s.market
                FROM stock_pool_members m
                LEFT JOIN symbols s ON s.symbol = m.symbol
                WHERE {' AND '.join(clauses)}
                ORDER BY m.symbol
                """,
                params,
            ).fetchall()
            return [dict(row) for row in rows]

    def set_pool_symbol_enabled(self, pool_id: str, symbol: str, enabled: bool) -> dict | None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE stock_pool_members
                SET enabled = ?, updated_at = ?
                WHERE pool_id = ? AND symbol = ?
                """,
                (1 if enabled else 0, utc_now_iso(), pool_id, symbol.upper()),
            )
        return self.get_pool_symbol(pool_id, symbol)

    def remove_pool_symbol(self, pool_id: str, symbol: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM stock_pool_members WHERE pool_id = ? AND symbol = ?",
                (pool_id, symbol.upper()),
            )
            return cursor.rowcount > 0

    def create_task(
        self,
        task_id: str,
        symbol: str,
        period: str,
        adjust_type: str,
        start_ts: int | None,
        end_ts: int | None,
    ) -> dict:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_tasks(
                  id, symbol, period, adjust_type, start_time, end_time, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'queued', ?)
                """,
                (task_id, symbol.upper(), period, adjust_type, start_ts, end_ts, utc_now_iso()),
            )
        return self.get_task(task_id)

    def get_active_task(self, symbol: str, period: str, adjust_type: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sync_tasks
                WHERE symbol = ? AND period = ? AND adjust_type = ?
                  AND status IN ('queued', 'running')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (symbol.upper(), period, adjust_type),
            ).fetchone()
            return dict(row) if row else None

    def update_task(
        self,
        task_id: str,
        status: str,
        rows_written: int | None = None,
        error: str | None = None,
    ) -> None:
        now = utc_now_iso()
        fields = ["status = ?"]
        params: list[object] = [status]
        if status == "running":
            fields.append("started_at = COALESCE(started_at, ?)")
            params.append(now)
        if status in {"success", "failed"}:
            fields.append("finished_at = ?")
            params.append(now)
        if rows_written is not None:
            fields.append("rows_written = ?")
            params.append(rows_written)
        if error is not None:
            fields.append("error = ?")
            params.append(error)
        params.append(task_id)
        with self.connect() as conn:
            conn.execute(f"UPDATE sync_tasks SET {', '.join(fields)} WHERE id = ?", params)

    def get_task(self, task_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sync_tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list_tasks(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT t.*, s.name
                FROM sync_tasks t
                LEFT JOIN symbols s ON s.symbol = t.symbol
                ORDER BY t.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_candles(self, candles: Iterable[Candle]) -> int:
        rows = list(candles)
        if not rows:
            return 0
        now = utc_now_iso()
        with self.connect() as conn:
            before = conn.total_changes
            conn.executemany(
                """
                INSERT INTO candles(
                  symbol, period, adjust_type, timestamp, open, high, low, close,
                  volume, turnover, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, period, adjust_type, timestamp) DO UPDATE SET
                  open = excluded.open,
                  high = excluded.high,
                  low = excluded.low,
                  close = excluded.close,
                  volume = excluded.volume,
                  turnover = excluded.turnover,
                  updated_at = excluded.updated_at
                """,
                [
                    (
                        c.symbol.upper(),
                        c.period,
                        c.adjust_type,
                        c.timestamp,
                        c.open,
                        c.high,
                        c.low,
                        c.close,
                        c.volume,
                        c.turnover,
                        now,
                        now,
                    )
                    for c in rows
                ],
            )
            return conn.total_changes - before

    def update_sync_state(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        last_ts: int | None,
        error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_state(
                  symbol, period, adjust_type, last_synced_timestamp, last_success_at, last_error
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, period, adjust_type) DO UPDATE SET
                  last_synced_timestamp = COALESCE(excluded.last_synced_timestamp, sync_state.last_synced_timestamp),
                  last_success_at = excluded.last_success_at,
                  last_error = excluded.last_error
                """,
                (symbol.upper(), period, adjust_type, last_ts, utc_now_iso() if error is None else None, error),
            )

    def latest_timestamp(self, symbol: str, period: str, adjust_type: str) -> int | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT MAX(timestamp) AS ts FROM candles
                WHERE symbol = ? AND period = ? AND adjust_type = ?
                """,
                (symbol.upper(), period, adjust_type),
            ).fetchone()
            return row["ts"] if row and row["ts"] is not None else None

    def list_sync_state(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sync_state ORDER BY symbol, period, adjust_type"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_candles(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        limit: int = 1000,
        start_ts: int | None = None,
        end_ts: int | None = None,
    ) -> list[dict]:
        clauses = ["symbol = ?", "period = ?", "adjust_type = ?"]
        params: list[object] = [symbol.upper(), period, adjust_type]
        if start_ts is not None:
            clauses.append("timestamp >= ?")
            params.append(start_ts)
        if end_ts is not None:
            clauses.append("timestamp <= ?")
            params.append(end_ts)
        params.append(min(limit, 20000))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT timestamp AS time, open, high, low, close, volume, turnover
                FROM candles
                WHERE {' AND '.join(clauses)}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [dict(row) for row in reversed(rows)]

    def get_latest_session_candles(
        self,
        symbol: str,
        period: str,
        adjust_type: str,
        limit: int = 20000,
    ) -> list[dict]:
        candles = self.get_candles(symbol, period, adjust_type, limit=limit)
        if not candles:
            return []
        latest_day = trading_day(candles[-1]["time"], symbol)
        return [row for row in candles if trading_day(row["time"], symbol) == latest_day]

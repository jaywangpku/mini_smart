from __future__ import annotations

from typing import Optional

import typer

from .config import load_settings
from .models import SyncRequest
from .storage import Storage
from .sync import SyncService, parse_date_or_datetime


app = typer.Typer(help="mini_smart Longbridge data research tool")


def _storage() -> Storage:
    return Storage(load_settings().db_path)


@app.command("init-db")
def init_db() -> None:
    storage = _storage()
    storage.init_db()
    typer.echo(f"SQLite initialized: {storage.db_path}")


@app.command("api")
def api(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("bankend.api:app", host=host, port=port, reload=True)


@app.command("add-symbol")
def add_symbol(symbol: str) -> None:
    storage = _storage()
    storage.init_db()
    row = storage.add_symbol(symbol)
    typer.echo(row)


@app.command("sync")
def sync(
    symbol: str,
    period: str = "1min",
    start: Optional[str] = None,
    end: Optional[str] = None,
    adjust_type: str = "no_adjust",
) -> None:
    storage = _storage()
    storage.init_db()
    rows = SyncService(storage).run(
        SyncRequest(
            symbol=symbol,
            period=period,
            adjust_type=adjust_type,
            start=parse_date_or_datetime(start),
            end=parse_date_or_datetime(end),
        )
    )
    typer.echo(f"rows_written={rows}")


@app.command("latest")
def latest(symbol: str, period: str = "1min", adjust_type: str = "no_adjust", limit: int = 10) -> None:
    storage = _storage()
    storage.init_db()
    for row in storage.get_candles(symbol, period, adjust_type, limit):
        typer.echo(row)

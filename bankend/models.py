from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


PeriodName = Literal[
    "1min",
    "2min",
    "3min",
    "5min",
    "10min",
    "15min",
    "20min",
    "30min",
    "45min",
    "60min",
    "120min",
    "180min",
    "240min",
    "day",
    "week",
    "month",
]

AdjustTypeName = Literal["no_adjust", "forward"]
TradeSessionName = Literal["intraday"]
TaskStatus = Literal["queued", "running", "success", "failed"]


@dataclass(frozen=True)
class Candle:
    symbol: str
    period: str
    adjust_type: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int | None = None
    turnover: float | None = None


@dataclass(frozen=True)
class SyncRequest:
    symbol: str
    period: str = "1min"
    adjust_type: str = "no_adjust"
    start: datetime | None = None
    end: datetime | None = None
    trade_session: str = "intraday"

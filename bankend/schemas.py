from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .models import SyncRequest
from .sync import parse_date_or_datetime


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
    start: Optional[int] = None
    end: Optional[int] = None


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


class RealtimeSubscription(BaseModel):
    symbol: str
    period: str = "1min"
    adjust_type: str = "forward"
    factor_ids: list[str] = Field(default_factory=list)
    factor_params: dict[str, dict] = Field(default_factory=dict)
    strategy_id: Optional[str] = None
    strategy_params: dict = Field(default_factory=dict)
    backtest: BacktestOptions = BacktestOptions()
    warmup_bars: int = 1000
    poll_interval: float = 5


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

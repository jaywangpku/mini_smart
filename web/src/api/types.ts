export type SymbolRow = {
  symbol: string
  name?: string | null
  market?: string | null
  enabled: number
  created_at: string
  updated_at: string
}

export type PoolRow = {
  id: string
  name: string
  description?: string | null
  symbol_count?: number
  created_at: string
  updated_at: string
}

export type PoolSymbolRow = {
  pool_id: string
  symbol: string
  enabled: number
  note?: string | null
  name?: string | null
  market?: string | null
  created_at: string
  updated_at: string
}

export type SecurityRow = {
  symbol: string
  name?: string | null
  name_en?: string | null
  name_cn?: string | null
  name_hk?: string | null
  market?: string | null
}

export type SecurityInfo = SecurityRow & {
  exchange?: string | null
  currency?: string | null
  lot_size?: number | null
  board?: string | null
  eps?: number | null
  eps_ttm?: number | null
  bps?: number | null
  dividend_yield?: number | null
  total_shares?: number | null
  circulating_shares?: number | null
}

export type SyncPayload = {
  symbol: string
  period: string
  adjust_type: string
  start?: string
  end?: string
}

export type BatchSyncPayload = {
  symbols: string[]
  period: string
  adjust_type: string
  start?: string
  end?: string
}

export type SyncTask = {
  id: string
  symbol: string
  name?: string | null
  period: string
  adjust_type: string
  status: 'queued' | 'running' | 'success' | 'failed'
  rows_written: number
  error?: string | null
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}

export type Candle = {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume?: number | null
  turnover?: number | null
}

export type FactorValuePoint = {
  time: number
  value?: number | null
}

export type CustomFactor = {
  id: string
  code: string
  name: string
  description?: string | null
  source_code: string
  default_params: string
  enabled: number
  created_at: string
  updated_at: string
}

export type CustomStrategy = {
  id: string
  code: string
  name: string
  description?: string | null
  source_code: string
  default_params: string
  enabled: number
  created_at: string
  updated_at: string
}

export type StrategySignal = {
  time: number
  action: 'buy' | 'sell'
  quantity: number
  price?: number | null
  executed_quantity?: number | null
  fee?: number | null
  reason?: string
}

export type StrategyTrade = {
  buy_time: number
  sell_time: number
  quantity: number
  buy_price: number
  sell_price: number
  pnl: number
  return_pct?: number | null
}

export type EquityPoint = {
  time: number
  value: number
  cash: number
  position: number
}

export type StrategyRunResult = {
  signals: StrategySignal[]
  trades: StrategyTrade[]
  equity_curve: EquityPoint[]
  summary: {
    initial_cash: number
    final_value: number
    cash: number
    position: number
    total_return_pct?: number | null
    trade_count: number
    win_rate?: number | null
    max_drawdown_pct?: number | null
  }
}

export type RealtimePayload = {
  symbol: string
  period: string
  adjust_type: string
  factor_ids: string[]
  factor_params: Record<string, Record<string, unknown>>
  strategy_id?: string | null
  strategy_params: Record<string, unknown>
  warmup_bars: number
  poll_interval: number
  backtest: {
    initial_cash: number
    fee_rate: number
    slippage_rate: number
  }
}

export type RealtimeSnapshot = {
  type: 'snapshot' | 'updates'
  status: {
    symbol: string
    period: string
    adjust_type: string
    source: string
    warning?: string | null
    updated_at?: string | null
    candle_count: number
  }
  candles: Candle[]
  factors: Array<{ time: number; [key: string]: number | null | undefined }>
  strategy_result?: StrategyRunResult | null
}

export type RealtimeSubscriptionStatus = {
  id: string
  status: 'running' | 'stopped'
  created_at: string
  updated_at?: string | null
  last_error?: string | null
  symbol: string
  period: string
  adjust_type: string
  source: string
  candle_count: number
}

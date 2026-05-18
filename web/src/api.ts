import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000
})

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

export async function initDb() {
  const { data } = await http.post('/db/init')
  return data
}

export async function createRealtimeSubscription(payload: RealtimePayload) {
  const { data } = await http.post<RealtimeSubscriptionStatus>('/realtime/subscriptions', payload)
  return data
}

export async function updateRealtimeSubscription(subscriptionId: string, payload: RealtimePayload) {
  const { data } = await http.patch<RealtimeSubscriptionStatus>(`/realtime/subscriptions/${subscriptionId}`, payload)
  return data
}

export async function deleteRealtimeSubscription(subscriptionId: string) {
  const { data } = await http.delete<{ ok: boolean }>(`/realtime/subscriptions/${subscriptionId}`)
  return data
}

export async function fetchRealtimeSnapshot(subscriptionId: string) {
  const { data } = await http.get<RealtimeSnapshot>(`/realtime/subscriptions/${subscriptionId}/snapshot`)
  return data
}

export async function fetchRealtimeUpdates(subscriptionId: string, since?: number) {
  const { data } = await http.get<RealtimeSnapshot>(`/realtime/subscriptions/${subscriptionId}/updates`, {
    params: since ? { since } : {}
  })
  return data
}

export async function fetchSymbols() {
  const { data } = await http.get<SymbolRow[]>('/symbols')
  return data
}

export async function addSymbol(symbol: string, name?: string) {
  const { data } = await http.post<SymbolRow>('/symbols', { symbol, name })
  return data
}

export async function setSymbolEnabled(symbol: string, enabled: boolean, name?: string) {
  const { data } = await http.patch<SymbolRow>(`/symbols/${symbol}`, { enabled, name })
  return data
}

export async function searchSecurities(market: string, query: string, limit = 50) {
  const { data } = await http.get<SecurityRow[]>('/securities', {
    params: { market, q: query, limit }
  })
  return data
}

export async function fetchSecurityInfo(symbol: string) {
  const { data } = await http.get<SecurityInfo>(`/securities/${symbol}`)
  return data
}

export async function fetchPools() {
  const { data } = await http.get<PoolRow[]>('/pools')
  return data
}

export async function createPool(name: string, description?: string) {
  const { data } = await http.post<PoolRow>('/pools', { name, description })
  return data
}

export async function updatePool(poolId: string, payload: { name?: string; description?: string }) {
  const { data } = await http.patch<PoolRow>(`/pools/${poolId}`, payload)
  return data
}

export async function deletePool(poolId: string) {
  const { data } = await http.delete<{ ok: boolean }>(`/pools/${poolId}`)
  return data
}

export async function fetchPoolSymbols(poolId: string, enabledOnly = false) {
  const { data } = await http.get<PoolSymbolRow[]>(`/pools/${poolId}/symbols`, {
    params: { enabled_only: enabledOnly }
  })
  return data
}

export async function addPoolSymbol(poolId: string, symbol: string, note?: string, name?: string) {
  const { data } = await http.post<PoolSymbolRow>(`/pools/${poolId}/symbols`, { symbol, note, name })
  return data
}

export async function setPoolSymbolEnabled(poolId: string, symbol: string, enabled: boolean) {
  const { data } = await http.patch<PoolSymbolRow>(`/pools/${poolId}/symbols/${symbol}`, { enabled })
  return data
}

export async function updatePoolSymbol(poolId: string, symbol: string, payload: { name?: string; market?: string }) {
  const { data } = await http.patch<PoolSymbolRow>(`/pools/${poolId}/symbols/${symbol}`, payload)
  return data
}

export async function removePoolSymbol(poolId: string, symbol: string) {
  const { data } = await http.delete<{ ok: boolean }>(`/pools/${poolId}/symbols/${symbol}`)
  return data
}

export async function fetchCustomFactors(enabledOnly = false) {
  const { data } = await http.get<CustomFactor[]>('/factors/custom', {
    params: { enabled_only: enabledOnly }
  })
  return data
}

export async function createCustomFactor(payload: {
  code: string
  name: string
  description?: string
  source_code: string
  default_params: Record<string, unknown>
  enabled: boolean
}) {
  const { data } = await http.post<CustomFactor>('/factors/custom', payload)
  return data
}

export async function updateCustomFactor(
  factorId: string,
  payload: Partial<{
    code: string
    name: string
    description: string
    source_code: string
    default_params: Record<string, unknown>
    enabled: boolean
  }>
) {
  const { data } = await http.patch<CustomFactor>(`/factors/custom/${factorId}`, payload)
  return data
}

export async function deleteCustomFactor(factorId: string) {
  const { data } = await http.delete<{ ok: boolean }>(`/factors/custom/${factorId}`)
  return data
}

export async function previewCustomFactor(
  factorId: string,
  payload: { symbol: string; period: string; adjust_type: string; params: Record<string, unknown>; limit: number; start?: number; end?: number }
) {
  const { data } = await http.post<FactorValuePoint[]>(`/factors/custom/${factorId}/preview`, payload)
  return data
}

export async function fetchCustomStrategies(enabledOnly = false) {
  const { data } = await http.get<CustomStrategy[]>('/strategies/custom', {
    params: { enabled_only: enabledOnly }
  })
  return data
}

export async function createCustomStrategy(payload: {
  code: string
  name: string
  description?: string
  source_code: string
  default_params: Record<string, unknown>
  enabled: boolean
}) {
  const { data } = await http.post<CustomStrategy>('/strategies/custom', payload)
  return data
}

export async function updateCustomStrategy(
  strategyId: string,
  payload: Partial<{
    code: string
    name: string
    description: string
    source_code: string
    default_params: Record<string, unknown>
    enabled: boolean
  }>
) {
  const { data } = await http.patch<CustomStrategy>(`/strategies/custom/${strategyId}`, payload)
  return data
}

export async function deleteCustomStrategy(strategyId: string) {
  const { data } = await http.delete<{ ok: boolean }>(`/strategies/custom/${strategyId}`)
  return data
}

export async function runCustomStrategy(
  strategyId: string,
  payload: {
    symbol: string
    period: string
    adjust_type: string
    params: Record<string, unknown>
    limit: number
    start?: number
    end?: number
    backtest: { initial_cash: number; fee_rate: number; slippage_rate: number }
  }
) {
  const { data } = await http.post<StrategyRunResult>(`/strategies/custom/${strategyId}/run`, payload)
  return data
}

export async function createSyncTask(payload: SyncPayload) {
  const { data } = await http.post<{ task_id: string; status: string; created: boolean }>('/sync', payload)
  return data
}

export async function createBatchSyncTask(payload: BatchSyncPayload) {
  const { data } = await http.post<{ tasks: Array<{ task_id: string; symbol: string; status: string; created: boolean }> }>(
    '/sync/batch',
    payload
  )
  return data
}

export async function syncPool(poolId: string, payload: Omit<SyncPayload, 'symbol'>) {
  const { data } = await http.post<{ tasks: Array<{ task_id: string; symbol: string; status: string; created: boolean }> }>(
    `/pools/${poolId}/sync`,
    { symbol: '*', ...payload }
  )
  return data
}

export async function syncPoolAllPeriods(poolId: string, payload: Omit<SyncPayload, 'symbol' | 'period'>) {
  const { data } = await http.post<{
    tasks: Array<{ task_id: string; symbol: string; period: string; status: string; created: boolean }>
  }>(`/pools/${poolId}/sync/all-periods`, { symbol: '*', period: '*', ...payload })
  return data
}

export async function fetchTasks(limit = 20) {
  const { data } = await http.get<SyncTask[]>('/sync/tasks', { params: { limit } })
  return data
}

export async function fetchCandles(
  symbol: string,
  period: string,
  adjustType: string,
  limit = 1000,
  range?: { start?: number; end?: number }
) {
  const { data } = await http.get<Candle[]>('/candles', {
    params: { symbol, period, adjust_type: adjustType, limit, ...range }
  })
  return data
}

export async function fetchLatestSessionCandles(symbol: string, period: string, adjustType: string, limit = 20000) {
  const { data } = await http.get<Candle[]>('/candles', {
    params: { symbol, period, adjust_type: adjustType, limit, latest_session: true }
  })
  return data
}

export async function fetchCustomFactorValues(
  factorId: string,
  symbol: string,
  period: string,
  adjustType: string,
  params: Record<string, unknown>,
  limit = 2000,
  range?: { start?: number; end?: number }
) {
  const { data } = await http.get<FactorValuePoint[]>(`/factors/custom/${factorId}/values`, {
    params: { symbol, period, adjust_type: adjustType, params: JSON.stringify(params), limit, ...range }
  })
  return data
}

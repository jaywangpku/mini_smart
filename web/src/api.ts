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

export type DerivativeFactorPoint = {
  time: number
  first_derivative?: number | null
  second_derivative?: number | null
}

export async function initDb() {
  const { data } = await http.post('/db/init')
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

export async function fetchDerivativeFactors(
  symbol: string,
  period: string,
  adjustType: string,
  n: number,
  m: number,
  limit = 2000,
  range?: { start?: number; end?: number }
) {
  const { data } = await http.get<DerivativeFactorPoint[]>('/factors/derivative', {
    params: { symbol, period, adjust_type: adjustType, n, m, limit, ...range }
  })
  return data
}

export async function fetchLatestSessionDerivativeFactors(
  symbol: string,
  period: string,
  adjustType: string,
  n: number,
  m: number,
  limit = 20000
) {
  const { data } = await http.get<DerivativeFactorPoint[]>('/factors/derivative', {
    params: { symbol, period, adjust_type: adjustType, n, m, limit, latest_session: true }
  })
  return data
}

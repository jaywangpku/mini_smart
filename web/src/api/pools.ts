import { http } from './http'
import type { PoolRow, PoolSymbolRow } from './types'

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

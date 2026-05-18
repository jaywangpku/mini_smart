import { http } from './http'
import type { SecurityInfo, SecurityRow, SymbolRow } from './types'

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

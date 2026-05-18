import { http } from './http'
import type { Candle } from './types'

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

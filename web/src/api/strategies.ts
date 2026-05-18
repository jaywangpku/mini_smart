import { http } from './http'
import type { CustomStrategy, StrategyRunResult } from './types'

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

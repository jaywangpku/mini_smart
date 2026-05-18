import { http } from './http'
import type { CustomFactor, FactorValuePoint } from './types'

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

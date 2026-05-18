import { http } from './http'
import type { BatchSyncPayload, SyncPayload, SyncTask } from './types'

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

import { http } from './http'
import type { RealtimePayload, RealtimeSnapshot, RealtimeSubscriptionStatus } from './types'

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

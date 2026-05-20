import { AUTH_TOKEN_KEY, http } from './http'

export type AuthUser = {
  id: string
  username: string
  role: string
  created_at: string
  updated_at: string
}

export async function login(username: string, password: string) {
  const { data } = await http.post<{ token: string; user: AuthUser }>('/auth/login', { username, password })
  localStorage.setItem(AUTH_TOKEN_KEY, data.token)
  return data
}

export async function register(username: string, password: string) {
  const { data } = await http.post<{ token: string; user: AuthUser }>('/auth/register', { username, password })
  localStorage.setItem(AUTH_TOKEN_KEY, data.token)
  return data
}

export async function fetchMe() {
  const { data } = await http.get<AuthUser>('/auth/me')
  return data
}

export async function fetchLongbridgeKey() {
  const { data } = await http.get('/me/api-keys/longbridge')
  return data
}

export async function saveLongbridgeKey(payload: { app_key: string; app_secret: string; access_token: string; http_url?: string }) {
  const { data } = await http.put('/me/api-keys/longbridge', payload)
  return data
}

export async function deleteLongbridgeKey() {
  const { data } = await http.delete('/me/api-keys/longbridge')
  return data
}

export async function changePassword(payload: { old_password: string; new_password: string }) {
  const { data } = await http.post('/auth/change-password', payload)
  return data
}

export async function adminResetPassword(payload: { username: string; new_password: string }) {
  const { data } = await http.post('/auth/admin/reset-password', payload)
  return data
}

export async function fetchAdminUsers() {
  const { data } = await http.get<AuthUser[]>('/auth/admin/users')
  return data
}

export async function deleteAdminUser(userId: string) {
  const { data } = await http.delete(`/auth/admin/users/${userId}`)
  return data
}

export function logout() {
  localStorage.removeItem(AUTH_TOKEN_KEY)
}

export function hasToken() {
  return Boolean(localStorage.getItem(AUTH_TOKEN_KEY))
}

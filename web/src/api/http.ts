import axios from 'axios'

export const http = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export const AUTH_TOKEN_KEY = 'mini_smart_token'

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      window.dispatchEvent(new CustomEvent('mini-smart-auth-expired'))
    }
    return Promise.reject(error)
  }
)

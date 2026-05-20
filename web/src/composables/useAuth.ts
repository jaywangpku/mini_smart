import { ref } from 'vue'
import { fetchMe, hasToken, login, logout, register, type AuthUser } from '../api'

type ErrorHandler = (err: unknown, fallback: string) => void

export function useAuth(options: { setError: ErrorHandler }) {
  const currentUser = ref<AuthUser | null>(null)
  const authReady = ref(false)
  const authMode = ref<'login' | 'register'>('login')
  const authForm = ref({ username: 'admin', password: 'admin' })
  const authLoading = ref(false)

  async function bootstrapAuth() {
    if (!hasToken()) {
      authReady.value = true
      return
    }
    try {
      currentUser.value = await fetchMe()
    } catch {
      logout()
      currentUser.value = null
    } finally {
      authReady.value = true
    }
  }

  async function submitAuth() {
    authLoading.value = true
    try {
      const action = authMode.value === 'register' ? register : login
      const result = await action(authForm.value.username.trim(), authForm.value.password)
      currentUser.value = result.user
      return result.user
    } catch (err) {
      options.setError(err, authMode.value === 'register' ? '注册失败' : '登录失败')
      return null
    } finally {
      authLoading.value = false
    }
  }

  function signOut() {
    logout()
    currentUser.value = null
  }

  window.addEventListener('mini-smart-auth-expired', signOut)

  return {
    currentUser,
    authReady,
    authMode,
    authForm,
    authLoading,
    bootstrapAuth,
    submitAuth,
    signOut
  }
}

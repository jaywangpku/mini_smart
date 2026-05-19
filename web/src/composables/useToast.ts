import { ref } from 'vue'

export function useToast() {
  const message = ref('')
  const error = ref('')
  let toastTimer: number | undefined

  function showToast(text: string, type: 'success' | 'error' = 'success') {
    if (toastTimer) window.clearTimeout(toastTimer)
    if (type === 'success') {
      message.value = text
      error.value = ''
    } else {
      error.value = text
      message.value = ''
    }
    toastTimer = window.setTimeout(() => {
      message.value = ''
      error.value = ''
    }, 2600)
  }

  function setError(err: unknown, fallback: string) {
    showToast(err instanceof Error ? err.message : fallback, 'error')
  }

  function clearToastTimer() {
    if (toastTimer) window.clearTimeout(toastTimer)
  }

  return {
    message,
    error,
    showToast,
    setError,
    clearToastTimer
  }
}

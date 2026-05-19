import { computed, ref, type ComputedRef, type Ref } from 'vue'
import {
  createBatchSyncTask,
  fetchTasks,
  syncPool,
  syncPoolAllPeriods,
  type PoolSymbolRow,
  type SyncTask
} from '../api'
import { localDateString } from '../utils'

type ToastType = (text: string, type?: 'success' | 'error') => void
type ErrorHandler = (err: unknown, fallback: string) => void

export function useSyncTasks(options: {
  enabledPoolSymbols: ComputedRef<PoolSymbolRow[]>
  selectedPoolId: Ref<string>
  selectedSymbols: Ref<string[]>
  period: Ref<string>
  adjustType: Ref<string>
  loading: Ref<boolean>
  showToast: ToastType
  setError: ErrorHandler
}) {
  const tasks = ref<SyncTask[]>([])
  const syncMode = ref<'incremental' | 'range'>('incremental')
  const start = ref('2025-01-01')
  const end = ref(localDateString())
  const hasRunningTask = computed(() => tasks.value.some((task) => task.status === 'queued' || task.status === 'running'))

  async function loadTasks() {
    tasks.value = await fetchTasks(20)
  }

  function toggleSelectedSymbol(symbol: string) {
    options.selectedSymbols.value = options.selectedSymbols.value.includes(symbol)
      ? options.selectedSymbols.value.filter((item) => item !== symbol)
      : [...options.selectedSymbols.value, symbol]
  }

  function selectAllEnabled() {
    options.selectedSymbols.value = options.enabledPoolSymbols.value.map((row) => row.symbol)
  }

  function taskSymbolLabel(task: SyncTask) {
    return task.name?.trim() || task.symbol
  }

  async function submitSelectedSync() {
    if (!options.selectedSymbols.value.length) return
    options.loading.value = true
    try {
      const response = await createBatchSyncTask({
        symbols: options.selectedSymbols.value,
        period: options.period.value,
        adjust_type: options.adjustType.value,
        start: syncMode.value === 'range' ? start.value || undefined : undefined,
        end: end.value || undefined
      })
      options.showToast(`已提交 ${response.tasks.length} 个同步任务`)
      await loadTasks()
    } catch (err) {
      options.setError(err, '批量同步失败')
    } finally {
      options.loading.value = false
    }
  }

  async function submitPoolSync() {
    options.loading.value = true
    try {
      const payload = {
        adjust_type: options.adjustType.value,
        start: syncMode.value === 'range' ? start.value || undefined : undefined,
        end: end.value || undefined
      }
      const response = options.period.value === 'all'
        ? await syncPoolAllPeriods(options.selectedPoolId.value, payload)
        : await syncPool(options.selectedPoolId.value, { period: options.period.value, ...payload })
      options.showToast(`股票池同步已提交：${response.tasks.length} 个任务`)
      await loadTasks()
    } catch (err) {
      options.setError(err, '股票池同步失败')
    } finally {
      options.loading.value = false
    }
  }

  return {
    tasks,
    selectedSymbols: options.selectedSymbols,
    syncMode,
    start,
    end,
    hasRunningTask,
    loadTasks,
    toggleSelectedSymbol,
    selectAllEnabled,
    taskSymbolLabel,
    submitSelectedSync,
    submitPoolSync
  }
}

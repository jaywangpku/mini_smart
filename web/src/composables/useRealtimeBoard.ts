import { ref, watch, type Ref } from 'vue'
import {
  createRealtimeSubscription,
  deleteRealtimeSubscription,
  fetchRealtimeSnapshot,
  fetchRealtimeUpdates,
  updateRealtimeSubscription,
  type Candle,
  type RealtimePayload,
  type RealtimeSnapshot,
  type StrategyRunResult
} from '../api'
import { mergeByTime, parseJsonObject } from '../appHelpers'

type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }
type ErrorHandler = (err: unknown, fallback: string) => void

export function useRealtimeBoard(options: {
  researchSymbol: Ref<string>
  period: Ref<string>
  adjustType: Ref<string>
  customFactorParamText: Ref<Record<string, string>>
  realtimeStrategyId: Ref<string>
  realtimeStrategyParams: Ref<string>
  strategyInitialCash: Ref<number>
  strategyFeeRate: Ref<number>
  strategySlippageRate: Ref<number>
  setError: ErrorHandler
}) {
  const showRealtimeIndicatorDialog = ref(false)
  const realtimeSelectedFactors = ref<string[]>([])
  const realtimeCandles = ref<Candle[]>([])
  const realtimeFactors = ref<ChartFactorPoint[]>([])
  const realtimeStrategyResult = ref<StrategyRunResult | null>(null)
  const realtimeFitKey = ref(0)
  const realtimeWarmupBars = ref(1000)
  const realtimePollInterval = ref(5)
  const realtimeStatus = ref('未连接')
  const realtimeSource = ref('-')
  const realtimeUpdatedAt = ref('')
  const realtimeWarning = ref('')
  const realtimeConnected = ref(false)
  const realtimeSubscriptionId = ref('')
  const realtimeSince = ref<number | undefined>()
  const showRealtimeEquity = ref(false)
  let realtimeTimer: number | undefined

  function openRealtimeIndicatorDialog() {
    showRealtimeIndicatorDialog.value = true
  }

  function closeRealtimeIndicatorDialog() {
    showRealtimeIndicatorDialog.value = false
  }

  function realtimePayload(): RealtimePayload {
    const factorParams: Record<string, Record<string, unknown>> = {}
    for (const key of realtimeSelectedFactors.value) {
      factorParams[key] = parseJsonObject(options.customFactorParamText.value[key] || '{}')
    }
    return {
      symbol: options.researchSymbol.value,
      period: options.period.value,
      adjust_type: options.adjustType.value,
      factor_ids: realtimeSelectedFactors.value,
      factor_params: factorParams,
      strategy_id: options.realtimeStrategyId.value || null,
      strategy_params: options.realtimeStrategyId.value ? parseJsonObject(options.realtimeStrategyParams.value) : {},
      warmup_bars: realtimeWarmupBars.value,
      poll_interval: realtimePollInterval.value,
      backtest: {
        initial_cash: options.strategyInitialCash.value,
        fee_rate: options.strategyFeeRate.value,
        slippage_rate: options.strategySlippageRate.value
      }
    }
  }

  function applyRealtimeSnapshot(payload: RealtimeSnapshot) {
    realtimeCandles.value = mergeByTime(realtimeCandles.value, payload.candles || [])
    realtimeFactors.value = mergeByTime(realtimeFactors.value, payload.factors || [])
    if (payload.strategy_result) {
      if (payload.type === 'updates' && realtimeStrategyResult.value) {
        realtimeStrategyResult.value = {
          ...payload.strategy_result,
          signals: mergeStrategySignals(realtimeStrategyResult.value.signals, payload.strategy_result.signals || [])
        }
      } else {
        realtimeStrategyResult.value = payload.strategy_result
      }
    }
    realtimeSource.value = payload.status?.source || realtimeSource.value || '-'
    realtimeUpdatedAt.value = payload.status?.updated_at || realtimeUpdatedAt.value
    realtimeWarning.value = payload.status?.warning || ''
    realtimeSince.value = realtimeCandles.value.at(-1)?.time
  }

  function mergeStrategySignals(current: StrategyRunResult['signals'], incoming: StrategyRunResult['signals']) {
    const byKey = new Map<string, StrategyRunResult['signals'][number]>()
    for (const signal of current) byKey.set(`${signal.time}:${signal.action}:${signal.quantity}`, signal)
    for (const signal of incoming) byKey.set(`${signal.time}:${signal.action}:${signal.quantity}`, signal)
    return [...byKey.values()].sort((a, b) => a.time - b.time)
  }

  async function pullRealtimeUpdates() {
    if (!realtimeSubscriptionId.value) return
    try {
      const payload = await fetchRealtimeUpdates(realtimeSubscriptionId.value, realtimeSince.value)
      applyRealtimeSnapshot(payload)
    } catch (err) {
      options.setError(err, '拉取实时增量失败')
    }
  }

  function scheduleRealtimePolling() {
    if (realtimeTimer) window.clearInterval(realtimeTimer)
    const interval = Math.max(1, Math.min(realtimePollInterval.value || 5, 60)) * 1000
    realtimeTimer = window.setInterval(pullRealtimeUpdates, interval)
  }

  async function startRealtime() {
    if (!options.researchSymbol.value) {
      options.setError(new Error('请先选择股票'), '请先选择股票')
      return
    }
    realtimeStatus.value = '连接中'
    realtimeWarning.value = ''
    realtimeCandles.value = []
    realtimeFactors.value = []
    realtimeStrategyResult.value = null
    realtimeSince.value = undefined
    try {
      if (realtimeSubscriptionId.value) await deleteRealtimeSubscription(realtimeSubscriptionId.value)
      const status = await createRealtimeSubscription(realtimePayload())
      realtimeSubscriptionId.value = status.id
      const snapshot = await fetchRealtimeSnapshot(status.id)
      applyRealtimeSnapshot(snapshot)
      realtimeConnected.value = true
      realtimeStatus.value = '运行中'
      realtimeFitKey.value += 1
      scheduleRealtimePolling()
    } catch (err) {
      options.setError(err, '启动实时看板失败')
    }
  }

  async function stopRealtime(clearStatus = true) {
    if (realtimeTimer) {
      window.clearInterval(realtimeTimer)
      realtimeTimer = undefined
    }
    if (realtimeSubscriptionId.value) {
      try {
        await deleteRealtimeSubscription(realtimeSubscriptionId.value)
      } catch {
        // 订阅已经不存在时，前端仍然清理本地状态。
      }
      realtimeSubscriptionId.value = ''
    }
    realtimeConnected.value = false
    if (clearStatus) realtimeStatus.value = '已停止'
  }

  async function refreshRealtime() {
    if (realtimeConnected.value) {
      if (realtimeSubscriptionId.value) {
        await updateRealtimeSubscription(realtimeSubscriptionId.value, realtimePayload())
        const snapshot = await fetchRealtimeSnapshot(realtimeSubscriptionId.value)
        realtimeCandles.value = []
        realtimeFactors.value = []
        realtimeStrategyResult.value = null
        realtimeSince.value = undefined
        applyRealtimeSnapshot(snapshot)
        scheduleRealtimePolling()
      }
    } else {
      await startRealtime()
    }
  }

  watch(realtimeSelectedFactors, (value) => {
    if (value.length > 2) realtimeSelectedFactors.value = value.slice(0, 2)
  }, { deep: true })

  return {
    showRealtimeIndicatorDialog,
    realtimeSelectedFactors,
    realtimeCandles,
    realtimeFactors,
    realtimeStrategyResult,
    realtimeFitKey,
    realtimeWarmupBars,
    realtimePollInterval,
    realtimeStatus,
    realtimeSource,
    realtimeUpdatedAt,
    realtimeWarning,
    realtimeConnected,
    realtimeSubscriptionId,
    realtimeSince,
    showRealtimeEquity,
    openRealtimeIndicatorDialog,
    closeRealtimeIndicatorDialog,
    realtimePayload,
    applyRealtimeSnapshot,
    mergeStrategySignals,
    pullRealtimeUpdates,
    scheduleRealtimePolling,
    startRealtime,
    stopRealtime,
    refreshRealtime
  }
}

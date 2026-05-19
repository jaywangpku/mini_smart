<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  createRealtimeSubscription,
  deleteRealtimeSubscription,
  fetchCandles,
  fetchCustomFactorValues,
  fetchPoolSymbols,
  fetchRealtimeSnapshot,
  fetchRealtimeUpdates,
  initDb,
  updateRealtimeSubscription,
  type Candle,
  type StrategyRunResult
} from './api'
import { chartLimitForPeriod, customFactorColor, customFactorIdFromKey, customFactorKey, mergeByTime, parseJsonObject, prettyJson } from './appHelpers'
import { tabs, type TabName } from './navigation'
import { dateRange, formatMoney, formatPct } from './utils'
import { useKlineIndicators } from './composables/useKlineIndicators'
import { useCustomFactors } from './composables/useCustomFactors'
import { useCustomStrategies } from './composables/useCustomStrategies'
import { usePools } from './composables/usePools'
import { useSyncTasks } from './composables/useSyncTasks'
import { useToast } from './composables/useToast'
import SideNav from './components/SideNav.vue'
import ToastMessage from './components/ToastMessage.vue'
import { provideAppViewContext } from './appContext'
import PoolView from './views/PoolView.vue'
import SyncView from './views/SyncView.vue'
import HistoryBoardView from './views/HistoryBoardView.vue'
import RealtimeBoardView from './views/RealtimeBoardView.vue'
import CustomFactorView from './views/CustomFactorView.vue'
import FactorResearchView from './views/FactorResearchView.vue'
import CustomStrategyView from './views/CustomStrategyView.vue'
import StrategyResearchView from './views/StrategyResearchView.vue'
import AppDialogs from './views/AppDialogs.vue'

type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }

const activeTab = ref<TabName>('pools')
const navCollapsed = ref(false)
const candles = ref<Candle[]>([])
const historyCandles = ref<Candle[]>([])
const historyFitKey = ref(0)
const factors = ref<ChartFactorPoint[]>([])
const strategyResearchFactors = ref<ChartFactorPoint[]>([])
const selectedSymbols = ref<string[]>([])
const researchSymbol = ref('')
const period = ref('1min')
const adjustType = ref('forward')
const researchStart = ref('')
const researchEnd = ref('')
const selectedFactors = ref<string[]>([])
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
const strategyInitialCash = ref(100000)
const strategyFeeRate = ref(0.0003)
const strategySlippageRate = ref(0.0002)
const {
  showVwap,
  showMa,
  showEma,
  showBollinger,
  maPeriod,
  emaPeriod,
  bollingerPeriod,
  bollingerMultiplier,
  activeParamDialog,
  openSimpleParamDialog,
  closeSimpleParamDialog,
  simpleParamTitle
} = useKlineIndicators()
const visibleCandleCount = ref(160)
const chartFitKey = ref(0)
const loadingOlder = ref(false)
const reachedHistoryStart = ref(false)
const loadingOlderHistory = ref(false)
const reachedHistoryStartForHistory = ref(false)
const loading = ref(false)
const { message, error, showToast, setError, clearToastTimer } = useToast()
let timer: number | undefined
let realtimeTimer: number | undefined

const {
  customFactors,
  selectedCustomFactorId,
  showNewFactorDialog,
  showEditFactorDialog,
  showParamDialog,
  showResearchParamDialog,
  showRealtimeFactorDialog,
  showResearchFactorDialog,
  editingResearchParamKey,
  newFactorDraft,
  editFactorDraft,
  customFactorForm,
  customFactorPreview,
  customPreviewCandles,
  customPreviewFactors,
  customPreviewFitKey,
  customPreviewSymbol,
  customPreviewPoolId,
  customPreviewPoolSymbols,
  customPreviewPeriod,
  customPreviewAdjustType,
  customPreviewLimit,
  customFactorParamText,
  customFactorDisplayMode,
  enabledCustomFactors,
  selectedCustomFactor,
  previewFactorKey,
  previewFactorSeries,
  selectedCustomFactors,
  factorSeriesMeta,
  loadCustomFactors,
  selectCustomFactor,
  openNewCustomFactorDialog,
  closeNewCustomFactorDialog,
  openEditCustomFactorDialog,
  closeEditCustomFactorDialog,
  openParamDialog,
  closeParamDialog,
  openResearchParamDialog,
  closeResearchParamDialog,
  openRealtimeFactorDialog,
  closeRealtimeFactorDialog,
  openResearchFactorDialog,
  closeResearchFactorDialog,
  resetCustomFactorForm,
  createCustomFactorFromDialog,
  saveCustomFactor,
  saveCustomFactorMeta,
  removeCustomFactor,
  runCustomFactorPreview,
  researchParamLabel,
  factorDisplayModeLabel
} = useCustomFactors({
  selectedFactors,
  showToast,
  setError
})

const {
  customStrategies,
  selectedCustomStrategyId,
  showNewStrategyDialog,
  showEditStrategyDialog,
  showStrategyParamDialog,
  showResearchStrategyParamDialog,
  showRealtimeStrategyParamDialog,
  newStrategyDraft,
  editStrategyDraft,
  customStrategyForm,
  strategyPreviewPoolId,
  strategyPreviewPoolSymbols,
  strategyPreviewSymbol,
  strategyPreviewPeriod,
  strategyPreviewAdjustType,
  strategyPreviewLimit,
  strategyPreviewInitialCash,
  strategyPreviewFeeRate,
  strategyPreviewSlippageRate,
  strategyPreviewCandles,
  strategyPreviewResult,
  strategyPreviewFitKey,
  showStrategyPreviewEquity,
  strategyResearchStrategyId,
  strategyResearchParams,
  strategyResearchCandles,
  strategyResearchResult,
  strategyResearchFitKey,
  showStrategyResearchEquity,
  realtimeStrategyId,
  realtimeStrategyParams,
  strategyResearchStart,
  strategyResearchEnd,
  enabledCustomStrategies,
  selectedCustomStrategy,
  selectedResearchStrategy,
  selectedRealtimeStrategy,
  loadCustomStrategies,
  selectCustomStrategy,
  resetCustomStrategyForm,
  openNewCustomStrategyDialog,
  closeNewCustomStrategyDialog,
  openEditCustomStrategyDialog,
  closeEditCustomStrategyDialog,
  openStrategyParamDialog,
  closeStrategyParamDialog,
  openResearchStrategyParamDialog,
  closeResearchStrategyParamDialog,
  openRealtimeStrategyParamDialog,
  closeRealtimeStrategyParamDialog,
  createCustomStrategyFromDialog,
  saveCustomStrategy,
  saveCustomStrategyMeta,
  removeCustomStrategy,
  strategyRunPayload,
  runCustomStrategyPreview,
  runStrategyResearch: runStrategyResearchBase
} = useCustomStrategies({
  researchSymbol,
  period,
  adjustType,
  strategyInitialCash,
  strategyFeeRate,
  strategySlippageRate,
  showToast,
  setError
})

const {
  pools,
  selectedPoolId,
  poolSymbols,
  showNewPoolDialog,
  showEditPoolDialog,
  newPoolDraft,
  editPoolDraft,
  newSymbol,
  newSymbolName,
  securityMarket,
  securityQuery,
  securityResults,
  selectedSecurity,
  searchingSecurities,
  selectedPool,
  enabledPoolSymbols,
  loadPools,
  loadPoolSymbols,
  openNewPoolDialog,
  closeNewPoolDialog,
  openEditPoolDialog,
  closeEditPoolDialog,
  handleCreatePool,
  handleUpdatePool,
  handleDeletePool,
  handleAddPoolSymbol,
  handleSearchSecurities,
  selectSecurity,
  addSelectedSecurity,
  savePoolSymbolName,
  togglePoolSymbol,
  deletePoolSymbol,
  symbolLabel
} = usePools({
  customPreviewPoolId,
  customPreviewSymbol,
  customPreviewPoolSymbols,
  strategyPreviewPoolId,
  strategyPreviewSymbol,
  strategyPreviewPoolSymbols,
  selectedSymbols,
  researchSymbol,
  showToast,
  setError
})

const {
  tasks,
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
} = useSyncTasks({
  enabledPoolSymbols,
  selectedPoolId,
  selectedSymbols,
  period,
  adjustType,
  loading,
  showToast,
  setError
})

async function loadChart(options: { resetView?: boolean } = {}) {
  if (!researchSymbol.value) {
    candles.value = []
    factors.value = []
    reachedHistoryStart.value = false
    return
  }
  const limit = chartLimitForPeriod(period.value)
  const range = dateRange(researchStart.value, researchEnd.value)
  const nextCandles = await fetchCandles(researchSymbol.value, period.value, adjustType.value, limit, range)
  const nextFactors = await loadFactorValues(limit, range)
  candles.value = nextCandles
  factors.value = nextFactors
  reachedHistoryStart.value = false
  if (options.resetView) chartFitKey.value += 1
}

async function loadHistoryChart(options: { resetView?: boolean } = {}) {
  if (!researchSymbol.value) {
    historyCandles.value = []
    reachedHistoryStartForHistory.value = false
    return
  }
  historyCandles.value = await fetchCandles(
    researchSymbol.value,
    period.value,
    adjustType.value,
    chartLimitForPeriod(period.value),
    dateRange(researchStart.value, researchEnd.value)
  )
  reachedHistoryStartForHistory.value = false
  if (options.resetView) historyFitKey.value += 1
}

async function loadOlderChartData() {
  if (loadingOlder.value || reachedHistoryStart.value || !researchSymbol.value || !candles.value.length) return
  loadingOlder.value = true
  error.value = ''
  try {
    const endTime = candles.value[0].time - 1
    const baseRange = dateRange(researchStart.value, researchEnd.value)
    const range = { ...baseRange, end: Math.min(baseRange.end ?? endTime, endTime) }
    const [olderCandles, olderFactors] = await Promise.all([
      fetchCandles(researchSymbol.value, period.value, adjustType.value, 1200, range),
      loadFactorValues(1200, range)
    ])

    if (!olderCandles.length) {
      reachedHistoryStart.value = true
      return
    }

    candles.value = mergeByTime(candles.value, olderCandles)
    factors.value = mergeByTime(factors.value, olderFactors)
    if (olderCandles.length < 1200) reachedHistoryStart.value = true
  } catch (err) {
    setError(err, '加载历史K线失败')
  } finally {
    loadingOlder.value = false
  }
}

async function loadOlderHistoryChartData() {
  if (loadingOlderHistory.value || reachedHistoryStartForHistory.value || !researchSymbol.value || !historyCandles.value.length) return
  loadingOlderHistory.value = true
  error.value = ''
  try {
    const endTime = historyCandles.value[0].time - 1
    const limit = chartLimitForPeriod(period.value)
    const baseRange = dateRange(researchStart.value, researchEnd.value)
    const range = { ...baseRange, end: Math.min(baseRange.end ?? endTime, endTime) }
    const olderCandles = await fetchCandles(researchSymbol.value, period.value, adjustType.value, limit, range)

    if (!olderCandles.length) {
      reachedHistoryStartForHistory.value = true
      return
    }

    historyCandles.value = mergeByTime(historyCandles.value, olderCandles)
    if (olderCandles.length < limit) reachedHistoryStartForHistory.value = true
  } catch (err) {
    setError(err, '加载历史看板K线失败')
  } finally {
    loadingOlderHistory.value = false
  }
}

async function loadFactorValues(limit: number, range?: { start?: number; end?: number }) {
  const byTime = new Map<number, ChartFactorPoint>()
  const ensurePoint = (time: number) => {
    let point = byTime.get(time)
    if (!point) {
      point = { time }
      byTime.set(time, point)
    }
    return point
  }

  await Promise.all(
    selectedCustomFactors.value.map(async (key) => {
      const id = customFactorIdFromKey(key)
      const rows = await fetchCustomFactorValues(id, researchSymbol.value, period.value, adjustType.value, parseJsonObject(customFactorParamText.value[key] || '{}'), limit, range)
      for (const row of rows) ensurePoint(row.time)[key] = row.value ?? null
    })
  )

  return [...byTime.values()].sort((a, b) => a.time - b.time)
}

async function loadStrategyResearchFactors() {
  if (!strategyResearchCandles.value.length) {
    strategyResearchFactors.value = []
    return
  }
  strategyResearchFactors.value = await loadFactorValues(
    strategyResearchCandles.value.length,
    dateRange(strategyResearchStart.value, strategyResearchEnd.value)
  )
}

async function runStrategyResearch() {
  await runStrategyResearchBase()
  await loadStrategyResearchFactors()
}

async function bootstrap() {
  loading.value = true
  error.value = ''
  try {
    await initDb()
    await loadPools()
    await loadPoolSymbols()
    await Promise.all([loadCustomFactors(), loadCustomStrategies(), loadTasks()])
    await loadChart({ resetView: true })
  } catch (err) {
    setError(err, '初始化失败')
  } finally {
    loading.value = false
  }
}

function openRealtimeIndicatorDialog() {
  showRealtimeIndicatorDialog.value = true
}

function closeRealtimeIndicatorDialog() {
  showRealtimeIndicatorDialog.value = false
}

function compactJson(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw || '{}'))
  } catch {
    return raw || '{}'
  }
}

function realtimePayload() {
  const factorParams: Record<string, Record<string, unknown>> = {}
  for (const key of realtimeSelectedFactors.value) {
    factorParams[key] = parseJsonObject(customFactorParamText.value[key] || '{}')
  }
  return {
    symbol: researchSymbol.value,
    period: period.value,
    adjust_type: adjustType.value,
    factor_ids: realtimeSelectedFactors.value,
    factor_params: factorParams,
    strategy_id: realtimeStrategyId.value || null,
    strategy_params: realtimeStrategyId.value ? parseJsonObject(realtimeStrategyParams.value) : {},
    warmup_bars: realtimeWarmupBars.value,
    poll_interval: realtimePollInterval.value,
    backtest: {
      initial_cash: strategyInitialCash.value,
      fee_rate: strategyFeeRate.value,
      slippage_rate: strategySlippageRate.value
    }
  }
}

function applyRealtimeSnapshot(payload: {
  type?: string
  status?: { source?: string; updated_at?: string | null; warning?: string | null }
  candles?: Candle[]
  factors?: ChartFactorPoint[]
  strategy_result?: StrategyRunResult | null
}) {
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
    setError(err, '拉取实时增量失败')
  }
}

function scheduleRealtimePolling() {
  if (realtimeTimer) window.clearInterval(realtimeTimer)
  const interval = Math.max(1, Math.min(realtimePollInterval.value || 5, 60)) * 1000
  realtimeTimer = window.setInterval(pullRealtimeUpdates, interval)
}

async function startRealtime() {
  if (!researchSymbol.value) {
    setError(new Error('请先选择股票'), '请先选择股票')
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
    setError(err, '启动实时看板失败')
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

watch(customPreviewPoolId, async (poolId) => {
  error.value = ''
  try {
    customPreviewPoolSymbols.value = await fetchPoolSymbols(poolId)
    customPreviewSymbol.value = customPreviewPoolSymbols.value[0]?.symbol || ''
  } catch (err) {
    setError(err, '加载测试股票池失败')
  }
})

watch(realtimeSelectedFactors, (value) => {
  if (value.length > 2) realtimeSelectedFactors.value = value.slice(0, 2)
}, { deep: true })

watch(
  [researchSymbol, period, adjustType, realtimeSelectedFactors, realtimeStrategyId, realtimeWarmupBars, realtimePollInterval],
  () => {
    if (realtimeConnected.value) refreshRealtime()
  },
  { deep: true }
)

watch(selectedPoolId, async () => {
  await loadPoolSymbols()
  if (!enabledPoolSymbols.value.some((row) => row.symbol === researchSymbol.value)) {
    researchSymbol.value = enabledPoolSymbols.value[0]?.symbol || ''
  }
  await loadChart()
})

watch([researchSymbol, period, adjustType, researchStart, researchEnd, selectedFactors, customFactorParamText], () => {
  loadChart().catch((err) => setError(err, '加载图表失败'))
}, { deep: true })

watch([selectedFactors, customFactorParamText], () => {
  if (activeTab.value === 'strategyResearch') {
    loadStrategyResearchFactors().catch((err) => setError(err, '加载策略研究因子失败'))
  }
}, { deep: true })

watch([researchSymbol, period, adjustType, researchStart, researchEnd], () => {
  if (activeTab.value === 'history') loadHistoryChart().catch((err) => setError(err, '加载历史看板失败'))
})

watch(activeTab, (tab) => {
  if (tab === 'history') loadHistoryChart({ resetView: true }).catch((err) => setError(err, '加载历史看板失败'))
})

provideAppViewContext({
  activeTab,
  navCollapsed,
  pools,
  selectedPoolId,
  poolSymbols,
  customFactors,
  customStrategies,
  tasks,
  candles,
  historyCandles,
  historyFitKey,
  strategyResearchFactors,
  factors,
  selectedSymbols,
  researchSymbol,
  researchStart,
  researchEnd,
  showNewPoolDialog,
  showEditPoolDialog,
  newPoolDraft,
  editPoolDraft,
  newSymbol,
  newSymbolName,
  securityMarket,
  securityQuery,
  securityResults,
  selectedSecurity,
  searchingSecurities,
  period,
  adjustType,
  syncMode,
  start,
  end,
  selectedFactors,
  selectedCustomFactorId,
  showNewFactorDialog,
  showEditFactorDialog,
  showParamDialog,
  showResearchParamDialog,
  showRealtimeIndicatorDialog,
  showRealtimeFactorDialog,
  showResearchFactorDialog,
  editingResearchParamKey,
  activeParamDialog,
  newFactorDraft,
  editFactorDraft,
  customFactorForm,
  customFactorPreview,
  customPreviewCandles,
  customPreviewFactors,
  customPreviewFitKey,
  customPreviewSymbol,
  customPreviewPoolId,
  customPreviewPoolSymbols,
  customPreviewPeriod,
  customPreviewAdjustType,
  customPreviewLimit,
  customFactorParamText,
  customFactorDisplayMode,
  selectedCustomStrategyId,
  showNewStrategyDialog,
  showEditStrategyDialog,
  showStrategyParamDialog,
  showResearchStrategyParamDialog,
  newStrategyDraft,
  editStrategyDraft,
  customStrategyForm,
  strategyPreviewPoolId,
  strategyPreviewPoolSymbols,
  strategyPreviewSymbol,
  strategyPreviewPeriod,
  strategyPreviewAdjustType,
  strategyPreviewLimit,
  strategyPreviewInitialCash,
  strategyPreviewFeeRate,
  strategyPreviewSlippageRate,
  strategyPreviewCandles,
  strategyPreviewResult,
  strategyPreviewFitKey,
  showStrategyPreviewEquity,
  strategyResearchStrategyId,
  strategyResearchParams,
  strategyResearchCandles,
  strategyResearchResult,
  strategyResearchFitKey,
  showStrategyResearchEquity,
  realtimeSelectedFactors,
  realtimeStrategyId,
  realtimeStrategyParams,
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
  showRealtimeStrategyParamDialog,
  strategyInitialCash,
  strategyFeeRate,
  strategySlippageRate,
  strategyResearchStart,
  strategyResearchEnd,
  showVwap,
  showMa,
  showEma,
  showBollinger,
  maPeriod,
  emaPeriod,
  bollingerPeriod,
  bollingerMultiplier,
  visibleCandleCount,
  chartFitKey,
  loadingOlder,
  reachedHistoryStart,
  loadingOlderHistory,
  reachedHistoryStartForHistory,
  loading,
  message,
  error,
  selectedPool,
  enabledPoolSymbols,
  hasRunningTask,
  enabledCustomFactors,
  selectedCustomFactor,
  enabledCustomStrategies,
  selectedCustomStrategy,
  selectedResearchStrategy,
  selectedRealtimeStrategy,
  previewFactorKey,
  previewFactorSeries,
  selectedCustomFactors,
  factorSeriesMeta,
  setError,
  showToast,
  loadPools,
  loadPoolSymbols,
  loadCustomFactors,
  loadCustomStrategies,
  loadTasks,
  loadChart,
  loadHistoryChart,
  loadOlderChartData,
  loadOlderHistoryChartData,
  loadFactorValues,
  bootstrap,
  customFactorKey,
  customFactorIdFromKey,
  customFactorColor,
  prettyJson,
  parseJsonObject,
  selectCustomFactor,
  selectCustomStrategy,
  resetCustomStrategyForm,
  openNewCustomStrategyDialog,
  closeNewCustomStrategyDialog,
  openEditCustomStrategyDialog,
  closeEditCustomStrategyDialog,
  openStrategyParamDialog,
  closeStrategyParamDialog,
  openResearchStrategyParamDialog,
  closeResearchStrategyParamDialog,
  openRealtimeStrategyParamDialog,
  closeRealtimeStrategyParamDialog,
  openNewCustomFactorDialog,
  closeNewCustomFactorDialog,
  openEditCustomFactorDialog,
  closeEditCustomFactorDialog,
  openParamDialog,
  closeParamDialog,
  openResearchParamDialog,
  closeResearchParamDialog,
  openRealtimeIndicatorDialog,
  closeRealtimeIndicatorDialog,
  openRealtimeFactorDialog,
  closeRealtimeFactorDialog,
  openResearchFactorDialog,
  closeResearchFactorDialog,
  openSimpleParamDialog,
  closeSimpleParamDialog,
  simpleParamTitle,
  researchParamLabel,
  compactJson,
  factorDisplayModeLabel,
  resetCustomFactorForm,
  createCustomFactorFromDialog,
  saveCustomFactor,
  saveCustomFactorMeta,
  removeCustomFactor,
  runCustomFactorPreview,
  createCustomStrategyFromDialog,
  saveCustomStrategy,
  saveCustomStrategyMeta,
  removeCustomStrategy,
  strategyRunPayload,
  runCustomStrategyPreview,
  runStrategyResearch,
  realtimePayload,
  applyRealtimeSnapshot,
  mergeStrategySignals,
  pullRealtimeUpdates,
  scheduleRealtimePolling,
  startRealtime,
  stopRealtime,
  refreshRealtime,
  openNewPoolDialog,
  closeNewPoolDialog,
  openEditPoolDialog,
  closeEditPoolDialog,
  handleCreatePool,
  handleUpdatePool,
  handleDeletePool,
  handleAddPoolSymbol,
  handleSearchSecurities,
  selectSecurity,
  addSelectedSecurity,
  savePoolSymbolName,
  togglePoolSymbol,
  deletePoolSymbol,
  toggleSelectedSymbol,
  selectAllEnabled,
  symbolLabel,
  taskSymbolLabel,
  submitSelectedSync,
  submitPoolSync,
  formatMoney,
  formatPct
})

onMounted(() => {
  bootstrap()
  timer = window.setInterval(async () => {
    await loadTasks()
    if (hasRunningTask.value) await loadChart()
  }, 3000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  clearToastTimer()
  if (realtimeTimer) window.clearInterval(realtimeTimer)
  stopRealtime(false)
})
</script>

<template>
  <main class="app-frame" :class="{ collapsed: navCollapsed }">
    <SideNav :tabs="tabs" :active-tab="activeTab" :collapsed="navCollapsed" @update:active-tab="(value) => activeTab = value as TabName" @update:collapsed="navCollapsed = $event" />

    <section class="content-shell">
      <ToastMessage :message="message" :error="error" />
      <PoolView v-if="activeTab === 'pools'" />
      <SyncView v-if="activeTab === 'sync'" />
      <HistoryBoardView v-if="activeTab === 'history'" />
      <RealtimeBoardView v-if="activeTab === 'realtime'" />
      <CustomFactorView v-if="activeTab === 'customFactors'" />
      <CustomStrategyView v-if="activeTab === 'customStrategies'" />
      <StrategyResearchView v-if="activeTab === 'strategyResearch'" />
      <FactorResearchView v-if="activeTab === 'research'" />
      <AppDialogs />
    </section>
  </main>
</template>

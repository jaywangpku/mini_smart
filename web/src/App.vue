<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { fetchPoolSymbols, initDb } from './api'
import { customFactorColor, customFactorIdFromKey, customFactorKey, parseJsonObject, prettyJson } from './appHelpers'
import { tabs, type TabName } from './navigation'
import { formatMoney, formatPct } from './utils'
import { useKlineIndicators } from './composables/useKlineIndicators'
import { useCustomFactors } from './composables/useCustomFactors'
import { useCustomStrategies } from './composables/useCustomStrategies'
import { usePools } from './composables/usePools'
import { useAuth } from './composables/useAuth'
import { useRealtimeBoard } from './composables/useRealtimeBoard'
import { useResearchCharts } from './composables/useResearchCharts'
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
import AuthView from './views/AuthView.vue'
import AccountView from './views/AccountView.vue'
import AppDialogs from './views/AppDialogs.vue'

const activeTab = ref<TabName>('pools')
const navCollapsed = ref(false)
const selectedSymbols = ref<string[]>([])
const researchSymbol = ref('')
const period = ref('1min')
const adjustType = ref('forward')
const researchStart = ref('')
const researchEnd = ref('')
const selectedFactors = ref<string[]>([])
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
const loading = ref(false)
const { message, error, showToast, setError, clearToastTimer } = useToast()
const {
  currentUser,
  authReady,
  authMode,
  authForm,
  authLoading,
  bootstrapAuth,
  submitAuth: submitAuthBase,
  signOut
} = useAuth({ setError })
let timer: number | undefined

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

const {
  candles,
  historyCandles,
  historyFitKey,
  factors,
  strategyResearchFactors,
  chartFitKey,
  loadingOlder,
  reachedHistoryStart,
  loadingOlderHistory,
  reachedHistoryStartForHistory,
  loadChart,
  loadHistoryChart,
  loadOlderChartData,
  loadOlderHistoryChartData,
  loadFactorValues,
  loadStrategyResearchFactors
} = useResearchCharts({
  researchSymbol,
  period,
  adjustType,
  researchStart,
  researchEnd,
  selectedCustomFactors,
  customFactorParamText,
  strategyResearchCandles,
  strategyResearchStart,
  strategyResearchEnd,
  error,
  setError
})

const {
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
} = useRealtimeBoard({
  researchSymbol,
  period,
  adjustType,
  customFactorParamText,
  realtimeStrategyId,
  realtimeStrategyParams,
  strategyInitialCash,
  strategyFeeRate,
  strategySlippageRate,
  setError
})

async function runStrategyResearch() {
  await runStrategyResearchBase()
  await loadStrategyResearchFactors()
}

async function submitAuth() {
  const user = await submitAuthBase()
  if (user) await bootstrap()
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

async function startApp() {
  await bootstrapAuth()
  if (currentUser.value) await bootstrap()
}

function compactJson(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw || '{}'))
  } catch {
    return raw || '{}'
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
  currentUser,
  authReady,
  authMode,
  authForm,
  authLoading,
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
  submitAuth,
  signOut,
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
  startApp()
  timer = window.setInterval(async () => {
    if (!currentUser.value) return
    await loadTasks()
    if (hasRunningTask.value) await loadChart()
  }, 3000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  clearToastTimer()
  stopRealtime(false)
})
</script>

<template>
  <AuthView v-if="authReady && !currentUser" />
  <main v-else-if="!authReady" class="app-frame">
    <section class="content-shell">
      <ToastMessage :message="message" :error="error" />
      <div class="empty-state">加载中...</div>
    </section>
  </main>
  <main v-else class="app-frame" :class="{ collapsed: navCollapsed }">
    <SideNav
      :tabs="tabs"
      :active-tab="activeTab"
      :collapsed="navCollapsed"
      :username="currentUser?.username"
      @logout="signOut"
      @update:active-tab="(value) => activeTab = value as TabName"
      @update:collapsed="navCollapsed = $event"
    />

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
      <AccountView v-if="activeTab === 'account'" />
      <AppDialogs />
    </section>
  </main>
</template>

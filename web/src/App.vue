<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import {
  addPoolSymbol,
  createCustomFactor,
  createCustomStrategy,
  createBatchSyncTask,
  createPool,
  deleteCustomFactor,
  deleteCustomStrategy,
  deletePool,
  fetchCandles,
  fetchCustomFactors,
  fetchCustomStrategies,
  fetchCustomFactorValues,
  fetchPoolSymbols,
  fetchPools,
  fetchSecurityInfo,
  fetchTasks,
  initDb,
  previewCustomFactor,
  removePoolSymbol,
  runCustomStrategy,
  searchSecurities,
  setPoolSymbolEnabled,
  syncPool,
  syncPoolAllPeriods,
  updateCustomFactor,
  updateCustomStrategy,
  updatePool,
  updatePoolSymbol,
  type Candle,
  type CustomFactor,
  type CustomStrategy,
  type FactorValuePoint,
  type PoolRow,
  type PoolSymbolRow,
  type SecurityInfo,
  type SecurityRow,
  type StrategyRunResult,
  type SyncTask
} from './api'
import { defaultFactorSource, defaultStrategySource } from './defaultSources'
import { dateRange, formatMoney, formatPct, localDateString } from './utils'
import CodeEditor from './components/CodeEditor.vue'
import KlineChart from './components/KlineChart.vue'
import SideNav from './components/SideNav.vue'
import StrategyResultPanel from './components/StrategyResultPanel.vue'
import ToastMessage from './components/ToastMessage.vue'

type TabName = 'pools' | 'sync' | 'research' | 'customFactors' | 'strategyResearch' | 'customStrategies'
type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }

const tabs: Array<{ id: TabName; label: string; icon: unknown }> = [
  { id: 'pools', label: '股票池管理', icon: Database },
  { id: 'sync', label: '数据同步', icon: Play },
  { id: 'customFactors', label: '自定义因子', icon: Code2 },
  { id: 'research', label: '因子研究', icon: BarChart3 },
  { id: 'customStrategies', label: '自定义策略', icon: Code2 },
  { id: 'strategyResearch', label: '策略研究', icon: BarChart3 }
]

const activeTab = ref<TabName>('pools')
const navCollapsed = ref(false)
const pools = ref<PoolRow[]>([])
const selectedPoolId = ref('default')
const poolSymbols = ref<PoolSymbolRow[]>([])
const customFactors = ref<CustomFactor[]>([])
const customStrategies = ref<CustomStrategy[]>([])
const tasks = ref<SyncTask[]>([])
const candles = ref<Candle[]>([])
const factors = ref<ChartFactorPoint[]>([])
const selectedSymbols = ref<string[]>([])
const researchSymbol = ref('')
const showNewPoolDialog = ref(false)
const showEditPoolDialog = ref(false)
const newPoolDraft = ref({ name: '', description: '' })
const editPoolDraft = ref({ name: '', description: '' })
const newSymbol = ref('MSTU.US')
const newSymbolName = ref('')
const securityMarket = ref('US')
const securityQuery = ref('MSTU')
const securityResults = ref<SecurityRow[]>([])
const selectedSecurity = ref<SecurityInfo | null>(null)
const searchingSecurities = ref(false)
const period = ref('1min')
const adjustType = ref('forward')
const syncMode = ref<'incremental' | 'range'>('incremental')
const start = ref('2025-01-01')
const end = ref(localDateString())
const selectedFactors = ref<string[]>([])
const selectedCustomFactorId = ref('')
const showNewFactorDialog = ref(false)
const showEditFactorDialog = ref(false)
const showParamDialog = ref(false)
const showResearchParamDialog = ref(false)
const editingResearchParamKey = ref('')
const activeParamDialog = ref<'ma' | 'ema' | 'boll' | ''>('')
const newFactorDraft = ref({
  code: '',
  name: '',
  description: ''
})
const editFactorDraft = ref({
  code: '',
  name: '',
  description: '',
  enabled: true
})
const customFactorForm = ref({
  code: 'my_factor',
  name: '我的因子',
  description: '',
  source_code: defaultFactorSource(),
  default_params: '{\n  "n": 5\n}',
  enabled: true
})
const customFactorPreview = ref<FactorValuePoint[]>([])
const customPreviewCandles = ref<Candle[]>([])
const customPreviewFactors = ref<ChartFactorPoint[]>([])
const customPreviewFitKey = ref(0)
const customPreviewSymbol = ref('')
const customPreviewPoolId = ref('default')
const customPreviewPoolSymbols = ref<PoolSymbolRow[]>([])
const customPreviewPeriod = ref('1min')
const customPreviewAdjustType = ref('forward')
const customPreviewLimit = ref(120)
const customFactorParamText = ref<Record<string, string>>({})
const selectedCustomStrategyId = ref('')
const showNewStrategyDialog = ref(false)
const showEditStrategyDialog = ref(false)
const showStrategyParamDialog = ref(false)
const showResearchStrategyParamDialog = ref(false)
const newStrategyDraft = ref({ code: '', name: '', description: '' })
const editStrategyDraft = ref({ code: '', name: '', description: '', enabled: true })
const customStrategyForm = ref({
  code: 'momentum_strategy',
  name: '动量策略',
  description: '',
  source_code: defaultStrategySource(),
  default_params: '{\n  "buy_size": 100,\n  "threshold": 0.01\n}',
  enabled: true
})
const strategyPreviewPoolId = ref('default')
const strategyPreviewPoolSymbols = ref<PoolSymbolRow[]>([])
const strategyPreviewSymbol = ref('')
const strategyPreviewPeriod = ref('1min')
const strategyPreviewAdjustType = ref('forward')
const strategyPreviewLimit = ref(300)
const strategyPreviewInitialCash = ref(100000)
const strategyPreviewFeeRate = ref(0.0003)
const strategyPreviewSlippageRate = ref(0.0002)
const strategyPreviewCandles = ref<Candle[]>([])
const strategyPreviewResult = ref<StrategyRunResult | null>(null)
const strategyPreviewFitKey = ref(0)
const showStrategyPreviewEquity = ref(false)
const strategyResearchStrategyId = ref('')
const strategyResearchParams = ref('{}')
const strategyResearchCandles = ref<Candle[]>([])
const strategyResearchResult = ref<StrategyRunResult | null>(null)
const strategyResearchFitKey = ref(0)
const showStrategyResearchEquity = ref(false)
const strategyInitialCash = ref(100000)
const strategyFeeRate = ref(0.0003)
const strategySlippageRate = ref(0.0002)
const strategyResearchStart = ref('')
const strategyResearchEnd = ref('')
const showVwap = ref(true)
const showMa = ref(false)
const showEma = ref(false)
const showBollinger = ref(false)
const maPeriod = ref(20)
const emaPeriod = ref(20)
const bollingerPeriod = ref(20)
const bollingerMultiplier = ref(2)
const visibleCandleCount = ref(160)
const chartFitKey = ref(0)
const loadingOlder = ref(false)
const reachedHistoryStart = ref(false)
const loading = ref(false)
const message = ref('')
const error = ref('')
let toastTimer: number | undefined
let timer: number | undefined

const selectedPool = computed(() => pools.value.find((pool) => pool.id === selectedPoolId.value))
const enabledPoolSymbols = computed(() => poolSymbols.value.filter((row) => row.enabled))
const hasRunningTask = computed(() => tasks.value.some((task) => task.status === 'queued' || task.status === 'running'))
const enabledCustomFactors = computed(() => customFactors.value.filter((factor) => factor.enabled))
const selectedCustomFactor = computed(() => customFactors.value.find((factor) => factor.id === selectedCustomFactorId.value))
const enabledCustomStrategies = computed(() => customStrategies.value.filter((strategy) => strategy.enabled))
const selectedCustomStrategy = computed(() => customStrategies.value.find((strategy) => strategy.id === selectedCustomStrategyId.value))
const selectedResearchStrategy = computed(() => customStrategies.value.find((strategy) => strategy.id === strategyResearchStrategyId.value))
const previewFactorKey = 'custom_preview'
const previewFactorSeries = computed(() => [
  {
    key: previewFactorKey,
    label: selectedCustomFactor.value?.name || '自定义因子',
    color: '#a78bfa',
    zeroLine: true
  }
])
const selectedCustomFactors = computed(() => selectedFactors.value.filter((key) => key.startsWith('custom:')))
const factorSeriesMeta = computed(() => {
  const custom = enabledCustomFactors.value.map((factor, index) => ({
    key: customFactorKey(factor.id),
    label: factor.name,
    color: customFactorColor(index),
    zeroLine: true
  }))
  return custom
})

function setError(err: unknown, fallback: string) {
  showToast(err instanceof Error ? err.message : fallback, 'error')
}

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

async function loadPools() {
  pools.value = await fetchPools()
  if (!pools.value.some((pool) => pool.id === selectedPoolId.value)) {
    selectedPoolId.value = pools.value[0]?.id || 'default'
  }
  if (!pools.value.some((pool) => pool.id === customPreviewPoolId.value)) {
    customPreviewPoolId.value = selectedPoolId.value
  }
}

async function loadPoolSymbols() {
  if (!selectedPoolId.value) return
  poolSymbols.value = await fetchPoolSymbols(selectedPoolId.value)
  selectedSymbols.value = selectedSymbols.value.filter((symbol) => poolSymbols.value.some((row) => row.symbol === symbol))
  if (!researchSymbol.value && enabledPoolSymbols.value.length) {
    researchSymbol.value = enabledPoolSymbols.value[0].symbol
  }
  if (!customPreviewSymbol.value && enabledPoolSymbols.value.length) {
    customPreviewSymbol.value = enabledPoolSymbols.value[0].symbol
  }
  if (customPreviewPoolId.value === selectedPoolId.value) {
    customPreviewPoolSymbols.value = poolSymbols.value
  }
  if (strategyPreviewPoolId.value === selectedPoolId.value) {
    strategyPreviewPoolSymbols.value = poolSymbols.value
  }
  if (!strategyPreviewSymbol.value && enabledPoolSymbols.value.length) {
    strategyPreviewSymbol.value = enabledPoolSymbols.value[0].symbol
  }
}

async function loadCustomFactors() {
  customFactors.value = await fetchCustomFactors()
  if (!selectedCustomFactorId.value && customFactors.value.length) {
    selectCustomFactor(customFactors.value[0])
  }
  for (const factor of customFactors.value) {
    const key = customFactorKey(factor.id)
    if (!customFactorParamText.value[key]) customFactorParamText.value[key] = prettyJson(factor.default_params)
  }
}

async function loadCustomStrategies() {
  customStrategies.value = await fetchCustomStrategies()
  if (!selectedCustomStrategyId.value && customStrategies.value.length) {
    selectCustomStrategy(customStrategies.value[0])
  }
  if (!strategyResearchStrategyId.value && enabledCustomStrategies.value.length) {
    const strategy = enabledCustomStrategies.value[0]
    strategyResearchStrategyId.value = strategy.id
    strategyResearchParams.value = prettyJson(strategy.default_params)
  }
}

async function loadTasks() {
  tasks.value = await fetchTasks(20)
}

function chartLimitForPeriod(value: string) {
  if (value === 'day') return 500
  if (value === '60min') return 1000
  if (value === '30min') return 1200
  return 2000
}

async function loadChart(options: { resetView?: boolean } = {}) {
  if (!researchSymbol.value) {
    candles.value = []
    factors.value = []
    reachedHistoryStart.value = false
    return
  }
  const limit = chartLimitForPeriod(period.value)
  const nextCandles = await fetchCandles(researchSymbol.value, period.value, adjustType.value, limit)
  const nextFactors = await loadFactorValues(limit)
  candles.value = nextCandles
  factors.value = nextFactors
  reachedHistoryStart.value = false
  if (options.resetView) chartFitKey.value += 1
}

function mergeByTime<T extends { time: number }>(current: T[], incoming: T[]) {
  const byTime = new Map<number, T>()
  for (const item of current) byTime.set(item.time, item)
  for (const item of incoming) byTime.set(item.time, item)
  return [...byTime.values()].sort((a, b) => a.time - b.time)
}

async function loadOlderChartData() {
  if (loadingOlder.value || reachedHistoryStart.value || !researchSymbol.value || !candles.value.length) return
  loadingOlder.value = true
  error.value = ''
  try {
    const endTime = candles.value[0].time - 1
    const range = { end: endTime }
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

function customFactorKey(id: string) {
  return `custom:${id}`
}

function customFactorIdFromKey(key: string) {
  return key.replace(/^custom:/, '')
}

function customFactorColor(index: number) {
  return ['#a78bfa', '#22c55e', '#facc15', '#fb7185', '#2dd4bf', '#c084fc'][index % 6]
}

function prettyJson(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw || '{}'), null, 2)
  } catch {
    return raw || '{}'
  }
}

function parseJsonObject(raw: string) {
  const value = JSON.parse(raw || '{}')
  if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error('参数必须是 JSON object')
  return value as Record<string, unknown>
}

function selectCustomFactor(factor: CustomFactor) {
  selectedCustomFactorId.value = factor.id
  customFactorForm.value = {
    code: factor.code,
    name: factor.name,
    description: factor.description || '',
    source_code: factor.source_code,
    default_params: prettyJson(factor.default_params),
    enabled: Boolean(factor.enabled)
  }
  customFactorPreview.value = []
  customPreviewCandles.value = []
  customPreviewFactors.value = []
}

function selectCustomStrategy(strategy: CustomStrategy) {
  selectedCustomStrategyId.value = strategy.id
  customStrategyForm.value = {
    code: strategy.code,
    name: strategy.name,
    description: strategy.description || '',
    source_code: strategy.source_code,
    default_params: prettyJson(strategy.default_params),
    enabled: Boolean(strategy.enabled)
  }
  strategyPreviewResult.value = null
  strategyPreviewCandles.value = []
  showStrategyPreviewEquity.value = false
}

function resetCustomStrategyForm() {
  selectedCustomStrategyId.value = ''
  customStrategyForm.value = {
    code: 'momentum_strategy',
    name: '动量策略',
    description: '',
    source_code: defaultStrategySource(),
    default_params: '{\n  "buy_size": 100,\n  "threshold": 0.01\n}',
    enabled: true
  }
  strategyPreviewResult.value = null
  strategyPreviewCandles.value = []
  showStrategyPreviewEquity.value = false
}

function openNewCustomStrategyDialog() {
  newStrategyDraft.value = { code: '', name: '', description: '' }
  showNewStrategyDialog.value = true
}

function closeNewCustomStrategyDialog() {
  showNewStrategyDialog.value = false
}

function openEditCustomStrategyDialog() {
  if (!selectedCustomStrategy.value) return
  editStrategyDraft.value = {
    code: customStrategyForm.value.code,
    name: customStrategyForm.value.name,
    description: customStrategyForm.value.description,
    enabled: customStrategyForm.value.enabled
  }
  showEditStrategyDialog.value = true
}

function closeEditCustomStrategyDialog() {
  showEditStrategyDialog.value = false
}

function openStrategyParamDialog() {
  if (!selectedCustomStrategy.value) return
  showStrategyParamDialog.value = true
}

function closeStrategyParamDialog() {
  showStrategyParamDialog.value = false
}

function openResearchStrategyParamDialog() {
  showResearchStrategyParamDialog.value = true
}

function closeResearchStrategyParamDialog() {
  showResearchStrategyParamDialog.value = false
}

function openNewCustomFactorDialog() {
  newFactorDraft.value = {
    code: '',
    name: '',
    description: ''
  }
  showNewFactorDialog.value = true
}

function closeNewCustomFactorDialog() {
  showNewFactorDialog.value = false
}

function openEditCustomFactorDialog() {
  if (!selectedCustomFactor.value) return
  editFactorDraft.value = {
    code: customFactorForm.value.code,
    name: customFactorForm.value.name,
    description: customFactorForm.value.description,
    enabled: customFactorForm.value.enabled
  }
  showEditFactorDialog.value = true
}

function closeEditCustomFactorDialog() {
  showEditFactorDialog.value = false
}

function openParamDialog() {
  if (!selectedCustomFactor.value) return
  showParamDialog.value = true
}

function closeParamDialog() {
  showParamDialog.value = false
}

function openResearchParamDialog(key: string) {
  editingResearchParamKey.value = key
  showResearchParamDialog.value = true
}

function closeResearchParamDialog() {
  showResearchParamDialog.value = false
  editingResearchParamKey.value = ''
}

function openSimpleParamDialog(type: 'ma' | 'ema' | 'boll') {
  activeParamDialog.value = type
}

function closeSimpleParamDialog() {
  activeParamDialog.value = ''
}

function simpleParamTitle() {
  const titles: Record<string, string> = {
    ma: 'MA 参数',
    ema: 'EMA 参数',
    boll: 'BOLL 参数'
  }
  return titles[activeParamDialog.value] || '参数配置'
}

function researchParamLabel(key: string) {
  return factorSeriesMeta.value.find((item) => item.key === key)?.label || '自定义因子'
}

function compactJson(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw || '{}'))
  } catch {
    return raw || '{}'
  }
}

function resetCustomFactorForm() {
  selectedCustomFactorId.value = ''
  customFactorForm.value = {
    code: 'my_factor',
    name: '我的因子',
    description: '',
    source_code: defaultFactorSource(),
    default_params: '{\n  "n": 5\n}',
    enabled: true
  }
  customFactorPreview.value = []
}

async function createCustomFactorFromDialog() {
  const code = newFactorDraft.value.code.trim()
  const name = newFactorDraft.value.name.trim()
  if (!code || !name) {
    showToast('请填写因子编码和因子名称', 'error')
    return
  }
  error.value = ''
  try {
    const saved = await createCustomFactor({
      code,
      name,
      description: newFactorDraft.value.description.trim() || undefined,
      source_code: defaultFactorSource(),
      default_params: { n: 5 },
      enabled: true
    })
    showNewFactorDialog.value = false
    showToast('自定义因子已创建')
    await loadCustomFactors()
    selectCustomFactor(saved)
  } catch (err) {
    setError(err, '创建自定义因子失败')
  }
}

async function saveCustomFactor() {
  error.value = ''
  try {
    const payload = {
      code: customFactorForm.value.code.trim(),
      name: customFactorForm.value.name.trim(),
      description: customFactorForm.value.description.trim() || undefined,
      source_code: customFactorForm.value.source_code,
      default_params: parseJsonObject(customFactorForm.value.default_params),
      enabled: customFactorForm.value.enabled
    }
    const saved = selectedCustomFactorId.value
      ? await updateCustomFactor(selectedCustomFactorId.value, payload)
      : await createCustomFactor(payload)
    showToast('自定义因子已保存')
    await loadCustomFactors()
    selectCustomFactor(saved)
  } catch (err) {
    setError(err, '保存自定义因子失败')
  }
}

async function saveCustomFactorMeta() {
  if (!selectedCustomFactorId.value) return
  error.value = ''
  try {
    const saved = await updateCustomFactor(selectedCustomFactorId.value, {
      code: editFactorDraft.value.code.trim(),
      name: editFactorDraft.value.name.trim(),
      description: editFactorDraft.value.description.trim() || undefined,
      enabled: editFactorDraft.value.enabled
    })
    showToast('因子信息已更新')
    showEditFactorDialog.value = false
    await loadCustomFactors()
    selectCustomFactor(saved)
  } catch (err) {
    setError(err, '修改自定义因子失败')
  }
}

async function removeCustomFactor() {
  if (!selectedCustomFactorId.value) return
  if (!window.confirm(`确认删除自定义因子「${customFactorForm.value.name}」？`)) return
  error.value = ''
  try {
    await deleteCustomFactor(selectedCustomFactorId.value)
    selectedFactors.value = selectedFactors.value.filter((key) => key !== customFactorKey(selectedCustomFactorId.value))
    resetCustomFactorForm()
    await loadCustomFactors()
  } catch (err) {
    setError(err, '删除自定义因子失败')
  }
}

async function runCustomFactorPreview() {
  if (!selectedCustomFactorId.value || !customPreviewSymbol.value) return
  error.value = ''
  try {
    const [previewCandles, previewValues] = await Promise.all([
      fetchCandles(customPreviewSymbol.value, customPreviewPeriod.value, customPreviewAdjustType.value, customPreviewLimit.value),
      previewCustomFactor(selectedCustomFactorId.value, {
      symbol: customPreviewSymbol.value,
      period: customPreviewPeriod.value,
      adjust_type: customPreviewAdjustType.value,
      params: parseJsonObject(customFactorForm.value.default_params),
      limit: customPreviewLimit.value
      })
    ])
    customFactorPreview.value = previewValues
    customPreviewCandles.value = previewCandles
    customPreviewFactors.value = previewValues.map((row) => ({
      time: row.time,
      [previewFactorKey]: row.value ?? null
    }))
    customPreviewFitKey.value += 1
  } catch (err) {
    setError(err, '试运行自定义因子失败')
  }
}

async function createCustomStrategyFromDialog() {
  const code = newStrategyDraft.value.code.trim()
  const name = newStrategyDraft.value.name.trim()
  if (!code || !name) {
    showToast('请填写策略编码和策略名称', 'error')
    return
  }
  error.value = ''
  try {
    const saved = await createCustomStrategy({
      code,
      name,
      description: newStrategyDraft.value.description.trim() || undefined,
      source_code: defaultStrategySource(),
      default_params: { buy_size: 100, threshold: 0.01 },
      enabled: true
    })
    showNewStrategyDialog.value = false
    showToast('自定义策略已创建')
    await loadCustomStrategies()
    selectCustomStrategy(saved)
  } catch (err) {
    setError(err, '创建自定义策略失败')
  }
}

async function saveCustomStrategy() {
  if (!selectedCustomStrategyId.value) return
  error.value = ''
  try {
    const saved = await updateCustomStrategy(selectedCustomStrategyId.value, {
      code: customStrategyForm.value.code.trim(),
      name: customStrategyForm.value.name.trim(),
      description: customStrategyForm.value.description.trim() || undefined,
      source_code: customStrategyForm.value.source_code,
      default_params: parseJsonObject(customStrategyForm.value.default_params),
      enabled: customStrategyForm.value.enabled
    })
    showToast('自定义策略已保存')
    await loadCustomStrategies()
    selectCustomStrategy(saved)
  } catch (err) {
    setError(err, '保存自定义策略失败')
  }
}

async function saveCustomStrategyMeta() {
  if (!selectedCustomStrategyId.value) return
  error.value = ''
  try {
    const saved = await updateCustomStrategy(selectedCustomStrategyId.value, {
      code: editStrategyDraft.value.code.trim(),
      name: editStrategyDraft.value.name.trim(),
      description: editStrategyDraft.value.description.trim() || undefined,
      enabled: editStrategyDraft.value.enabled
    })
    showEditStrategyDialog.value = false
    showToast('策略信息已更新')
    await loadCustomStrategies()
    selectCustomStrategy(saved)
  } catch (err) {
    setError(err, '修改自定义策略失败')
  }
}

async function removeCustomStrategy() {
  if (!selectedCustomStrategyId.value) return
  if (!window.confirm(`确认删除自定义策略「${customStrategyForm.value.name}」？`)) return
  error.value = ''
  try {
    await deleteCustomStrategy(selectedCustomStrategyId.value)
    resetCustomStrategyForm()
    await loadCustomStrategies()
  } catch (err) {
    setError(err, '删除自定义策略失败')
  }
}

function strategyRunPayload(
  symbol: string,
  periodValue: string,
  adjustValue: string,
  limit: number,
  params: Record<string, unknown>,
  cash: number,
  fee: number,
  slippage: number,
  range: { start?: number; end?: number } = {}
) {
  return {
    symbol,
    period: periodValue,
    adjust_type: adjustValue,
    params,
    limit,
    ...range,
    backtest: {
      initial_cash: cash,
      fee_rate: fee,
      slippage_rate: slippage
    }
  }
}

async function runCustomStrategyPreview() {
  if (!selectedCustomStrategyId.value || !strategyPreviewSymbol.value) return
  error.value = ''
  try {
    const [previewCandles, result] = await Promise.all([
      fetchCandles(strategyPreviewSymbol.value, strategyPreviewPeriod.value, strategyPreviewAdjustType.value, strategyPreviewLimit.value),
      runCustomStrategy(
        selectedCustomStrategyId.value,
        strategyRunPayload(
          strategyPreviewSymbol.value,
          strategyPreviewPeriod.value,
          strategyPreviewAdjustType.value,
          strategyPreviewLimit.value,
          parseJsonObject(customStrategyForm.value.default_params),
          strategyPreviewInitialCash.value,
          strategyPreviewFeeRate.value,
          strategyPreviewSlippageRate.value
        )
      )
    ])
    strategyPreviewCandles.value = previewCandles
    strategyPreviewResult.value = result
    showStrategyPreviewEquity.value = false
    strategyPreviewFitKey.value += 1
  } catch (err) {
    setError(err, '试运行自定义策略失败')
  }
}

async function runStrategyResearch() {
  if (!strategyResearchStrategyId.value || !researchSymbol.value) return
  error.value = ''
  try {
    const limit = chartLimitForPeriod(period.value)
    const range = dateRange(strategyResearchStart.value, strategyResearchEnd.value)
    const [nextCandles, result] = await Promise.all([
      fetchCandles(researchSymbol.value, period.value, adjustType.value, limit, range),
      runCustomStrategy(
        strategyResearchStrategyId.value,
        strategyRunPayload(
          researchSymbol.value,
          period.value,
          adjustType.value,
          limit,
          parseJsonObject(strategyResearchParams.value),
          strategyInitialCash.value,
          strategyFeeRate.value,
          strategySlippageRate.value,
          range
        )
      )
    ])
    strategyResearchCandles.value = nextCandles
    strategyResearchResult.value = result
    showStrategyResearchEquity.value = false
    strategyResearchFitKey.value += 1
  } catch (err) {
    setError(err, '运行策略失败')
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

watch(strategyPreviewPoolId, async (poolId) => {
  error.value = ''
  try {
    strategyPreviewPoolSymbols.value = await fetchPoolSymbols(poolId)
    strategyPreviewSymbol.value = strategyPreviewPoolSymbols.value[0]?.symbol || ''
  } catch (err) {
    setError(err, '加载策略测试股票池失败')
  }
})

watch(strategyResearchStrategyId, (strategyId) => {
  const strategy = customStrategies.value.find((item) => item.id === strategyId)
  if (strategy) strategyResearchParams.value = prettyJson(strategy.default_params)
})

function openNewPoolDialog() {
  newPoolDraft.value = { name: '', description: '' }
  showNewPoolDialog.value = true
}

function closeNewPoolDialog() {
  showNewPoolDialog.value = false
}

function openEditPoolDialog() {
  if (!selectedPool.value) return
  editPoolDraft.value = {
    name: selectedPool.value.name,
    description: selectedPool.value.description || ''
  }
  showEditPoolDialog.value = true
}

function closeEditPoolDialog() {
  showEditPoolDialog.value = false
}

async function handleCreatePool() {
  const name = newPoolDraft.value.name.trim()
  if (!name) {
    showToast('请填写股票池名称', 'error')
    return
  }
  error.value = ''
  try {
    const pool = await createPool(name, newPoolDraft.value.description.trim() || undefined)
    showNewPoolDialog.value = false
    showToast('股票池已创建')
    selectedPoolId.value = pool.id
    await loadPools()
    await loadPoolSymbols()
  } catch (err) {
    setError(err, '创建股票池失败')
  }
}

async function handleUpdatePool() {
  if (!selectedPoolId.value) return
  const name = editPoolDraft.value.name.trim()
  if (!name) {
    showToast('请填写股票池名称', 'error')
    return
  }
  error.value = ''
  try {
    await updatePool(selectedPoolId.value, {
      name,
      description: editPoolDraft.value.description.trim() || undefined
    })
    showEditPoolDialog.value = false
    showToast('股票池已更新')
    await loadPools()
  } catch (err) {
    setError(err, '更新股票池失败')
  }
}

async function handleDeletePool() {
  if (!selectedPoolId.value || selectedPoolId.value === 'default') return
  if (!window.confirm(`确认删除股票池「${selectedPool.value?.name || selectedPoolId.value}」？`)) return
  error.value = ''
  try {
    await deletePool(selectedPoolId.value)
    showToast('股票池已删除')
    selectedPoolId.value = 'default'
    await loadPools()
    await loadPoolSymbols()
  } catch (err) {
    setError(err, '删除股票池失败')
  }
}

async function handleAddPoolSymbol() {
  const symbol = newSymbol.value.trim().toUpperCase()
  if (!symbol) return
  error.value = ''
  try {
    await addPoolSymbol(selectedPoolId.value, symbol, undefined, newSymbolName.value.trim() || undefined)
    newSymbol.value = ''
    newSymbolName.value = ''
    await Promise.all([loadPools(), loadPoolSymbols()])
  } catch (err) {
    setError(err, '添加股票失败')
  }
}

async function handleSearchSecurities() {
  searchingSecurities.value = true
  error.value = ''
  try {
    securityResults.value = await searchSecurities(securityMarket.value, securityQuery.value.trim(), 50)
    selectedSecurity.value = null
    if (!securityResults.value.length) showToast('没有找到匹配股票')
  } catch (err) {
    setError(err, '查询可添加股票失败')
  } finally {
    searchingSecurities.value = false
  }
}

async function selectSecurity(row: SecurityRow) {
  selectedSecurity.value = {
    ...row,
    exchange: null,
    currency: null
  }
  error.value = ''
  try {
    selectedSecurity.value = await fetchSecurityInfo(row.symbol)
  } catch (err) {
    setError(err, '查询股票基本信息失败')
  }
}

async function addSelectedSecurity() {
  if (!selectedSecurity.value) return
  error.value = ''
  try {
    await addPoolSymbol(
      selectedPoolId.value,
      selectedSecurity.value.symbol,
      undefined,
      selectedSecurity.value.name || selectedSecurity.value.name_cn || selectedSecurity.value.name_hk || selectedSecurity.value.name_en || undefined
    )
    showToast(`${selectedSecurity.value.symbol} 已加入股票池`)
    await Promise.all([loadPools(), loadPoolSymbols()])
  } catch (err) {
    setError(err, '添加股票失败')
  }
}

async function savePoolSymbolName(row: PoolSymbolRow) {
  await updatePoolSymbol(selectedPoolId.value, row.symbol, { name: row.name?.trim() || undefined })
  await loadPoolSymbols()
}

async function togglePoolSymbol(row: PoolSymbolRow) {
  await setPoolSymbolEnabled(selectedPoolId.value, row.symbol, !row.enabled)
  await loadPoolSymbols()
}

async function deletePoolSymbol(row: PoolSymbolRow) {
  await removePoolSymbol(selectedPoolId.value, row.symbol)
  await Promise.all([loadPools(), loadPoolSymbols()])
}

function toggleSelectedSymbol(symbol: string) {
  selectedSymbols.value = selectedSymbols.value.includes(symbol)
    ? selectedSymbols.value.filter((item) => item !== symbol)
    : [...selectedSymbols.value, symbol]
}

function selectAllEnabled() {
  selectedSymbols.value = enabledPoolSymbols.value.map((row) => row.symbol)
}

function symbolLabel(row: PoolSymbolRow) {
  return row.name?.trim() || row.symbol
}

function taskSymbolLabel(task: SyncTask) {
  return task.name?.trim() || task.symbol
}

async function submitSelectedSync() {
  if (!selectedSymbols.value.length) return
  loading.value = true
  error.value = ''
  try {
    const response = await createBatchSyncTask({
      symbols: selectedSymbols.value,
      period: period.value,
      adjust_type: adjustType.value,
      start: syncMode.value === 'range' ? start.value || undefined : undefined,
      end: end.value || undefined
    })
    showToast(`已提交 ${response.tasks.length} 个同步任务`)
    await loadTasks()
  } catch (err) {
    setError(err, '批量同步失败')
  } finally {
    loading.value = false
  }
}

async function submitPoolSync() {
  loading.value = true
  error.value = ''
  try {
    const payload = {
      adjust_type: adjustType.value,
      start: syncMode.value === 'range' ? start.value || undefined : undefined,
      end: end.value || undefined
    }
    const response = period.value === 'all'
      ? await syncPoolAllPeriods(selectedPoolId.value, payload)
      : await syncPool(selectedPoolId.value, { period: period.value, ...payload })
    showToast(`股票池同步已提交：${response.tasks.length} 个任务`)
    await loadTasks()
  } catch (err) {
    setError(err, '股票池同步失败')
  } finally {
    loading.value = false
  }
}

watch(selectedPoolId, async () => {
  await loadPoolSymbols()
  if (!enabledPoolSymbols.value.some((row) => row.symbol === researchSymbol.value)) {
    researchSymbol.value = enabledPoolSymbols.value[0]?.symbol || ''
  }
  await loadChart()
})

watch([researchSymbol, period, adjustType, selectedFactors, customFactorParamText], () => {
  loadChart().catch((err) => setError(err, '加载图表失败'))
}, { deep: true })

onMounted(() => {
  bootstrap()
  timer = window.setInterval(async () => {
    await loadTasks()
    if (hasRunningTask.value) await loadChart()
  }, 3000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  if (toastTimer) window.clearTimeout(toastTimer)
})
</script>

<template>
  <main class="app-frame" :class="{ collapsed: navCollapsed }">
    <SideNav :tabs="tabs" :active-tab="activeTab" :collapsed="navCollapsed" @update:active-tab="(value) => activeTab = value as TabName" @update:collapsed="navCollapsed = $event" />

    <section class="content-shell">
      <ToastMessage :message="message" :error="error" />

      <section v-if="activeTab === 'pools'" class="tab-grid">
      <aside class="panel">
        <div class="panel-title">
          <Database :size="17" />
          <span>股票池</span>
        </div>
        <button class="submit secondary" @click="openNewPoolDialog">
          <Plus :size="17" />
          <span>新建股票池</span>
        </button>
        <div class="pool-card-list">
          <button
            v-for="pool in pools"
            :key="pool.id"
            :class="{ selected: selectedPoolId === pool.id }"
            type="button"
            @click="selectedPoolId = pool.id"
          >
            <strong>{{ pool.name }}</strong>
            <span>{{ pool.symbol_count || 0 }} 只股票</span>
            <small v-if="pool.description">{{ pool.description }}</small>
          </button>
        </div>
        <div class="factor-side-actions">
          <div class="sync-actions">
            <button class="submit secondary" title="修改股票池" @click="openEditPoolDialog">
              <Edit3 :size="17" />
            </button>
            <button class="submit danger" title="删除股票池" :disabled="selectedPoolId === 'default'" @click="handleDeletePool">
              <Trash2 :size="17" />
            </button>
          </div>
        </div>
      </aside>

      <div v-if="showNewPoolDialog" class="modal-backdrop" @click.self="closeNewPoolDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Database :size="17" />
            <span>新建股票池</span>
          </div>
          <label>
            股票池名称
            <input v-model="newPoolDraft.name" placeholder="例如：杠杆ETF研究池" @keyup.enter="handleCreatePool" />
          </label>
          <label>
            描述
            <textarea v-model="newPoolDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewPoolDialog">取消</button>
            <button class="submit compact" @click="handleCreatePool">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditPoolDialog" class="modal-backdrop" @click.self="closeEditPoolDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Database :size="17" />
            <span>修改股票池</span>
          </div>
          <label>
            股票池名称
            <input v-model="editPoolDraft.name" placeholder="股票池名称" @keyup.enter="handleUpdatePool" />
          </label>
          <label>
            描述
            <textarea v-model="editPoolDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditPoolDialog">取消</button>
            <button class="submit compact" @click="handleUpdatePool">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <section class="main-panel">
        <div class="chart-head">
          <div>
            <h2>{{ selectedPool?.name || '股票池' }}</h2>
            <p>{{ poolSymbols.length }} 只股票，{{ enabledPoolSymbols.length }} 只启用</p>
          </div>
        </div>
        <div class="security-search">
          <div class="security-search-bar">
            <select v-model="securityMarket" title="市场">
              <option value="US">美股</option>
              <option value="HK">港股</option>
              <option value="CN">A股</option>
              <option value="SG">新加坡</option>
            </select>
            <input v-model="securityQuery" placeholder="搜索股票代码或名称，例如 MSTU / MicroStrategy" @keyup.enter="handleSearchSecurities" />
            <button class="submit secondary compact" :disabled="searchingSecurities" @click="handleSearchSecurities">
              <Search :size="16" />
              <span>{{ searchingSecurities ? '查询中' : '查询' }}</span>
            </button>
          </div>
          <div v-if="securityResults.length" class="security-results">
            <button
              v-for="row in securityResults"
              :key="row.symbol"
              :class="{ selected: selectedSecurity?.symbol === row.symbol }"
              type="button"
              @click="selectSecurity(row)"
            >
              <strong>{{ row.symbol }}</strong>
              <span>{{ row.name || row.name_cn || row.name_hk || row.name_en || '-' }}</span>
              <small>{{ row.market || securityMarket }}</small>
            </button>
          </div>
          <div v-if="selectedSecurity" class="security-info">
            <div>
              <strong>{{ selectedSecurity.symbol }}</strong>
              <span>{{ selectedSecurity.name || selectedSecurity.name_cn || selectedSecurity.name_hk || selectedSecurity.name_en || '-' }}</span>
            </div>
            <dl>
              <div><dt>交易所</dt><dd>{{ selectedSecurity.exchange || '-' }}</dd></div>
              <div><dt>币种</dt><dd>{{ selectedSecurity.currency || '-' }}</dd></div>
              <div><dt>每手</dt><dd>{{ selectedSecurity.lot_size || '-' }}</dd></div>
              <div><dt>EPS</dt><dd>{{ selectedSecurity.eps_ttm ?? selectedSecurity.eps ?? '-' }}</dd></div>
              <div><dt>BPS</dt><dd>{{ selectedSecurity.bps ?? '-' }}</dd></div>
              <div><dt>股息率</dt><dd>{{ selectedSecurity.dividend_yield ?? '-' }}</dd></div>
            </dl>
            <button class="submit compact" @click="addSelectedSecurity">
              <Plus :size="16" />
              <span>加入股票池</span>
            </button>
          </div>
          <details class="manual-add">
            <summary>手动添加</summary>
            <div class="add-symbol-row">
              <input v-model="newSymbol" placeholder="MSTU.US" @keyup.enter="handleAddPoolSymbol" />
              <input v-model="newSymbolName" placeholder="股票名称，例如 MicroStrategy" @keyup.enter="handleAddPoolSymbol" />
              <button class="icon-button primary" title="加入股票池" @click="handleAddPoolSymbol">
                <Plus :size="18" />
              </button>
            </div>
          </details>
        </div>
        <div class="pool-table">
          <div class="pool-row header">
            <span>股票</span>
            <span>名称</span>
            <span>启用</span>
            <span>操作</span>
          </div>
          <div v-for="row in poolSymbols" :key="row.symbol" class="pool-row">
            <span>{{ row.symbol }}</span>
            <input v-model="row.name" class="name-input" placeholder="股票名称" @keyup.enter="savePoolSymbolName(row)" />
            <input type="checkbox" :checked="Boolean(row.enabled)" @change="togglePoolSymbol(row)" />
            <button class="icon-button" title="保存名称" @click="savePoolSymbolName(row)">
              <Save :size="16" />
            </button>
            <button class="icon-button danger" title="移除" @click="deletePoolSymbol(row)">
              <Trash2 :size="16" />
            </button>
          </div>
        </div>
      </section>
      </section>

      <section v-if="activeTab === 'sync'" class="tab-grid">
      <aside class="panel">
        <div class="panel-title">
          <Play :size="17" />
          <span>同步参数</span>
        </div>
        <label>
          股票池
          <select v-model="selectedPoolId">
            <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
          </select>
        </label>
        <label>
          周期
          <select v-model="period">
            <option value="all">全部周期</option>
            <option value="1min">1min</option>
            <option value="5min">5min</option>
            <option value="15min">15min</option>
            <option value="30min">30min</option>
            <option value="60min">60min</option>
            <option value="day">day</option>
          </select>
        </label>
        <label>
          复权
          <select v-model="adjustType">
            <option value="forward">前复权</option>
            <option value="no_adjust">不复权</option>
          </select>
        </label>
        <label>
          同步方式
          <select v-model="syncMode">
            <option value="incremental">增量更新</option>
            <option value="range">指定时间范围</option>
          </select>
        </label>
        <label>
          开始日期
          <input v-model="start" type="date" :disabled="syncMode === 'incremental'" />
        </label>
        <label>
          结束日期
          <input v-model="end" type="date" />
        </label>
        <div class="sync-actions">
          <button class="submit" :disabled="loading || !selectedSymbols.length || period === 'all'" @click="submitSelectedSync">
            <Play :size="17" />
            <span>同步选中的股票</span>
          </button>
          <button class="submit secondary" :disabled="loading || !enabledPoolSymbols.length" @click="submitPoolSync">
            <RefreshCw :size="17" />
            <span>同步当前股票池</span>
          </button>
        </div>
      </aside>

      <section class="main-panel">
        <div class="chart-head">
          <div>
            <h2>选择同步股票</h2>
            <p>已选择 {{ selectedSymbols.length }} / {{ enabledPoolSymbols.length }}</p>
          </div>
          <button class="ghost" @click="selectAllEnabled">全选启用</button>
        </div>
        <div class="selector-grid">
          <button
            v-for="row in enabledPoolSymbols"
            :key="row.symbol"
            :class="{ selected: selectedSymbols.includes(row.symbol) }"
            @click="toggleSelectedSymbol(row.symbol)"
          >
            <strong>{{ symbolLabel(row) }}</strong>
            <small v-if="row.name">{{ row.symbol }}</small>
          </button>
        </div>
        <div class="tasks">
          <div class="tasks-head">
            <div>
              <h2>同步任务</h2>
              <p>最新 20 条</p>
            </div>
            <button class="ghost" @click="loadTasks">刷新任务</button>
          </div>
          <div class="task-table">
            <div class="task-row header">
              <span>任务</span>
              <span>标的</span>
              <span>名称</span>
              <span>状态</span>
              <span>写入</span>
              <span>错误</span>
            </div>
            <div v-for="task in tasks" :key="task.id" class="task-row">
              <span>{{ task.id }}</span>
              <span>{{ task.symbol }}</span>
              <span>{{ taskSymbolLabel(task) }}</span>
              <span :class="['status', task.status]">{{ task.status }}</span>
              <span>{{ task.rows_written }}</span>
              <span class="task-error">{{ task.error || '' }}</span>
            </div>
          </div>
        </div>
      </section>
      </section>

      <section v-if="activeTab === 'customFactors'" class="custom-factor-layout">
        <aside class="panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>自定义因子</span>
          </div>
          <button class="submit secondary" @click="openNewCustomFactorDialog">
            <Plus :size="17" />
            <span>新建因子</span>
          </button>
          <div class="custom-factor-list">
            <button
              v-for="factor in customFactors"
              :key="factor.id"
              :class="{ selected: selectedCustomFactorId === factor.id }"
              type="button"
              @click="selectCustomFactor(factor)"
            >
              <strong>{{ factor.name }}</strong>
              <span>{{ factor.code }} · {{ factor.enabled ? '启用' : '停用' }}</span>
            </button>
          </div>
          <div v-if="selectedCustomFactor" class="factor-side-actions">
            <div class="factor-side-summary">
              <strong>{{ customFactorForm.name }}</strong>
              <span>{{ customFactorForm.code }} · {{ customFactorForm.enabled ? '启用' : '停用' }}</span>
              <p v-if="customFactorForm.description">{{ customFactorForm.description }}</p>
            </div>
            <div class="sync-actions">
              <button class="submit secondary" title="修改信息" @click="openEditCustomFactorDialog">
                <Edit3 :size="17" />
              </button>
              <button class="submit" title="保存代码" @click="saveCustomFactor">
                <Save :size="17" />
              </button>
              <button class="submit danger" title="删除因子" @click="removeCustomFactor">
                <Trash2 :size="17" />
              </button>
            </div>
          </div>
        </aside>

        <section class="main-panel custom-factor-editor">
          <div v-if="selectedCustomFactor" class="factor-workbench">
            <div class="param-strip">
              <span>因子参数</span>
              <code>{{ customFactorForm.default_params.replace(/\s+/g, ' ') }}</code>
              <button class="ghost" @click="openParamDialog">编辑参数</button>
            </div>
            <CodeEditor v-model="customFactorForm.source_code" language="python" />
            <div class="preview-config compact-preview">
              <label>
                股票池
                <select v-model="customPreviewPoolId">
                  <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
                </select>
              </label>
              <label>
                测试股票
                <select v-model="customPreviewSymbol">
                  <option v-for="row in customPreviewPoolSymbols" :key="row.symbol" :value="row.symbol">
                    {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
                  </option>
                </select>
              </label>
              <label>
                周期
                <select v-model="customPreviewPeriod">
                  <option value="1min">1min</option>
                  <option value="5min">5min</option>
                  <option value="15min">15min</option>
                  <option value="30min">30min</option>
                  <option value="60min">60min</option>
                  <option value="day">day</option>
                </select>
              </label>
              <label>
                复权
                <select v-model="customPreviewAdjustType">
                  <option value="forward">前复权</option>
                  <option value="no_adjust">不复权</option>
                </select>
              </label>
              <label>
                样本数
                <input v-model.number="customPreviewLimit" type="number" min="20" max="1000" />
              </label>
              <button class="submit secondary compact" :disabled="!selectedCustomFactorId" @click="runCustomFactorPreview">
                <Play :size="16" />
                <span>试运行</span>
              </button>
            </div>
            <KlineChart
              v-if="customPreviewCandles.length"
              :candles="customPreviewCandles"
              :factors="customPreviewFactors"
              :selected-factors="[previewFactorKey]"
              :factor-series="previewFactorSeries"
              :fit-key="customPreviewFitKey"
              :show-vwap="false"
              :show-ma="false"
              :show-ema="false"
              :show-bollinger="false"
              :ma-period="maPeriod"
              :ema-period="emaPeriod"
              :bollinger-period="bollingerPeriod"
              :bollinger-multiplier="bollingerMultiplier"
              v-model:visible-candle-count="visibleCandleCount"
              @load-older="() => {}"
            />
          </div>
          <div v-else class="empty-state">请先在左侧新建或选择一个自定义因子</div>
        </section>
      </section>

      <section v-if="activeTab === 'customStrategies'" class="custom-factor-layout">
        <aside class="panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>自定义策略</span>
          </div>
          <button class="submit secondary" @click="openNewCustomStrategyDialog">
            <Plus :size="17" />
            <span>新建策略</span>
          </button>
          <div class="custom-factor-list">
            <button
              v-for="strategy in customStrategies"
              :key="strategy.id"
              :class="{ selected: selectedCustomStrategyId === strategy.id }"
              type="button"
              @click="selectCustomStrategy(strategy)"
            >
              <strong>{{ strategy.name }}</strong>
              <span>{{ strategy.code }} · {{ strategy.enabled ? '启用' : '停用' }}</span>
            </button>
          </div>
          <div v-if="selectedCustomStrategy" class="factor-side-actions">
            <div class="factor-side-summary">
              <strong>{{ customStrategyForm.name }}</strong>
              <span>{{ customStrategyForm.code }} · {{ customStrategyForm.enabled ? '启用' : '停用' }}</span>
              <p v-if="customStrategyForm.description">{{ customStrategyForm.description }}</p>
            </div>
            <div class="sync-actions">
              <button class="submit secondary" title="修改信息" @click="openEditCustomStrategyDialog">
                <Edit3 :size="17" />
              </button>
              <button class="submit" title="保存代码" @click="saveCustomStrategy">
                <Save :size="17" />
              </button>
              <button class="submit danger" title="删除策略" @click="removeCustomStrategy">
                <Trash2 :size="17" />
              </button>
            </div>
          </div>
        </aside>

        <section class="main-panel custom-factor-editor">
          <div v-if="selectedCustomStrategy" class="factor-workbench">
            <div class="param-strip">
              <span>策略参数</span>
              <code>{{ customStrategyForm.default_params.replace(/\s+/g, ' ') }}</code>
              <button class="ghost" @click="openStrategyParamDialog">编辑参数</button>
            </div>
            <CodeEditor v-model="customStrategyForm.source_code" language="python" />
            <div class="preview-config compact-preview">
              <label>
                股票池
                <select v-model="strategyPreviewPoolId">
                  <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
                </select>
              </label>
              <label>
                测试股票
                <select v-model="strategyPreviewSymbol">
                  <option v-for="row in strategyPreviewPoolSymbols" :key="row.symbol" :value="row.symbol">
                    {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
                  </option>
                </select>
              </label>
              <label>
                周期
                <select v-model="strategyPreviewPeriod">
                  <option value="1min">1min</option>
                  <option value="5min">5min</option>
                  <option value="15min">15min</option>
                  <option value="30min">30min</option>
                  <option value="60min">60min</option>
                  <option value="day">day</option>
                </select>
              </label>
              <label>
                复权
                <select v-model="strategyPreviewAdjustType">
                  <option value="forward">前复权</option>
                  <option value="no_adjust">不复权</option>
                </select>
              </label>
              <label>
                样本数
                <input v-model.number="strategyPreviewLimit" type="number" min="20" max="5000" />
              </label>
              <button class="submit secondary compact" :disabled="!selectedCustomStrategyId" @click="runCustomStrategyPreview">
                <Play :size="16" />
                <span>试运行</span>
              </button>
            </div>
            <div class="preview-config compact-preview">
              <label>
                初始资金
                <input v-model.number="strategyPreviewInitialCash" type="number" min="1" />
              </label>
              <label>
                手续费率
                <input v-model.number="strategyPreviewFeeRate" type="number" min="0" step="0.0001" />
              </label>
              <label>
                滑点率
                <input v-model.number="strategyPreviewSlippageRate" type="number" min="0" step="0.0001" />
              </label>
            </div>
            <KlineChart
              v-if="strategyPreviewCandles.length"
              :candles="strategyPreviewCandles"
              :factors="[]"
              :selected-factors="[]"
              :factor-series="[]"
              :fit-key="strategyPreviewFitKey"
              :show-vwap="showVwap"
              :show-ma="false"
              :show-ema="false"
              :show-bollinger="false"
              :ma-period="maPeriod"
              :ema-period="emaPeriod"
              :bollinger-period="bollingerPeriod"
              :bollinger-multiplier="bollingerMultiplier"
              :trade-signals="strategyPreviewResult?.signals || []"
              v-model:visible-candle-count="visibleCandleCount"
              @load-older="() => {}"
            />
            <StrategyResultPanel v-if="strategyPreviewResult" :result="strategyPreviewResult" v-model:show-equity="showStrategyPreviewEquity" />
          </div>
          <div v-else class="empty-state">请先在左侧新建或选择一个自定义策略</div>
        </section>
      </section>

      <section v-if="activeTab === 'strategyResearch'" class="research-layout">
        <aside class="panel research-controls">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>策略研究</span>
          </div>
          <label>
            股票池
            <select v-model="selectedPoolId">
              <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
            </select>
          </label>
          <label>
            股票
            <select v-model="researchSymbol">
              <option v-for="row in enabledPoolSymbols" :key="row.symbol" :value="row.symbol">
                {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
              </option>
            </select>
          </label>
          <label>
            周期
            <select v-model="period">
              <option value="1min">1min</option>
              <option value="5min">5min</option>
              <option value="15min">15min</option>
              <option value="30min">30min</option>
              <option value="60min">60min</option>
              <option value="day">day</option>
            </select>
          </label>
          <label>
            复权
            <select v-model="adjustType">
              <option value="forward">前复权</option>
              <option value="no_adjust">不复权</option>
            </select>
          </label>
          <label>
            策略
            <select v-model="strategyResearchStrategyId">
              <option v-for="strategy in enabledCustomStrategies" :key="strategy.id" :value="strategy.id">{{ strategy.name }}</option>
            </select>
          </label>
          <button class="ghost param-button strategy-param-button" type="button" @click="openResearchStrategyParamDialog">策略参数</button>
          <label>
            开始日期
            <input v-model="strategyResearchStart" type="date" />
          </label>
          <label>
            结束日期
            <input v-model="strategyResearchEnd" type="date" />
          </label>
          <label>
            初始资金
            <input v-model.number="strategyInitialCash" type="number" min="1" />
          </label>
          <label>
            手续费率
            <input v-model.number="strategyFeeRate" type="number" min="0" step="0.0001" />
          </label>
          <label>
            滑点率
            <input v-model.number="strategySlippageRate" type="number" min="0" step="0.0001" />
          </label>
          <button class="submit" :disabled="!strategyResearchStrategyId || !researchSymbol" @click="runStrategyResearch">
            <Play :size="17" />
            <span>运行策略</span>
          </button>
        </aside>

        <section class="main-panel research-panel">
          <div class="chart-head">
            <div>
              <h2>{{ selectedResearchStrategy?.name || '请选择策略' }} · {{ researchSymbol || '请选择股票' }}</h2>
              <p>{{ strategyResearchCandles.length }} 根K线 · {{ strategyResearchResult?.signals.length || 0 }} 个信号</p>
            </div>
          </div>
          <KlineChart
            :candles="strategyResearchCandles"
            :factors="[]"
            :selected-factors="[]"
            :factor-series="[]"
            :fit-key="strategyResearchFitKey"
            :show-vwap="showVwap"
            :show-ma="showMa"
            :show-ema="showEma"
            :show-bollinger="showBollinger"
            :ma-period="maPeriod"
            :ema-period="emaPeriod"
            :bollinger-period="bollingerPeriod"
            :bollinger-multiplier="bollingerMultiplier"
            :trade-signals="strategyResearchResult?.signals || []"
            v-model:visible-candle-count="visibleCandleCount"
            @load-older="() => {}"
          />
          <StrategyResultPanel v-if="strategyResearchResult" :result="strategyResearchResult" show-cash-position v-model:show-equity="showStrategyResearchEquity" />
          <div v-if="strategyResearchResult?.trades.length" class="task-table strategy-table">
            <div class="strategy-trade-row header">
              <span>买入时间</span>
              <span>卖出时间</span>
              <span>数量</span>
              <span>买入价</span>
              <span>卖出价</span>
              <span>盈亏</span>
              <span>收益率</span>
            </div>
            <div v-for="trade in strategyResearchResult.trades.slice(-20).reverse()" :key="`${trade.buy_time}-${trade.sell_time}`" class="strategy-trade-row">
              <span>{{ new Date(trade.buy_time * 1000).toLocaleString() }}</span>
              <span>{{ new Date(trade.sell_time * 1000).toLocaleString() }}</span>
              <span>{{ trade.quantity }}</span>
              <span>{{ formatMoney(trade.buy_price) }}</span>
              <span>{{ formatMoney(trade.sell_price) }}</span>
              <span>{{ formatMoney(trade.pnl) }}</span>
              <span>{{ formatPct(trade.return_pct) }}</span>
            </div>
          </div>
        </section>
      </section>

      <div v-if="showNewFactorDialog" class="modal-backdrop" @click.self="closeNewCustomFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>新建自定义因子</span>
          </div>
          <label>
            因子编码
            <input v-model="newFactorDraft.code" placeholder="例如 rsi_factor" @keyup.enter="createCustomFactorFromDialog" />
          </label>
          <label>
            因子名称
            <input v-model="newFactorDraft.name" placeholder="例如 RSI 因子" @keyup.enter="createCustomFactorFromDialog" />
          </label>
          <label>
            描述
            <textarea v-model="newFactorDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewCustomFactorDialog">取消</button>
            <button class="submit compact" @click="createCustomFactorFromDialog">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditFactorDialog" class="modal-backdrop" @click.self="closeEditCustomFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>修改因子信息</span>
          </div>
          <label>
            因子编码
            <input v-model="editFactorDraft.code" placeholder="例如 rsi_factor" />
          </label>
          <label>
            因子名称
            <input v-model="editFactorDraft.name" placeholder="例如 RSI 因子" />
          </label>
          <label>
            描述
            <textarea v-model="editFactorDraft.description" placeholder="可选"></textarea>
          </label>
          <label class="check-row custom-enabled">
            <input v-model="editFactorDraft.enabled" type="checkbox" />
            启用
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditCustomFactorDialog">取消</button>
            <button class="submit compact" @click="saveCustomFactorMeta">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showNewStrategyDialog" class="modal-backdrop" @click.self="closeNewCustomStrategyDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>新建自定义策略</span>
          </div>
          <label>
            策略编码
            <input v-model="newStrategyDraft.code" placeholder="例如 momentum_strategy" @keyup.enter="createCustomStrategyFromDialog" />
          </label>
          <label>
            策略名称
            <input v-model="newStrategyDraft.name" placeholder="例如 动量策略" @keyup.enter="createCustomStrategyFromDialog" />
          </label>
          <label>
            描述
            <textarea v-model="newStrategyDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewCustomStrategyDialog">取消</button>
            <button class="submit compact" @click="createCustomStrategyFromDialog">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditStrategyDialog" class="modal-backdrop" @click.self="closeEditCustomStrategyDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>修改策略信息</span>
          </div>
          <label>
            策略编码
            <input v-model="editStrategyDraft.code" placeholder="例如 momentum_strategy" />
          </label>
          <label>
            策略名称
            <input v-model="editStrategyDraft.name" placeholder="例如 动量策略" />
          </label>
          <label>
            描述
            <textarea v-model="editStrategyDraft.description" placeholder="可选"></textarea>
          </label>
          <label class="check-row custom-enabled">
            <input v-model="editStrategyDraft.enabled" type="checkbox" />
            启用
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditCustomStrategyDialog">取消</button>
            <button class="submit compact" @click="saveCustomStrategyMeta">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showParamDialog" class="modal-backdrop" @click.self="closeParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>编辑因子参数 JSON</span>
          </div>
          <CodeEditor v-model="customFactorForm.default_params" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showStrategyParamDialog" class="modal-backdrop" @click.self="closeStrategyParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>编辑策略参数 JSON</span>
          </div>
          <CodeEditor v-model="customStrategyForm.default_params" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeStrategyParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showResearchStrategyParamDialog" class="modal-backdrop" @click.self="closeResearchStrategyParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>策略研究参数 JSON</span>
          </div>
          <CodeEditor v-model="strategyResearchParams" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeResearchStrategyParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showResearchParamDialog" class="modal-backdrop" @click.self="closeResearchParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>{{ researchParamLabel(editingResearchParamKey) }} 参数 JSON</span>
          </div>
          <CodeEditor v-model="customFactorParamText[editingResearchParamKey]" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeResearchParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="activeParamDialog" class="modal-backdrop" @click.self="closeSimpleParamDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>{{ simpleParamTitle() }}</span>
          </div>
          <label v-if="activeParamDialog === 'ma'">
            周期
            <input v-model.number="maPeriod" type="number" min="1" max="240" />
          </label>
          <label v-if="activeParamDialog === 'ema'">
            周期
            <input v-model.number="emaPeriod" type="number" min="1" max="240" />
          </label>
          <template v-if="activeParamDialog === 'boll'">
            <label>
              周期
              <input v-model.number="bollingerPeriod" type="number" min="1" max="240" />
            </label>
            <label>
              倍数
              <input v-model.number="bollingerMultiplier" type="number" min="0.1" max="10" step="0.1" />
            </label>
          </template>
          <div class="modal-actions">
            <button class="ghost" @click="closeSimpleParamDialog">完成</button>
          </div>
        </section>
      </div>

      <section v-if="activeTab === 'research'" class="research-layout">
      <aside class="panel research-controls">
        <div class="panel-title">
          <BarChart3 :size="17" />
          <span>研究视图</span>
        </div>
        <label>
          股票池
          <select v-model="selectedPoolId">
            <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
          </select>
        </label>
        <label>
          股票
          <select v-model="researchSymbol">
            <option v-for="row in enabledPoolSymbols" :key="row.symbol" :value="row.symbol">
              {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
            </option>
          </select>
        </label>
        <label>
          周期
          <select v-model="period">
            <option value="1min">1min</option>
            <option value="5min">5min</option>
            <option value="15min">15min</option>
            <option value="30min">30min</option>
            <option value="60min">60min</option>
            <option value="day">day</option>
          </select>
        </label>
        <label>
          复权
          <select v-model="adjustType">
            <option value="forward">前复权</option>
            <option value="no_adjust">不复权</option>
          </select>
        </label>
        <div class="factor-picker">
          <div class="factor-config-title">因子指标</div>
          <div v-for="factor in enabledCustomFactors" :key="factor.id" class="factor-option-row">
            <label class="check-row">
              <input v-model="selectedFactors" type="checkbox" :value="customFactorKey(factor.id)" />
              {{ factor.name }}
            </label>
            <button
              v-if="selectedFactors.includes(customFactorKey(factor.id))"
              class="ghost param-button"
              type="button"
              @click="openResearchParamDialog(customFactorKey(factor.id))"
            >
              参数配置
            </button>
          </div>
        </div>
        <button class="submit" @click="loadChart({ resetView: true })">
          <RefreshCw :size="17" />
          <span>刷新图表</span>
        </button>
      </aside>

      <section class="main-panel research-panel">
        <div class="chart-head">
          <div>
            <h2>{{ researchSymbol || '请选择股票' }} · {{ period }}</h2>
            <p>{{ candles.length }} 根K线 · {{ factors.length }} 个因子点</p>
          </div>
        </div>
        <div class="chart-indicator-bar">
          <div class="factor-config-title">K线指标</div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showVwap" type="checkbox" />
              VWAP
            </label>
          </div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showMa" type="checkbox" />
              MA
            </label>
            <button v-if="showMa" class="ghost param-button" type="button" @click="openSimpleParamDialog('ma')">参数配置</button>
          </div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showEma" type="checkbox" />
              EMA
            </label>
            <button v-if="showEma" class="ghost param-button" type="button" @click="openSimpleParamDialog('ema')">参数配置</button>
          </div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showBollinger" type="checkbox" />
              BOLL
            </label>
            <button v-if="showBollinger" class="ghost param-button" type="button" @click="openSimpleParamDialog('boll')">参数配置</button>
          </div>
        </div>
        <KlineChart
          :candles="candles"
          :factors="factors"
          :selected-factors="selectedFactors"
          :factor-series="factorSeriesMeta"
          :fit-key="chartFitKey"
          :show-vwap="showVwap"
          :show-ma="showMa"
          :show-ema="showEma"
          :show-bollinger="showBollinger"
          :ma-period="maPeriod"
          :ema-period="emaPeriod"
          :bollinger-period="bollingerPeriod"
          :bollinger-multiplier="bollingerMultiplier"
          v-model:visible-candle-count="visibleCandleCount"
          @load-older="loadOlderChartData"
        />
      </section>
    </section>
    </section>
  </main>
</template>

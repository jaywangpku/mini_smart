<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { BarChart3, Code2, Database, Edit3, Menu, PanelLeftClose, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import {
  addPoolSymbol,
  createCustomFactor,
  createBatchSyncTask,
  createPool,
  deleteCustomFactor,
  deletePool,
  fetchCandles,
  fetchCustomFactors,
  fetchCustomFactorValues,
  fetchDerivativeFactors,
  fetchPoolSymbols,
  fetchPools,
  fetchSecurityInfo,
  fetchTasks,
  initDb,
  previewCustomFactor,
  removePoolSymbol,
  searchSecurities,
  setPoolSymbolEnabled,
  syncPool,
  syncPoolAllPeriods,
  updateCustomFactor,
  updatePool,
  updatePoolSymbol,
  type Candle,
  type CustomFactor,
  type FactorValuePoint,
  type PoolRow,
  type PoolSymbolRow,
  type SecurityInfo,
  type SecurityRow,
  type SyncTask
} from './api'
import CodeEditor from './components/CodeEditor.vue'
import KlineChart from './components/KlineChart.vue'

type TabName = 'pools' | 'sync' | 'research' | 'customFactors'
type FactorKey = 'first_derivative' | 'second_derivative'
type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }

const tabs: Array<{ id: TabName; label: string; icon: unknown }> = [
  { id: 'pools', label: '股票池管理', icon: Database },
  { id: 'sync', label: '数据同步', icon: Play },
  { id: 'research', label: '因子研究', icon: BarChart3 },
  { id: 'customFactors', label: '自定义因子', icon: Code2 }
]

const factorOptions: Array<{ key: FactorKey; label: string }> = [
  { key: 'first_derivative', label: '一阶导' },
  { key: 'second_derivative', label: '二阶导' }
]

const activeTab = ref<TabName>('pools')
const navCollapsed = ref(false)
const pools = ref<PoolRow[]>([])
const selectedPoolId = ref('default')
const poolSymbols = ref<PoolSymbolRow[]>([])
const customFactors = ref<CustomFactor[]>([])
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
const factorN = ref(5)
const factorM = ref(5)
const selectedFactors = ref<string[]>(['first_derivative', 'second_derivative'])
const selectedCustomFactorId = ref('')
const showNewFactorDialog = ref(false)
const showEditFactorDialog = ref(false)
const showParamDialog = ref(false)
const showResearchParamDialog = ref(false)
const editingResearchParamKey = ref('')
const activeParamDialog = ref<'first' | 'second' | 'ma' | 'ema' | 'boll' | ''>('')
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

function localDateString(date = new Date()) {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const selectedPool = computed(() => pools.value.find((pool) => pool.id === selectedPoolId.value))
const enabledPoolSymbols = computed(() => poolSymbols.value.filter((row) => row.enabled))
const hasRunningTask = computed(() => tasks.value.some((task) => task.status === 'queued' || task.status === 'running'))
const enabledCustomFactors = computed(() => customFactors.value.filter((factor) => factor.enabled))
const selectedCustomFactor = computed(() => customFactors.value.find((factor) => factor.id === selectedCustomFactorId.value))
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
const selectedSystemFactors = computed(() => selectedFactors.value.filter((key): key is FactorKey => key === 'first_derivative' || key === 'second_derivative'))
const factorSeriesMeta = computed(() => {
  const system = factorOptions.map((factor, index) => ({
    key: factor.key,
    label: factor.label,
    color: index === 0 ? '#38bdf8' : '#f97316',
    zeroLine: true
  }))
  const custom = enabledCustomFactors.value.map((factor, index) => ({
    key: customFactorKey(factor.id),
    label: factor.name,
    color: customFactorColor(index),
    zeroLine: true
  }))
  return [...system, ...custom]
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

  if (selectedSystemFactors.value.length) {
    const derivative = await fetchDerivativeFactors(researchSymbol.value, period.value, adjustType.value, factorN.value, factorM.value, limit, range)
    for (const item of derivative) {
      const point = ensurePoint(item.time)
      if (selectedSystemFactors.value.includes('first_derivative')) point.first_derivative = item.first_derivative
      if (selectedSystemFactors.value.includes('second_derivative')) point.second_derivative = item.second_derivative
    }
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
    await Promise.all([loadCustomFactors(), loadTasks()])
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

function defaultFactorSource() {
  return `def compute(candles, params):
    n = int(params.get("n", 5))
    result = []
    for index, row in enumerate(candles):
        if index < n:
            result.append({"time": row["time"], "value": None})
            continue
        previous = candles[index - n]["close"]
        value = (row["close"] - previous) / previous if previous else None
        result.append({"time": row["time"], "value": value})
    return result
`
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

function openSimpleParamDialog(type: 'first' | 'second' | 'ma' | 'ema' | 'boll') {
  activeParamDialog.value = type
}

function closeSimpleParamDialog() {
  activeParamDialog.value = ''
}

function simpleParamTitle() {
  const titles: Record<string, string> = {
    first: '一阶导参数',
    second: '二阶导参数',
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

watch(customPreviewPoolId, async (poolId) => {
  error.value = ''
  try {
    customPreviewPoolSymbols.value = await fetchPoolSymbols(poolId)
    customPreviewSymbol.value = customPreviewPoolSymbols.value[0]?.symbol || ''
  } catch (err) {
    setError(err, '加载测试股票池失败')
  }
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

watch([researchSymbol, period, adjustType, factorN, factorM, selectedFactors, customFactorParamText], () => {
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
    <aside class="side-nav">
      <div class="brand">
        <button class="icon-button" title="收起导航" @click="navCollapsed = !navCollapsed">
          <PanelLeftClose v-if="!navCollapsed" :size="18" />
          <Menu v-else :size="18" />
        </button>
        <div v-if="!navCollapsed">
          <h1>量化研究台</h1>
        </div>
      </div>
      <nav class="side-tabs">
        <button v-for="tab in tabs" :key="tab.id" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
          <component :is="tab.icon" :size="18" />
          <span v-if="!navCollapsed">{{ tab.label }}</span>
        </button>
      </nav>
    </aside>

    <section class="content-shell">
      <div v-if="message || error" :class="['toast', error ? 'error' : 'notice']">
        {{ error || message }}
      </div>

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
          <label v-if="activeParamDialog === 'first'">
            步长
            <input v-model.number="factorN" type="number" min="1" max="240" />
          </label>
          <label v-if="activeParamDialog === 'second'">
            步长
            <input v-model.number="factorM" type="number" min="1" max="240" />
          </label>
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
          <div class="factor-group-title">系统预设</div>
          <div v-for="factor in factorOptions" :key="factor.key" class="factor-option-row">
            <label class="check-row">
              <input v-model="selectedFactors" type="checkbox" :value="factor.key" />
              {{ factor.label }}
            </label>
            <button
              v-if="selectedFactors.includes(factor.key)"
              class="ghost param-button"
              type="button"
              @click="openSimpleParamDialog(factor.key === 'first_derivative' ? 'first' : 'second')"
            >
              参数配置
            </button>
          </div>
          <div class="factor-group-title">自定义因子</div>
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
            <p>{{ candles.length }} 根K线 · {{ factors.length }} 个因子点 · 一阶导步长={{ factorN }} · 二阶导步长={{ factorM }}</p>
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

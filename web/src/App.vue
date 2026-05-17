<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { BarChart3, Database, Menu, PanelLeftClose, Play, Plus, RefreshCw, Save, Trash2 } from 'lucide-vue-next'
import {
  addPoolSymbol,
  createBatchSyncTask,
  createPool,
  deletePool,
  fetchCandles,
  fetchDerivativeFactors,
  fetchPoolSymbols,
  fetchPools,
  fetchTasks,
  initDb,
  removePoolSymbol,
  setPoolSymbolEnabled,
  syncPool,
  updatePool,
  updatePoolSymbol,
  type Candle,
  type DerivativeFactorPoint,
  type PoolRow,
  type PoolSymbolRow,
  type SyncTask
} from './api'
import KlineChart from './components/KlineChart.vue'

type TabName = 'pools' | 'sync' | 'research'
type FactorKey = 'first_derivative' | 'second_derivative'

const tabs: Array<{ id: TabName; label: string; icon: unknown }> = [
  { id: 'pools', label: '股票池管理', icon: Database },
  { id: 'sync', label: '数据同步', icon: Play },
  { id: 'research', label: 'K线与因子研究', icon: BarChart3 }
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
const tasks = ref<SyncTask[]>([])
const candles = ref<Candle[]>([])
const factors = ref<DerivativeFactorPoint[]>([])
const selectedSymbols = ref<string[]>([])
const researchSymbol = ref('')
const newPoolName = ref('')
const newPoolDescription = ref('')
const newSymbol = ref('MSTU.US')
const newSymbolName = ref('')
const editPoolName = ref('')
const editPoolDescription = ref('')
const period = ref('1min')
const adjustType = ref('forward')
const start = ref('2025-01-01')
const end = ref(localDateString())
const factorN = ref(5)
const factorM = ref(5)
const selectedFactors = ref<FactorKey[]>(['first_derivative', 'second_derivative'])
const showVwap = ref(true)
const showMa = ref(false)
const showEma = ref(false)
const showBollinger = ref(false)
const maPeriod = ref(20)
const emaPeriod = ref(20)
const bollingerPeriod = ref(20)
const bollingerMultiplier = ref(2)
const chartFitKey = ref(0)
const loadingOlder = ref(false)
const reachedHistoryStart = ref(false)
const loading = ref(false)
const message = ref('')
const error = ref('')
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

function setError(err: unknown, fallback: string) {
  error.value = err instanceof Error ? err.message : fallback
}

async function loadPools() {
  pools.value = await fetchPools()
  if (!pools.value.some((pool) => pool.id === selectedPoolId.value)) {
    selectedPoolId.value = pools.value[0]?.id || 'default'
  }
  syncPoolEditForm()
}

async function loadPoolSymbols() {
  if (!selectedPoolId.value) return
  poolSymbols.value = await fetchPoolSymbols(selectedPoolId.value)
  selectedSymbols.value = selectedSymbols.value.filter((symbol) => poolSymbols.value.some((row) => row.symbol === symbol))
  if (!researchSymbol.value && enabledPoolSymbols.value.length) {
    researchSymbol.value = enabledPoolSymbols.value[0].symbol
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

async function loadChart() {
  if (!researchSymbol.value) {
    candles.value = []
    factors.value = []
    reachedHistoryStart.value = false
    return
  }
  const limit = chartLimitForPeriod(period.value)
  const [nextCandles, nextFactors] = await Promise.all([
    fetchCandles(researchSymbol.value, period.value, adjustType.value, limit),
    fetchDerivativeFactors(researchSymbol.value, period.value, adjustType.value, factorN.value, factorM.value, limit)
  ])
  candles.value = nextCandles
  factors.value = nextFactors
  reachedHistoryStart.value = false
  chartFitKey.value += 1
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
      fetchDerivativeFactors(researchSymbol.value, period.value, adjustType.value, factorN.value, factorM.value, 1200, range)
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

async function bootstrap() {
  loading.value = true
  error.value = ''
  try {
    await initDb()
    await loadPools()
    await loadPoolSymbols()
    await Promise.all([loadTasks(), loadChart()])
  } catch (err) {
    setError(err, '初始化失败')
  } finally {
    loading.value = false
  }
}

async function handleCreatePool() {
  const name = newPoolName.value.trim()
  if (!name) return
  error.value = ''
  try {
    const pool = await createPool(name, newPoolDescription.value.trim() || undefined)
    newPoolName.value = ''
    newPoolDescription.value = ''
    selectedPoolId.value = pool.id
    await loadPools()
    await loadPoolSymbols()
  } catch (err) {
    setError(err, '创建股票池失败')
  }
}

function syncPoolEditForm() {
  editPoolName.value = selectedPool.value?.name || ''
  editPoolDescription.value = selectedPool.value?.description || ''
}

async function handleUpdatePool() {
  if (!selectedPoolId.value) return
  const name = editPoolName.value.trim()
  if (!name) return
  error.value = ''
  try {
    await updatePool(selectedPoolId.value, {
      name,
      description: editPoolDescription.value.trim() || undefined
    })
    message.value = '股票池已更新'
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
    message.value = '股票池已删除'
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
      start: start.value || undefined,
      end: end.value || undefined
    })
    message.value = `已提交 ${response.tasks.length} 个同步任务`
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
    const response = await syncPool(selectedPoolId.value, {
      period: period.value,
      adjust_type: adjustType.value,
      start: start.value || undefined,
      end: end.value || undefined
    })
    message.value = `股票池全量同步已提交：${response.tasks.length} 个任务`
    await loadTasks()
  } catch (err) {
    setError(err, '股票池同步失败')
  } finally {
    loading.value = false
  }
}

watch(selectedPoolId, async () => {
  syncPoolEditForm()
  await loadPoolSymbols()
  if (!enabledPoolSymbols.value.some((row) => row.symbol === researchSymbol.value)) {
    researchSymbol.value = enabledPoolSymbols.value[0]?.symbol || ''
  }
  await loadChart()
})

watch([researchSymbol, period, adjustType, factorN, factorM], () => {
  loadChart().catch((err) => setError(err, '加载图表失败'))
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
      <button class="ghost refresh-nav" @click="bootstrap">
        <RefreshCw :size="17" />
        <span v-if="!navCollapsed">刷新</span>
      </button>
    </aside>

    <section class="content-shell">
      <p v-if="message" class="notice global">{{ message }}</p>
      <p v-if="error" class="error global">{{ error }}</p>

      <section v-if="activeTab === 'pools'" class="tab-grid">
      <aside class="panel">
        <div class="panel-title">
          <Database :size="17" />
          <span>股票池</span>
        </div>
        <label>
          当前股票池
          <select v-model="selectedPoolId">
            <option v-for="pool in pools" :key="pool.id" :value="pool.id">
              {{ pool.name }}（{{ pool.symbol_count || 0 }}）
            </option>
          </select>
        </label>
        <label>
          股票池名称
          <input v-model="editPoolName" placeholder="股票池名称" @keyup.enter="handleUpdatePool" />
        </label>
        <label>
          股票池描述
          <input v-model="editPoolDescription" placeholder="可选" @keyup.enter="handleUpdatePool" />
        </label>
        <div class="sync-actions">
          <button class="submit secondary" @click="handleUpdatePool">
            <Save :size="17" />
            <span>保存股票池</span>
          </button>
          <button class="submit danger" :disabled="selectedPoolId === 'default'" @click="handleDeletePool">
            <Trash2 :size="17" />
            <span>删除股票池</span>
          </button>
        </div>
        <label>
          新股票池
          <input v-model="newPoolName" placeholder="例如：杠杆ETF研究池" @keyup.enter="handleCreatePool" />
        </label>
        <label>
          描述
          <input v-model="newPoolDescription" placeholder="可选" @keyup.enter="handleCreatePool" />
        </label>
        <button class="submit" @click="handleCreatePool">
          <Plus :size="17" />
          <span>创建股票池</span>
        </button>
      </aside>

      <section class="main-panel">
        <div class="chart-head">
          <div>
            <h2>{{ selectedPool?.name || '股票池' }}</h2>
            <p>{{ poolSymbols.length }} 只股票，{{ enabledPoolSymbols.length }} 只启用</p>
          </div>
          <div class="add-symbol-row">
            <input v-model="newSymbol" placeholder="MSTU.US" @keyup.enter="handleAddPoolSymbol" />
            <input v-model="newSymbolName" placeholder="股票名称，例如 MicroStrategy" @keyup.enter="handleAddPoolSymbol" />
            <button class="icon-button primary" title="加入股票池" @click="handleAddPoolSymbol">
              <Plus :size="18" />
            </button>
          </div>
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
          开始日期
          <input v-model="start" type="date" />
        </label>
        <label>
          结束日期
          <input v-model="end" type="date" />
        </label>
        <div class="sync-actions">
          <button class="submit" :disabled="loading || !selectedSymbols.length" @click="submitSelectedSync">
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
          <div v-for="factor in factorOptions" :key="factor.key" class="factor-option-row">
            <label class="check-row">
              <input v-model="selectedFactors" type="checkbox" :value="factor.key" />
              {{ factor.label }}
            </label>
            <details v-if="selectedFactors.includes(factor.key)" class="param-disclosure">
              <summary>参数配置</summary>
              <label v-if="factor.key === 'first_derivative'" class="inline-param">
                步长
                <input v-model.number="factorN" type="number" min="1" max="240" />
              </label>
              <label v-else class="inline-param">
                步长
                <input v-model.number="factorM" type="number" min="1" max="240" />
              </label>
            </details>
          </div>
        </div>
        <button class="submit" @click="loadChart">
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
            <details v-if="showMa" class="param-disclosure">
              <summary>参数配置</summary>
              <label class="inline-param">
                周期
                <input v-model.number="maPeriod" type="number" min="1" max="240" />
              </label>
            </details>
          </div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showEma" type="checkbox" />
              EMA
            </label>
            <details v-if="showEma" class="param-disclosure">
              <summary>参数配置</summary>
              <label class="inline-param">
                周期
                <input v-model.number="emaPeriod" type="number" min="1" max="240" />
              </label>
            </details>
          </div>
          <div class="indicator-option-row">
            <label class="check-row">
              <input v-model="showBollinger" type="checkbox" />
              BOLL
            </label>
            <details v-if="showBollinger" class="param-disclosure bollinger-disclosure">
              <summary>参数配置</summary>
              <label class="inline-param">
                周期
                <input v-model.number="bollingerPeriod" type="number" min="1" max="240" />
              </label>
              <label class="inline-param">
                倍数
                <input v-model.number="bollingerMultiplier" type="number" min="0.1" max="10" step="0.1" />
              </label>
            </details>
          </div>
        </div>
        <KlineChart
          :candles="candles"
          :factors="factors"
          :selected-factors="selectedFactors"
          :fit-key="chartFitKey"
          :show-vwap="showVwap"
          :show-ma="showMa"
          :show-ema="showEma"
          :show-bollinger="showBollinger"
          :ma-period="maPeriod"
          :ema-period="emaPeriod"
          :bollinger-period="bollingerPeriod"
          :bollinger-multiplier="bollingerMultiplier"
          @load-older="loadOlderChartData"
        />
      </section>
    </section>
    </section>
  </main>
</template>

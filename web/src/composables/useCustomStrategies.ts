import { computed, ref, watch, type Ref } from 'vue'
import {
  createCustomStrategy,
  deleteCustomStrategy,
  fetchCandles,
  fetchCustomStrategies,
  fetchPoolSymbols,
  runCustomStrategy,
  updateCustomStrategy,
  type Candle,
  type PoolSymbolRow,
  type StrategyRunResult
} from '../api'
import { chartLimitForPeriod, parseJsonObject, prettyJson } from '../appHelpers'
import { defaultStrategySource } from '../defaultSources'
import { dateRange } from '../utils'

type ToastType = (text: string, type?: 'success' | 'error') => void
type ErrorHandler = (err: unknown, fallback: string) => void

export function useCustomStrategies(options: {
  researchSymbol: Ref<string>
  period: Ref<string>
  adjustType: Ref<string>
  strategyInitialCash: Ref<number>
  strategyFeeRate: Ref<number>
  strategySlippageRate: Ref<number>
  showToast: ToastType
  setError: ErrorHandler
}) {
  const customStrategies = ref<Awaited<ReturnType<typeof fetchCustomStrategies>>>([])
  const selectedCustomStrategyId = ref('')
  const showNewStrategyDialog = ref(false)
  const showEditStrategyDialog = ref(false)
  const showStrategyParamDialog = ref(false)
  const showResearchStrategyParamDialog = ref(false)
  const showRealtimeStrategyParamDialog = ref(false)
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
  const realtimeStrategyId = ref('')
  const realtimeStrategyParams = ref('{}')
  const strategyResearchStart = ref('')
  const strategyResearchEnd = ref('')

  const enabledCustomStrategies = computed(() => customStrategies.value.filter((strategy) => strategy.enabled))
  const selectedCustomStrategy = computed(() => customStrategies.value.find((strategy) => strategy.id === selectedCustomStrategyId.value))
  const selectedResearchStrategy = computed(() => customStrategies.value.find((strategy) => strategy.id === strategyResearchStrategyId.value))
  const selectedRealtimeStrategy = computed(() => customStrategies.value.find((strategy) => strategy.id === realtimeStrategyId.value))

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
    if (!realtimeStrategyId.value && enabledCustomStrategies.value.length) {
      const strategy = enabledCustomStrategies.value[0]
      realtimeStrategyId.value = strategy.id
      realtimeStrategyParams.value = prettyJson(strategy.default_params)
    }
  }

  function selectCustomStrategy(strategy: typeof customStrategies.value[number]) {
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

  function openRealtimeStrategyParamDialog() {
    showRealtimeStrategyParamDialog.value = true
  }

  function closeRealtimeStrategyParamDialog() {
    showRealtimeStrategyParamDialog.value = false
  }

  async function createCustomStrategyFromDialog() {
    const code = newStrategyDraft.value.code.trim()
    const name = newStrategyDraft.value.name.trim()
    if (!code || !name) {
      options.showToast('请填写策略编码和策略名称', 'error')
      return
    }
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
      options.showToast('自定义策略已创建')
      await loadCustomStrategies()
      selectCustomStrategy(saved)
    } catch (err) {
      options.setError(err, '创建自定义策略失败')
    }
  }

  async function saveCustomStrategy() {
    if (!selectedCustomStrategyId.value) return
    try {
      const saved = await updateCustomStrategy(selectedCustomStrategyId.value, {
        code: customStrategyForm.value.code.trim(),
        name: customStrategyForm.value.name.trim(),
        description: customStrategyForm.value.description.trim() || undefined,
        source_code: customStrategyForm.value.source_code,
        default_params: parseJsonObject(customStrategyForm.value.default_params),
        enabled: customStrategyForm.value.enabled
      })
      options.showToast('自定义策略已保存')
      await loadCustomStrategies()
      selectCustomStrategy(saved)
    } catch (err) {
      options.setError(err, '保存自定义策略失败')
    }
  }

  async function saveCustomStrategyMeta() {
    if (!selectedCustomStrategyId.value) return
    try {
      const saved = await updateCustomStrategy(selectedCustomStrategyId.value, {
        code: editStrategyDraft.value.code.trim(),
        name: editStrategyDraft.value.name.trim(),
        description: editStrategyDraft.value.description.trim() || undefined,
        enabled: editStrategyDraft.value.enabled
      })
      showEditStrategyDialog.value = false
      options.showToast('策略信息已更新')
      await loadCustomStrategies()
      selectCustomStrategy(saved)
    } catch (err) {
      options.setError(err, '修改自定义策略失败')
    }
  }

  async function removeCustomStrategy() {
    if (!selectedCustomStrategyId.value) return
    if (!window.confirm(`确认删除自定义策略「${customStrategyForm.value.name}」？`)) return
    try {
      await deleteCustomStrategy(selectedCustomStrategyId.value)
      resetCustomStrategyForm()
      await loadCustomStrategies()
    } catch (err) {
      options.setError(err, '删除自定义策略失败')
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
      options.setError(err, '试运行自定义策略失败')
    }
  }

  async function runStrategyResearch() {
    if (!strategyResearchStrategyId.value || !options.researchSymbol.value) return
    try {
      const limit = chartLimitForPeriod(options.period.value)
      const range = dateRange(strategyResearchStart.value, strategyResearchEnd.value)
      const [nextCandles, result] = await Promise.all([
        fetchCandles(options.researchSymbol.value, options.period.value, options.adjustType.value, limit, range),
        runCustomStrategy(
          strategyResearchStrategyId.value,
          strategyRunPayload(
            options.researchSymbol.value,
            options.period.value,
            options.adjustType.value,
            limit,
            parseJsonObject(strategyResearchParams.value),
            options.strategyInitialCash.value,
            options.strategyFeeRate.value,
            options.strategySlippageRate.value,
            range
          )
        )
      ])
      strategyResearchCandles.value = nextCandles
      strategyResearchResult.value = result
      showStrategyResearchEquity.value = false
      strategyResearchFitKey.value += 1
    } catch (err) {
      options.setError(err, '运行策略失败')
    }
  }

  watch(strategyPreviewPoolId, async (poolId) => {
    try {
      strategyPreviewPoolSymbols.value = await fetchPoolSymbols(poolId)
      strategyPreviewSymbol.value = strategyPreviewPoolSymbols.value[0]?.symbol || ''
    } catch (err) {
      options.setError(err, '加载策略测试股票池失败')
    }
  })

  watch(strategyResearchStrategyId, (strategyId) => {
    const strategy = customStrategies.value.find((item) => item.id === strategyId)
    if (strategy) strategyResearchParams.value = prettyJson(strategy.default_params)
  })

  watch(realtimeStrategyId, (strategyId) => {
    const strategy = customStrategies.value.find((item) => item.id === strategyId)
    realtimeStrategyParams.value = strategy ? prettyJson(strategy.default_params) : '{}'
  })

  return {
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
    runStrategyResearch
  }
}

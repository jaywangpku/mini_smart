import { computed, ref, type Ref } from 'vue'
import {
  createCustomFactor,
  deleteCustomFactor,
  fetchCandles,
  fetchCustomFactors,
  previewCustomFactor,
  updateCustomFactor,
  type Candle,
  type FactorValuePoint,
  type PoolSymbolRow
} from '../api'
import { customFactorColor, customFactorKey, parseJsonObject, prettyJson } from '../appHelpers'
import { defaultFactorSource } from '../defaultSources'

type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }
export type FactorDisplayMode = 'raw' | 'zero_center' | 'percent' | 'log10' | 'symlog'
type ToastType = (text: string, type?: 'success' | 'error') => void
type ErrorHandler = (err: unknown, fallback: string) => void

export function useCustomFactors(options: {
  selectedFactors: Ref<string[]>
  showToast: ToastType
  setError: ErrorHandler
}) {
  const customFactors = ref<Awaited<ReturnType<typeof fetchCustomFactors>>>([])
  const selectedCustomFactorId = ref('')
  const showNewFactorDialog = ref(false)
  const showEditFactorDialog = ref(false)
  const showParamDialog = ref(false)
  const showResearchParamDialog = ref(false)
  const showRealtimeFactorDialog = ref(false)
  const showResearchFactorDialog = ref(false)
  const editingResearchParamKey = ref('')
  const newFactorDraft = ref({ code: '', name: '', description: '' })
  const editFactorDraft = ref({ code: '', name: '', description: '', enabled: true })
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
  const customFactorDisplayMode = ref<Record<string, FactorDisplayMode>>({})

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
  const selectedCustomFactors = computed(() => options.selectedFactors.value.filter((key) => key.startsWith('custom:')))
  const factorSeriesMeta = computed(() => enabledCustomFactors.value.map((factor, index) => ({
    key: customFactorKey(factor.id),
    label: factor.name,
    color: customFactorColor(index),
    zeroLine: true,
    displayMode: customFactorDisplayMode.value[customFactorKey(factor.id)] || 'raw'
  })))

  async function loadCustomFactors() {
    customFactors.value = await fetchCustomFactors()
    if (!selectedCustomFactorId.value && customFactors.value.length) {
      selectCustomFactor(customFactors.value[0])
    }
    for (const factor of customFactors.value) {
      const key = customFactorKey(factor.id)
      if (!customFactorParamText.value[key]) customFactorParamText.value[key] = prettyJson(factor.default_params)
      if (!customFactorDisplayMode.value[key]) customFactorDisplayMode.value[key] = 'raw'
    }
  }

  function selectCustomFactor(factor: typeof customFactors.value[number]) {
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

  function openNewCustomFactorDialog() {
    newFactorDraft.value = { code: '', name: '', description: '' }
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

  function openRealtimeFactorDialog() {
    showRealtimeFactorDialog.value = true
  }

  function closeRealtimeFactorDialog() {
    showRealtimeFactorDialog.value = false
  }

  function openResearchFactorDialog() {
    showResearchFactorDialog.value = true
  }

  function closeResearchFactorDialog() {
    showResearchFactorDialog.value = false
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
      options.showToast('请填写因子编码和因子名称', 'error')
      return
    }
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
      options.showToast('自定义因子已创建')
      await loadCustomFactors()
      selectCustomFactor(saved)
    } catch (err) {
      options.setError(err, '创建自定义因子失败')
    }
  }

  async function saveCustomFactor() {
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
      options.showToast('自定义因子已保存')
      await loadCustomFactors()
      selectCustomFactor(saved)
    } catch (err) {
      options.setError(err, '保存自定义因子失败')
    }
  }

  async function saveCustomFactorMeta() {
    if (!selectedCustomFactorId.value) return
    try {
      const saved = await updateCustomFactor(selectedCustomFactorId.value, {
        code: editFactorDraft.value.code.trim(),
        name: editFactorDraft.value.name.trim(),
        description: editFactorDraft.value.description.trim() || undefined,
        enabled: editFactorDraft.value.enabled
      })
      options.showToast('因子信息已更新')
      showEditFactorDialog.value = false
      await loadCustomFactors()
      selectCustomFactor(saved)
    } catch (err) {
      options.setError(err, '修改自定义因子失败')
    }
  }

  async function removeCustomFactor() {
    if (!selectedCustomFactorId.value) return
    if (!window.confirm(`确认删除自定义因子「${customFactorForm.value.name}」？`)) return
    try {
      await deleteCustomFactor(selectedCustomFactorId.value)
      options.selectedFactors.value = options.selectedFactors.value.filter((key) => key !== customFactorKey(selectedCustomFactorId.value))
      resetCustomFactorForm()
      await loadCustomFactors()
    } catch (err) {
      options.setError(err, '删除自定义因子失败')
    }
  }

  async function runCustomFactorPreview() {
    if (!selectedCustomFactorId.value || !customPreviewSymbol.value) return
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
      options.setError(err, '试运行自定义因子失败')
    }
  }

  function researchParamLabel(key: string) {
    return factorSeriesMeta.value.find((item) => item.key === key)?.label || '自定义因子'
  }

  function factorDisplayModeLabel(mode: FactorDisplayMode) {
    const labels: Record<FactorDisplayMode, string> = {
      raw: '原始值',
      zero_center: '零轴居中',
      percent: '百分比',
      log10: 'log10',
      symlog: '对称log'
    }
    return labels[mode] || '原始值'
  }

  return {
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
  }
}

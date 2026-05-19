import { computed, ref, type Ref } from 'vue'
import {
  addPoolSymbol,
  createPool,
  deletePool,
  fetchPoolSymbols,
  fetchPools,
  fetchSecurityInfo,
  removePoolSymbol,
  searchSecurities,
  setPoolSymbolEnabled,
  updatePool,
  updatePoolSymbol,
  type PoolSymbolRow,
  type SecurityInfo,
  type SecurityRow
} from '../api'

type ToastType = (text: string, type?: 'success' | 'error') => void
type ErrorHandler = (err: unknown, fallback: string) => void

export function usePools(options: {
  customPreviewPoolId: Ref<string>
  customPreviewSymbol: Ref<string>
  customPreviewPoolSymbols: Ref<PoolSymbolRow[]>
  strategyPreviewPoolId: Ref<string>
  strategyPreviewSymbol: Ref<string>
  strategyPreviewPoolSymbols: Ref<PoolSymbolRow[]>
  selectedSymbols: Ref<string[]>
  researchSymbol: Ref<string>
  showToast: ToastType
  setError: ErrorHandler
}) {
  const pools = ref<Awaited<ReturnType<typeof fetchPools>>>([])
  const selectedPoolId = ref('default')
  const poolSymbols = ref<PoolSymbolRow[]>([])
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

  const selectedPool = computed(() => pools.value.find((pool) => pool.id === selectedPoolId.value))
  const enabledPoolSymbols = computed(() => poolSymbols.value.filter((row) => row.enabled))

  async function loadPools() {
    pools.value = await fetchPools()
    if (!pools.value.some((pool) => pool.id === selectedPoolId.value)) {
      selectedPoolId.value = pools.value[0]?.id || 'default'
    }
    if (!pools.value.some((pool) => pool.id === options.customPreviewPoolId.value)) {
      options.customPreviewPoolId.value = selectedPoolId.value
    }
  }

  async function loadPoolSymbols() {
    if (!selectedPoolId.value) return
    poolSymbols.value = await fetchPoolSymbols(selectedPoolId.value)
    options.selectedSymbols.value = options.selectedSymbols.value.filter((symbol) => poolSymbols.value.some((row) => row.symbol === symbol))
    if (!options.researchSymbol.value && enabledPoolSymbols.value.length) {
      options.researchSymbol.value = enabledPoolSymbols.value[0].symbol
    }
    if (!options.customPreviewSymbol.value && enabledPoolSymbols.value.length) {
      options.customPreviewSymbol.value = enabledPoolSymbols.value[0].symbol
    }
    if (options.customPreviewPoolId.value === selectedPoolId.value) {
      options.customPreviewPoolSymbols.value = poolSymbols.value
    }
    if (options.strategyPreviewPoolId.value === selectedPoolId.value) {
      options.strategyPreviewPoolSymbols.value = poolSymbols.value
    }
    if (!options.strategyPreviewSymbol.value && enabledPoolSymbols.value.length) {
      options.strategyPreviewSymbol.value = enabledPoolSymbols.value[0].symbol
    }
  }

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
      options.showToast('请填写股票池名称', 'error')
      return
    }
    try {
      const pool = await createPool(name, newPoolDraft.value.description.trim() || undefined)
      showNewPoolDialog.value = false
      options.showToast('股票池已创建')
      selectedPoolId.value = pool.id
      await loadPools()
      await loadPoolSymbols()
    } catch (err) {
      options.setError(err, '创建股票池失败')
    }
  }

  async function handleUpdatePool() {
    if (!selectedPoolId.value) return
    const name = editPoolDraft.value.name.trim()
    if (!name) {
      options.showToast('请填写股票池名称', 'error')
      return
    }
    try {
      await updatePool(selectedPoolId.value, {
        name,
        description: editPoolDraft.value.description.trim() || undefined
      })
      showEditPoolDialog.value = false
      options.showToast('股票池已更新')
      await loadPools()
    } catch (err) {
      options.setError(err, '更新股票池失败')
    }
  }

  async function handleDeletePool() {
    if (!selectedPoolId.value || selectedPoolId.value === 'default') return
    if (!window.confirm(`确认删除股票池「${selectedPool.value?.name || selectedPoolId.value}」？`)) return
    try {
      await deletePool(selectedPoolId.value)
      options.showToast('股票池已删除')
      selectedPoolId.value = 'default'
      await loadPools()
      await loadPoolSymbols()
    } catch (err) {
      options.setError(err, '删除股票池失败')
    }
  }

  async function handleAddPoolSymbol() {
    const symbol = newSymbol.value.trim().toUpperCase()
    if (!symbol) return
    try {
      await addPoolSymbol(selectedPoolId.value, symbol, undefined, newSymbolName.value.trim() || undefined)
      newSymbol.value = ''
      newSymbolName.value = ''
      await Promise.all([loadPools(), loadPoolSymbols()])
    } catch (err) {
      options.setError(err, '添加股票失败')
    }
  }

  async function handleSearchSecurities() {
    searchingSecurities.value = true
    try {
      securityResults.value = await searchSecurities(securityMarket.value, securityQuery.value.trim(), 50)
      selectedSecurity.value = null
      if (!securityResults.value.length) options.showToast('没有找到匹配股票')
    } catch (err) {
      options.setError(err, '查询可添加股票失败')
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
    try {
      selectedSecurity.value = await fetchSecurityInfo(row.symbol)
    } catch (err) {
      options.setError(err, '查询股票基本信息失败')
    }
  }

  async function addSelectedSecurity() {
    if (!selectedSecurity.value) return
    try {
      await addPoolSymbol(
        selectedPoolId.value,
        selectedSecurity.value.symbol,
        undefined,
        selectedSecurity.value.name || selectedSecurity.value.name_cn || selectedSecurity.value.name_hk || selectedSecurity.value.name_en || undefined
      )
      options.showToast(`${selectedSecurity.value.symbol} 已加入股票池`)
      await Promise.all([loadPools(), loadPoolSymbols()])
    } catch (err) {
      options.setError(err, '添加股票失败')
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

  function symbolLabel(row: PoolSymbolRow) {
    return row.name?.trim() || row.symbol
  }

  return {
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
  }
}

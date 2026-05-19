import { ref, type Ref } from 'vue'
import { fetchCandles, fetchCustomFactorValues, type Candle } from '../api'
import { chartLimitForPeriod, customFactorIdFromKey, mergeByTime, parseJsonObject } from '../appHelpers'
import { dateRange } from '../utils'

type ChartFactorPoint = { time: number; [key: string]: number | null | undefined }
type ErrorHandler = (err: unknown, fallback: string) => void

export function useResearchCharts(options: {
  researchSymbol: Ref<string>
  period: Ref<string>
  adjustType: Ref<string>
  researchStart: Ref<string>
  researchEnd: Ref<string>
  selectedCustomFactors: Ref<string[]>
  customFactorParamText: Ref<Record<string, string>>
  strategyResearchCandles: Ref<Candle[]>
  strategyResearchStart: Ref<string>
  strategyResearchEnd: Ref<string>
  error: Ref<string>
  setError: ErrorHandler
}) {
  const candles = ref<Candle[]>([])
  const historyCandles = ref<Candle[]>([])
  const historyFitKey = ref(0)
  const factors = ref<ChartFactorPoint[]>([])
  const strategyResearchFactors = ref<ChartFactorPoint[]>([])
  const chartFitKey = ref(0)
  const loadingOlder = ref(false)
  const reachedHistoryStart = ref(false)
  const loadingOlderHistory = ref(false)
  const reachedHistoryStartForHistory = ref(false)

  async function loadChart(loadOptions: { resetView?: boolean } = {}) {
    if (!options.researchSymbol.value) {
      candles.value = []
      factors.value = []
      reachedHistoryStart.value = false
      return
    }
    const limit = chartLimitForPeriod(options.period.value)
    const range = dateRange(options.researchStart.value, options.researchEnd.value)
    const nextCandles = await fetchCandles(options.researchSymbol.value, options.period.value, options.adjustType.value, limit, range)
    const nextFactors = await loadFactorValues(limit, range)
    candles.value = nextCandles
    factors.value = nextFactors
    reachedHistoryStart.value = false
    if (loadOptions.resetView) chartFitKey.value += 1
  }

  async function loadHistoryChart(loadOptions: { resetView?: boolean } = {}) {
    if (!options.researchSymbol.value) {
      historyCandles.value = []
      reachedHistoryStartForHistory.value = false
      return
    }
    historyCandles.value = await fetchCandles(
      options.researchSymbol.value,
      options.period.value,
      options.adjustType.value,
      chartLimitForPeriod(options.period.value),
      dateRange(options.researchStart.value, options.researchEnd.value)
    )
    reachedHistoryStartForHistory.value = false
    if (loadOptions.resetView) historyFitKey.value += 1
  }

  async function loadOlderChartData() {
    if (loadingOlder.value || reachedHistoryStart.value || !options.researchSymbol.value || !candles.value.length) return
    loadingOlder.value = true
    options.error.value = ''
    try {
      const endTime = candles.value[0].time - 1
      const baseRange = dateRange(options.researchStart.value, options.researchEnd.value)
      const range = { ...baseRange, end: Math.min(baseRange.end ?? endTime, endTime) }
      const [olderCandles, olderFactors] = await Promise.all([
        fetchCandles(options.researchSymbol.value, options.period.value, options.adjustType.value, 1200, range),
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
      options.setError(err, '加载历史K线失败')
    } finally {
      loadingOlder.value = false
    }
  }

  async function loadOlderHistoryChartData() {
    if (loadingOlderHistory.value || reachedHistoryStartForHistory.value || !options.researchSymbol.value || !historyCandles.value.length) return
    loadingOlderHistory.value = true
    options.error.value = ''
    try {
      const endTime = historyCandles.value[0].time - 1
      const limit = chartLimitForPeriod(options.period.value)
      const baseRange = dateRange(options.researchStart.value, options.researchEnd.value)
      const range = { ...baseRange, end: Math.min(baseRange.end ?? endTime, endTime) }
      const olderCandles = await fetchCandles(options.researchSymbol.value, options.period.value, options.adjustType.value, limit, range)

      if (!olderCandles.length) {
        reachedHistoryStartForHistory.value = true
        return
      }

      historyCandles.value = mergeByTime(historyCandles.value, olderCandles)
      if (olderCandles.length < limit) reachedHistoryStartForHistory.value = true
    } catch (err) {
      options.setError(err, '加载历史看板K线失败')
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
      options.selectedCustomFactors.value.map(async (key) => {
        const id = customFactorIdFromKey(key)
        const rows = await fetchCustomFactorValues(
          id,
          options.researchSymbol.value,
          options.period.value,
          options.adjustType.value,
          parseJsonObject(options.customFactorParamText.value[key] || '{}'),
          limit,
          range
        )
        for (const row of rows) ensurePoint(row.time)[key] = row.value ?? null
      })
    )

    return [...byTime.values()].sort((a, b) => a.time - b.time)
  }

  async function loadStrategyResearchFactors() {
    if (!options.strategyResearchCandles.value.length) {
      strategyResearchFactors.value = []
      return
    }
    strategyResearchFactors.value = await loadFactorValues(
      options.strategyResearchCandles.value.length,
      dateRange(options.strategyResearchStart.value, options.strategyResearchEnd.value)
    )
  }

  return {
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
  }
}

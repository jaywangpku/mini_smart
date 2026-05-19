<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { LineStyle, createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from 'lightweight-charts'
import type { Candle } from '../api'

type FactorPoint = { time: number; [key: string]: number | null | undefined }
type FactorDisplayMode = 'raw' | 'zero_center' | 'percent' | 'log10' | 'symlog'
type FactorSeriesMeta = { key: string; label: string; color: string; zeroLine?: boolean; displayMode?: FactorDisplayMode }
export type TradeSignal = {
  time: number
  action: 'buy' | 'sell'
  quantity: number
  price?: number | null
  executed_quantity?: number | null
  reason?: string
}

const props = defineProps<{
  candles: Candle[]
  factors: FactorPoint[]
  selectedFactors: string[]
  factorSeries: FactorSeriesMeta[]
  fitKey: number
  showVwap: boolean
  showMa: boolean
  showEma: boolean
  showBollinger: boolean
  maPeriod: number
  emaPeriod: number
  bollingerPeriod: number
  bollingerMultiplier: number
  visibleCandleCount: number
  tradeSignals?: TradeSignal[]
  showTodayButton?: boolean
  rangeButtons?: boolean
  lockTodayRange?: boolean
}>()

const emit = defineEmits<{
  loadOlder: []
  'update:visibleCandleCount': [value: number]
}>()

const chartTheme = {
  background: '#0f172a',
  text: '#cbd5e1',
  grid: '#1e293b',
  border: '#334155',
  zero: '#fb7185'
}

const candleHost = ref<HTMLDivElement | null>(null)
const factorHosts = new Map<string, HTMLDivElement>()
const hoverTime = ref<number | null>(null)
const sizeStep = ref(20)
const moveStep = ref(40)
const selectedSessionCount = ref(1)
let candleChart: IChartApi | undefined
let candleSeries: ISeriesApi<'Candlestick'> | undefined
let vwapSeries: ISeriesApi<'Line'> | undefined
let maSeries: ISeriesApi<'Line'> | undefined
let emaSeries: ISeriesApi<'Line'> | undefined
let bollUpperSeries: ISeriesApi<'Line'> | undefined
let bollMiddleSeries: ISeriesApi<'Line'> | undefined
let bollLowerSeries: ISeriesApi<'Line'> | undefined
let volumeSeries: ISeriesApi<'Histogram'> | undefined
let factorCharts = new Map<string, IChartApi>()
let factorSeries = new Map<string, ISeriesApi<'Line'>>()
let resizeObserver: ResizeObserver | undefined
let syncingRange = false
let syncingCrosshair = false
let lastFitKey = -1
let suppressOlderRequest = false

const candleByTime = computed(() => new Map(props.candles.map((item) => [item.time, item])))
const factorByTime = computed(() => new Map(props.factors.map((item) => [item.time, item])))
const signalByTime = computed(() => {
  const result = new Map<number, TradeSignal[]>()
  for (const signal of props.tradeSignals || []) {
    const list = result.get(signal.time) || []
    list.push(signal)
    result.set(signal.time, list)
  }
  return result
})
const selectedTime = computed(() => hoverTime.value ?? props.candles.at(-1)?.time ?? null)
const selectedCandle = computed(() => (selectedTime.value ? candleByTime.value.get(selectedTime.value) : undefined))
const selectedFactor = computed(() => (selectedTime.value ? factorByTime.value.get(selectedTime.value) : undefined))
const selectedSignals = computed(() => (selectedTime.value ? signalByTime.value.get(selectedTime.value) || [] : []))
const vwapByTime = computed(() => new Map(vwapData().map((item) => [item.time as number, item.value])))
const selectedVwap = computed(() => (selectedTime.value ? vwapByTime.value.get(selectedTime.value) : undefined))
const maByTime = computed(() => new Map(movingAverageData(props.maPeriod).map((item) => [item.time as number, item.value])))
const selectedMa = computed(() => (selectedTime.value ? maByTime.value.get(selectedTime.value) : undefined))
const emaByTime = computed(() => new Map(exponentialMovingAverageData(props.emaPeriod).map((item) => [item.time as number, item.value])))
const selectedEma = computed(() => (selectedTime.value ? emaByTime.value.get(selectedTime.value) : undefined))
const bollingerByTime = computed(() => {
  const result = new Map<number, { upper: number; middle: number; lower: number }>()
  for (const item of bollingerData(props.bollingerPeriod, props.bollingerMultiplier)) {
    result.set(item.time as number, {
      upper: item.upper,
      middle: item.middle,
      lower: item.lower
    })
  }
  return result
})
const selectedBollinger = computed(() => (selectedTime.value ? bollingerByTime.value.get(selectedTime.value) : undefined))
const factorPercentiles = computed(() => {
  const result = new Map<string, Map<number, number>>()

  for (const key of props.selectedFactors) {
    const values = props.factors
      .map((item) => ({ time: item.time, value: item[key] }))
      .filter((item): item is { time: number; value: number } => typeof item.value === 'number' && Number.isFinite(item.value))
    const sorted = values.map((item) => item.value).sort((a, b) => a - b)
    const byTime = new Map<number, number>()

    for (const item of values) {
      byTime.set(item.time, upperBound(sorted, item.value) / sorted.length)
    }

    result.set(key, byTime)
  }

  return result
})

function upperBound(values: number[], target: number) {
  let left = 0
  let right = values.length
  while (left < right) {
    const middle = Math.floor((left + right) / 2)
    if (values[middle] <= target) {
      left = middle + 1
    } else {
      right = middle
    }
  }
  return left
}

function formatTime(value: number | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(new Date(value * 1000))
}

function formatNumber(value?: number | null, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return value.toFixed(digits)
}

function formatVolume(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(2)}K`
  return `${value}`
}

function formatPercentile(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return `${(value * 100).toFixed(1)}%`
}

function percentileFor(key: string) {
  if (!selectedTime.value) return null
  return factorPercentiles.value.get(key)?.get(selectedTime.value) ?? null
}

function factorMeta(key: string) {
  return props.factorSeries.find((item) => item.key === key) ?? { key, label: key, color: '#38bdf8', zeroLine: true }
}

function setFactorHost(key: string, element: Element | unknown | null) {
  if (element instanceof HTMLDivElement) {
    factorHosts.set(key, element)
  } else {
    factorHosts.delete(key)
  }
}

function allCharts() {
  return [candleChart, ...factorCharts.values()].filter(Boolean) as IChartApi[]
}

function syncVisibleRange(source: IChartApi) {
  const range = source.timeScale().getVisibleLogicalRange()
  if (!range || syncingRange) return
  syncingRange = true
  for (const target of allCharts()) {
    if (target !== source) target.timeScale().setVisibleLogicalRange(range)
  }
  queueMicrotask(() => {
    syncingRange = false
  })
}

function bindTimeScaleSync(chart: IChartApi) {
  chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
    if (syncingRange) return
    const range = chart.timeScale().getVisibleLogicalRange()
    if (!suppressOlderRequest && range && range.from < 40) emit('loadOlder')
    syncVisibleRange(chart)
  })
}

function normalizedVisibleCount(value = props.visibleCandleCount) {
  return Math.min(2000, Math.max(20, Math.floor(value || 160)))
}

function normalizedStep(value: number, fallback: number) {
  return Math.min(2000, Math.max(1, Math.floor(value || fallback)))
}

function currentVisibleRange() {
  return candleChart?.timeScale().getVisibleLogicalRange() ?? null
}

function setPrimaryVisibleRange(from: number, to: number) {
  if (!candleChart) return
  const maxIndex = Math.max(props.candles.length - 1, 0)
  const width = Math.max(to - from, 1)
  let nextFrom = Math.max(0, Math.min(from, maxIndex))
  let nextTo = nextFrom + width
  if (nextTo > maxIndex) {
    nextTo = maxIndex
    nextFrom = Math.max(0, nextTo - width)
  }
  candleChart.timeScale().setVisibleLogicalRange({ from: nextFrom, to: nextTo })
  syncVisibleRange(candleChart)
}

function setRangeWithRightOffset(from: number, to: number, rightOffset = 10) {
  if (!candleChart) return
  const maxIndex = Math.max(props.candles.length - 1, 0)
  const nextFrom = Math.max(0, Math.min(from, maxIndex))
  const nextTo = Math.max(nextFrom + 1, Math.min(to, maxIndex) + rightOffset)
  candleChart.timeScale().setVisibleLogicalRange({ from: nextFrom, to: nextTo })
  syncVisibleRange(candleChart)
}

function shiftVisibleRange(amount: number) {
  const range = currentVisibleRange()
  if (!range) return
  if (range.from + amount < 40) emit('loadOlder')
  setPrimaryVisibleRange(range.from + amount, range.to + amount)
}

function resizeVisibleCount(nextCount: number) {
  const count = normalizedVisibleCount(nextCount)
  emit('update:visibleCandleCount', count)
  const range = currentVisibleRange()
  const to = range?.to ?? Math.max(props.candles.length - 1, 0)
  setPrimaryVisibleRange(to - count + 1, to)
}

function showRecentSessions(sessionCount: number) {
  if (!props.candles.length) return
  selectedSessionCount.value = sessionCount
  const sessions = [...new Set(props.candles.map((item) => sessionKey(item.time)))]
  const selectedSessions = new Set(sessions.slice(-Math.max(1, sessionCount)))
  const allIndexes = props.candles
    .map((item, index) => selectedSessions.has(sessionKey(item.time)) ? index : -1)
    .filter((index) => index >= 0)
  const firstIndex = allIndexes.length > 280 ? allIndexes[allIndexes.length - 280] : allIndexes[0]
  if (firstIndex < 0) return
  const lastIndex = props.candles.length - 1
  emit('update:visibleCandleCount', lastIndex - firstIndex + 1)
  setRangeWithRightOffset(firstIndex, lastIndex, 10)
}

function showTodayCandles() {
  showRecentSessions(1)
}

function factorValue(point: FactorPoint, key: string) {
  return point[key]
}

function factorDisplayMode(key: string) {
  return factorMeta(key).displayMode || 'raw'
}

function transformFactorValue(value: number, mode: FactorDisplayMode) {
  if (!Number.isFinite(value)) return null
  if (mode === 'percent') return value * 100
  if (mode === 'log10') return value > 0 ? Math.log10(value) : null
  if (mode === 'symlog') return Math.sign(value) * Math.log10(1 + Math.abs(value))
  return value
}

function chartFactorValue(point: FactorPoint | undefined, key: string) {
  if (!point) return null
  const value = factorValue(point, key)
  return typeof value === 'number' ? transformFactorValue(value, factorDisplayMode(key)) : null
}

function transformedFactorValues(key: string) {
  return props.factors
    .map((item) => {
      const value = factorValue(item, key)
      return typeof value === 'number' ? transformFactorValue(value, factorDisplayMode(key)) : null
    })
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
}

function sessionKey(time: number) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date(time * 1000))
}

function vwapData() {
  let currentSession = ''
  let cumulativeTurnover = 0
  let cumulativeVolume = 0

  return props.candles.flatMap((item) => {
    const key = sessionKey(item.time)
    if (key !== currentSession) {
      currentSession = key
      cumulativeTurnover = 0
      cumulativeVolume = 0
    }

    const volume = Number(item.volume || 0)
    const turnover = Number(item.turnover || 0)
    if (!Number.isFinite(volume) || !Number.isFinite(turnover) || volume <= 0 || turnover <= 0) {
      return []
    }

    cumulativeVolume += volume
    cumulativeTurnover += turnover
    return [{ time: item.time as UTCTimestamp, value: cumulativeTurnover / cumulativeVolume }]
  })
}

function movingAverageData(period: number) {
  const result: Array<{ time: UTCTimestamp; value: number }> = []
  let sum = 0
  const safePeriod = Math.max(1, Math.floor(period || 1))

  props.candles.forEach((item, index) => {
    sum += item.close
    if (index >= safePeriod) sum -= props.candles[index - safePeriod].close
    if (index >= safePeriod - 1) {
      result.push({ time: item.time as UTCTimestamp, value: sum / safePeriod })
    }
  })

  return result
}

function exponentialMovingAverageData(period: number) {
  const result: Array<{ time: UTCTimestamp; value: number }> = []
  const safePeriod = Math.max(1, Math.floor(period || 1))
  const multiplier = 2 / (safePeriod + 1)
  let ema: number | undefined

  props.candles.forEach((item, index) => {
    if (index < safePeriod - 1) return
    if (ema === undefined) {
      const windowItems = props.candles.slice(index - safePeriod + 1, index + 1)
      ema = windowItems.reduce((sum, row) => sum + row.close, 0) / safePeriod
    } else {
      ema = (item.close - ema) * multiplier + ema
    }
    result.push({ time: item.time as UTCTimestamp, value: ema })
  })

  return result
}

function bollingerData(period: number, multiplier: number) {
  const result: Array<{ time: UTCTimestamp; upper: number; middle: number; lower: number }> = []
  const safePeriod = Math.max(1, Math.floor(period || 1))
  const safeMultiplier = Number.isFinite(multiplier) ? multiplier : 2

  props.candles.forEach((item, index) => {
    if (index < safePeriod - 1) return
    const windowItems = props.candles.slice(index - safePeriod + 1, index + 1)
    const middle = windowItems.reduce((sum, row) => sum + row.close, 0) / safePeriod
    const variance = windowItems.reduce((sum, row) => sum + (row.close - middle) ** 2, 0) / safePeriod
    const width = Math.sqrt(variance) * safeMultiplier
    result.push({
      time: item.time as UTCTimestamp,
      upper: middle + width,
      middle,
      lower: middle - width
    })
  })

  return result
}

function signalMarkers() {
  return (props.tradeSignals || []).map((signal) => ({
    time: signal.time as UTCTimestamp,
    position: signal.action === 'buy' ? 'belowBar' : 'aboveBar',
    color: signal.action === 'buy' ? '#22c55e' : '#f43f5e',
    shape: signal.action === 'buy' ? 'arrowUp' : 'arrowDown',
    text: `${signal.action === 'buy' ? '买' : '卖'} ${formatVolume(signal.executed_quantity || signal.quantity)}`
  }))
}

function syncCrosshair(time: number | null, source?: IChartApi) {
  if (syncingCrosshair) return
  hoverTime.value = time
  syncingCrosshair = true

  if (!time) {
    for (const chart of allCharts()) {
      if (chart !== source) chart.clearCrosshairPosition()
    }
    queueMicrotask(() => {
      syncingCrosshair = false
    })
    return
  }

  const candle = candleByTime.value.get(time)
  if (candleChart && candleSeries && candleChart !== source && candle) {
    candleChart.setCrosshairPosition(candle.close, time as UTCTimestamp, candleSeries)
  }

  const factor = factorByTime.value.get(time)
  for (const [key, chart] of factorCharts) {
    const series = factorSeries.get(key)
    if (!series || chart === source) continue
    const value = chartFactorValue(factor, key)
    chart.setCrosshairPosition(typeof value === 'number' && Number.isFinite(value) ? value : 0, time as UTCTimestamp, series)
  }

  queueMicrotask(() => {
    syncingCrosshair = false
  })
}

function render() {
  if (!candleSeries) return
  candleSeries.setData(
    props.candles.map((item) => ({
      time: item.time as UTCTimestamp,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }))
  )
  vwapSeries?.setData(props.showVwap ? vwapData() : [])
  maSeries?.setData(props.showMa ? movingAverageData(props.maPeriod) : [])
  emaSeries?.setData(props.showEma ? exponentialMovingAverageData(props.emaPeriod) : [])
  const bollinger = bollingerData(props.bollingerPeriod, props.bollingerMultiplier)
  bollUpperSeries?.setData(props.showBollinger ? bollinger.map((item) => ({ time: item.time, value: item.upper })) : [])
  bollMiddleSeries?.setData(props.showBollinger ? bollinger.map((item) => ({ time: item.time, value: item.middle })) : [])
  bollLowerSeries?.setData(props.showBollinger ? bollinger.map((item) => ({ time: item.time, value: item.lower })) : [])
  volumeSeries?.setData(
    props.candles.map((item) => {
      const value = item.volume || 0
      return {
        time: item.time as UTCTimestamp,
        value,
        color: item.close >= item.open ? 'rgba(15, 159, 110, 0.28)' : 'rgba(214, 69, 80, 0.28)'
      }
    })
  )
  ;(candleSeries as unknown as { setMarkers?: (markers: unknown[]) => void })?.setMarkers?.(signalMarkers())
  for (const [key, series] of factorSeries) {
    applyFactorSeriesOptions(key, series)
    series.setData(
      props.factors.map((item) => {
        const value = factorValue(item, key)
        const chartValue = typeof value === 'number' ? transformFactorValue(value, factorDisplayMode(key)) : null
        return value === null || value === undefined
          ? { time: item.time as UTCTimestamp }
          : chartValue === null
            ? { time: item.time as UTCTimestamp }
            : { time: item.time as UTCTimestamp, value: chartValue }
      })
    )
  }
  if (candleChart && props.lockTodayRange) {
    showRecentSessions(1)
    lastFitKey = props.fitKey
  } else if (candleChart && props.rangeButtons) {
    showRecentSessions(selectedSessionCount.value)
    lastFitKey = props.fitKey
  } else if (candleChart && props.fitKey !== lastFitKey) {
    suppressOlderRequest = true
    const count = normalizedVisibleCount()
    const to = Math.max(props.candles.length - 1, 0)
    const from = Math.max(to - count + 1, 0)
    candleChart.timeScale().setVisibleLogicalRange({ from, to })
    syncVisibleRange(candleChart)
    lastFitKey = props.fitKey
    window.setTimeout(() => {
      suppressOlderRequest = false
    }, 250)
  }
}

function createFactorChart(key: string, host: HTMLDivElement) {
  const meta = factorMeta(key)
  const chart = createChart(host, {
    autoSize: true,
    layout: {
      background: { color: chartTheme.background },
      textColor: chartTheme.text
    },
    grid: {
      vertLines: { color: chartTheme.grid },
      horzLines: { color: chartTheme.grid }
    },
    crosshair: {
      mode: 1
    },
    rightPriceScale: {
      borderColor: chartTheme.border,
      minimumWidth: 82,
      ticksVisible: true,
      entireTextOnly: false
    },
    timeScale: {
      borderColor: chartTheme.border,
      timeVisible: true,
      secondsVisible: false
    }
  })
  const series = chart.addLineSeries({
    color: meta.color,
    lineWidth: 2,
    title: ''
  })
  if (meta.zeroLine) {
    series.createPriceLine({
      price: 0,
      color: chartTheme.zero,
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: '0'
    })
  }
  factorCharts.set(key, chart)
  factorSeries.set(key, series)
  applyFactorSeriesOptions(key, series)
  resizeObserver?.observe(host)
  bindTimeScaleSync(chart)
  chart.subscribeCrosshairMove((param) => {
    if (syncingCrosshair) return
    syncCrosshair(typeof param.time === 'number' ? param.time : null, chart)
  })
}

function applyFactorSeriesOptions(key: string, series: ISeriesApi<'Line'>) {
  const mode = factorDisplayMode(key)
  const values = transformedFactorValues(key)
  const shouldCenterZero = mode === 'zero_center' || mode === 'symlog'
  ;(series as unknown as { applyOptions: (options: Record<string, unknown>) => void }).applyOptions({
    autoscaleInfoProvider: shouldCenterZero
      ? () => {
          const maxAbs = Math.max(1e-9, ...values.map((value) => Math.abs(value)))
          return {
            priceRange: {
              minValue: -maxAbs,
              maxValue: maxAbs
            }
          }
        }
      : undefined
  })
}

async function syncFactorCharts() {
  await nextTick()
  for (const key of props.selectedFactors) {
    const host = factorHosts.get(key)
    if (host && !factorCharts.has(key)) createFactorChart(key, host)
  }
  for (const key of [...factorCharts.keys()]) {
    if (!props.selectedFactors.includes(key)) {
      factorCharts.get(key)?.remove()
      factorCharts.delete(key)
      factorSeries.delete(key)
    }
  }
  render()
}

onMounted(() => {
  if (!candleHost.value) return
  candleChart = createChart(candleHost.value, {
    autoSize: true,
    layout: {
      background: { color: chartTheme.background },
      textColor: chartTheme.text
    },
    grid: {
      vertLines: { color: chartTheme.grid },
      horzLines: { color: chartTheme.grid }
    },
    crosshair: {
      mode: 1
    },
    rightPriceScale: {
      borderColor: chartTheme.border,
      minimumWidth: 72
    },
    timeScale: {
      borderColor: chartTheme.border,
      timeVisible: true,
      secondsVisible: false
    }
  })
  candleSeries = candleChart.addCandlestickSeries({
    upColor: '#22c55e',
    downColor: '#f43f5e',
    borderUpColor: '#22c55e',
    borderDownColor: '#f43f5e',
    wickUpColor: '#22c55e',
    wickDownColor: '#f43f5e'
  })
  vwapSeries = candleChart.addLineSeries({
    color: '#a78bfa',
    lineWidth: 2,
    title: '',
    priceLineVisible: false
  })
  maSeries = candleChart.addLineSeries({
    color: '#06b6d4',
    lineWidth: 2,
    title: '',
    priceLineVisible: false
  })
  emaSeries = candleChart.addLineSeries({
    color: '#38bdf8',
    lineWidth: 2,
    title: '',
    priceLineVisible: false
  })
  bollUpperSeries = candleChart.addLineSeries({
    color: '#c084fc',
    lineWidth: 1,
    title: '',
    priceLineVisible: false
  })
  bollMiddleSeries = candleChart.addLineSeries({
    color: '#fbbf24',
    lineWidth: 1,
    title: '',
    priceLineVisible: false
  })
  bollLowerSeries = candleChart.addLineSeries({
    color: '#c084fc',
    lineWidth: 1,
    title: '',
    priceLineVisible: false
  })
  volumeSeries = candleChart.addHistogramSeries({
    color: 'rgba(82, 100, 123, 0.24)',
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
    priceLineVisible: false,
    lastValueVisible: false
  })
  candleChart.priceScale('right').applyOptions({
    scaleMargins: {
      top: 0.08,
      bottom: 0.28
    }
  })
  candleChart.priceScale('volume').applyOptions({
    scaleMargins: {
      top: 0.78,
      bottom: 0
    }
  })
  candleChart.subscribeCrosshairMove((param) => {
    if (syncingCrosshair) return
    syncCrosshair(typeof param.time === 'number' ? param.time : null, candleChart)
  })
  resizeObserver = new ResizeObserver(() => {
    candleChart?.applyOptions({ autoSize: true })
    for (const chart of factorCharts.values()) chart.applyOptions({ autoSize: true })
  })
  resizeObserver.observe(candleHost.value)
  bindTimeScaleSync(candleChart)
  syncFactorCharts()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  candleChart?.remove()
  for (const chart of factorCharts.values()) chart.remove()
})

watch(
  () => [
    props.candles,
    props.factors,
    props.fitKey,
    props.showVwap,
    props.showMa,
    props.showEma,
    props.showBollinger,
    props.maPeriod,
    props.emaPeriod,
    props.bollingerPeriod,
    props.bollingerMultiplier,
    props.tradeSignals
  ],
  render,
  { deep: true }
)
watch(() => [props.selectedFactors, props.factorSeries], syncFactorCharts, { deep: true })
</script>

<template>
  <div class="chart-stack">
    <div v-if="rangeButtons && !lockTodayRange" class="chart-nav-bar">
      <button type="button" title="展示今天" @click="showRecentSessions(1)">今天</button>
      <button type="button" title="展示近三天" @click="showRecentSessions(3)">近三天</button>
      <button type="button" title="展示近5天" @click="showRecentSessions(5)">近5天</button>
      <button type="button" title="展示近10天" @click="showRecentSessions(10)">近10天</button>
    </div>
    <div v-else-if="!lockTodayRange" class="chart-nav-bar">
      <button type="button" title="向左翻页" @click="shiftVisibleRange(-normalizedVisibleCount())">‹‹</button>
      <button type="button" title="向左滑动" @click="shiftVisibleRange(-normalizedStep(moveStep, 40))">‹</button>
      <button type="button" title="增加展示数量" @click="resizeVisibleCount(normalizedVisibleCount() + normalizedStep(sizeStep, 20))">+</button>
      <label class="visible-count-field">
        展示
        <input :value="normalizedVisibleCount()" type="number" min="20" max="2000" @change="resizeVisibleCount(Number(($event.target as HTMLInputElement).value))" />
        根
      </label>
      <button v-if="showTodayButton" type="button" title="展示今天" @click="showTodayCandles">今天</button>
      <button type="button" title="减少展示数量" @click="resizeVisibleCount(normalizedVisibleCount() - normalizedStep(sizeStep, 20))">-</button>
      <button type="button" title="向右滑动" @click="shiftVisibleRange(normalizedStep(moveStep, 40))">›</button>
      <button type="button" title="向右翻页" @click="shiftVisibleRange(normalizedVisibleCount())">››</button>
      <label>
        加减
        <input v-model.number="sizeStep" type="number" min="1" max="2000" />
      </label>
      <label>
        左右
        <input v-model.number="moveStep" type="number" min="1" max="2000" />
      </label>
    </div>
    <div class="price-chart-wrap">
      <div v-if="!candles.length" class="empty">暂无本地K线数据</div>
      <div ref="candleHost" class="chart full"></div>
    </div>
    <div v-for="key in selectedFactors" :key="key" class="factor-panel">
      <div class="factor-panel-title">
        <span><i :style="{ background: factorMeta(key).color }"></i></span>
        <span>{{ formatNumber(chartFactorValue(selectedFactor, key), 6) }} · 分位 {{ formatPercentile(percentileFor(key)) }}</span>
      </div>
      <div :ref="(el) => setFactorHost(key, el)" class="factor-chart"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { LineStyle, createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from 'lightweight-charts'
import type { Candle } from '../api'

type FactorPoint = { time: number; [key: string]: number | null | undefined }
type FactorSeriesMeta = { key: string; label: string; color: string; zeroLine?: boolean }
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

function factorValue(point: FactorPoint, key: string) {
  return point[key]
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
    const value = factor ? factorValue(factor, key) : null
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
    series.setData(
      props.factors.map((item) => {
        const value = factorValue(item, key)
        return value === null || value === undefined
          ? { time: item.time as UTCTimestamp }
          : { time: item.time as UTCTimestamp, value }
      })
    )
  }
  if (candleChart && props.fitKey !== lastFitKey) {
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
      minimumWidth: 72
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
    title: meta.label
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
  resizeObserver?.observe(host)
  bindTimeScaleSync(chart)
  chart.subscribeCrosshairMove((param) => {
    if (syncingCrosshair) return
    syncCrosshair(typeof param.time === 'number' ? param.time : null, chart)
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
    title: 'VWAP',
    priceLineVisible: false
  })
  maSeries = candleChart.addLineSeries({
    color: '#06b6d4',
    lineWidth: 2,
    title: 'MA',
    priceLineVisible: false
  })
  emaSeries = candleChart.addLineSeries({
    color: '#38bdf8',
    lineWidth: 2,
    title: 'EMA',
    priceLineVisible: false
  })
  bollUpperSeries = candleChart.addLineSeries({
    color: '#c084fc',
    lineWidth: 1,
    title: 'BOLL上轨',
    priceLineVisible: false
  })
  bollMiddleSeries = candleChart.addLineSeries({
    color: '#fbbf24',
    lineWidth: 1,
    title: 'BOLL中轨',
    priceLineVisible: false
  })
  bollLowerSeries = candleChart.addLineSeries({
    color: '#c084fc',
    lineWidth: 1,
    title: 'BOLL下轨',
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
    <div class="chart-nav-bar">
      <button type="button" title="向左翻页" @click="shiftVisibleRange(-normalizedVisibleCount())">‹‹</button>
      <button type="button" title="向左滑动" @click="shiftVisibleRange(-normalizedStep(moveStep, 40))">‹</button>
      <button type="button" title="增加展示数量" @click="resizeVisibleCount(normalizedVisibleCount() + normalizedStep(sizeStep, 20))">+</button>
      <span>展示 {{ normalizedVisibleCount() }} 根</span>
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
    <div class="hover-table">
      <span>时间 {{ formatTime(selectedTime) }}</span>
      <span>开 {{ formatNumber(selectedCandle?.open, 3) }}</span>
      <span>高 {{ formatNumber(selectedCandle?.high, 3) }}</span>
      <span>低 {{ formatNumber(selectedCandle?.low, 3) }}</span>
      <span>收 {{ formatNumber(selectedCandle?.close, 3) }}</span>
      <span>量 {{ formatVolume(selectedCandle?.volume) }}</span>
      <span v-if="props.showVwap">VWAP {{ formatNumber(selectedVwap, 3) }}</span>
      <span v-if="props.showMa">MA{{ props.maPeriod }} {{ formatNumber(selectedMa, 3) }}</span>
      <span v-if="props.showEma">EMA{{ props.emaPeriod }} {{ formatNumber(selectedEma, 3) }}</span>
      <span v-if="props.showBollinger">
        BOLL{{ props.bollingerPeriod }},{{ props.bollingerMultiplier }} {{ formatNumber(selectedBollinger?.upper, 3) }} /
        {{ formatNumber(selectedBollinger?.middle, 3) }} /
        {{ formatNumber(selectedBollinger?.lower, 3) }}
      </span>
      <span v-for="key in selectedFactors" :key="key">
        {{ factorMeta(key).label }} {{ formatNumber(selectedFactor?.[key], 6) }} · 分位 {{ formatPercentile(percentileFor(key)) }}
      </span>
      <span v-for="signal in selectedSignals" :key="`${signal.time}-${signal.action}`">
        {{ signal.action === 'buy' ? '买点' : '卖点' }} {{ formatVolume(signal.executed_quantity || signal.quantity) }} ·
        {{ formatNumber(signal.price, 3) }}{{ signal.reason ? ` · ${signal.reason}` : '' }}
      </span>
    </div>
    <div class="price-chart-wrap">
      <div v-if="!candles.length" class="empty">暂无本地K线数据</div>
      <div ref="candleHost" class="chart full"></div>
    </div>
    <div v-for="key in selectedFactors" :key="key" class="factor-panel">
      <div class="factor-panel-title">
        <span><i :style="{ background: factorMeta(key).color }"></i>{{ factorMeta(key).label }}</span>
        <span>{{ formatNumber(selectedFactor?.[key], 6) }} · 分位 {{ formatPercentile(percentileFor(key)) }}</span>
      </div>
      <div :ref="(el) => setFactorHost(key, el)" class="factor-chart"></div>
    </div>
  </div>
</template>

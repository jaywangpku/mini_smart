<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from 'lightweight-charts'
import type { EquityPoint } from '../api'

const props = defineProps<{
  points: EquityPoint[]
}>()

const host = ref<HTMLDivElement | null>(null)
let chart: IChartApi | undefined
let series: ISeriesApi<'Line'> | undefined
let resizeObserver: ResizeObserver | undefined

function render() {
  if (!series) return
  series.setData(
    props.points.map((point) => ({
      time: point.time as UTCTimestamp,
      value: point.value
    }))
  )
  chart?.timeScale().fitContent()
}

onMounted(() => {
  if (!host.value) return
  chart = createChart(host.value, {
    autoSize: true,
    layout: {
      background: { color: '#0f172a' },
      textColor: '#cbd5e1'
    },
    grid: {
      vertLines: { color: '#1e293b' },
      horzLines: { color: '#1e293b' }
    },
    rightPriceScale: {
      borderColor: '#334155',
      minimumWidth: 72
    },
    timeScale: {
      borderColor: '#334155',
      timeVisible: true,
      secondsVisible: false
    }
  })
  series = chart.addLineSeries({
    color: '#38bdf8',
    lineWidth: 2,
    title: '权益曲线',
    priceLineVisible: false
  })
  resizeObserver = new ResizeObserver(() => chart?.applyOptions({ autoSize: true }))
  resizeObserver.observe(host.value)
  render()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  chart?.remove()
})

watch(() => props.points, render, { deep: true })
</script>

<template>
  <div class="equity-chart-wrap">
    <div v-if="!points.length" class="empty">暂无收益曲线数据</div>
    <div ref="host" class="chart full"></div>
  </div>
</template>

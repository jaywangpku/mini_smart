<script setup lang="ts">
import type { StrategyRunResult } from '../api'
import { formatMoney, formatPct } from '../utils'
import EquityCurveChart from './EquityCurveChart.vue'

defineProps<{
  result: StrategyRunResult
  showEquity: boolean
  showCashPosition?: boolean
}>()

const emit = defineEmits<{
  'update:showEquity': [value: boolean]
}>()
</script>

<template>
  <div class="strategy-result-panel">
    <div class="summary-grid">
      <span>收益 {{ formatPct(result.summary.total_return_pct) }}</span>
      <span>最终资产 {{ formatMoney(result.summary.final_value) }}</span>
      <span v-if="showCashPosition">现金 {{ formatMoney(result.summary.cash) }}</span>
      <span v-if="showCashPosition">持仓 {{ result.summary.position }}</span>
      <span>交易 {{ result.summary.trade_count }}</span>
      <span>胜率 {{ formatPct(result.summary.win_rate) }}</span>
      <span>最大回撤 {{ formatPct(result.summary.max_drawdown_pct) }}</span>
      <button class="ghost compact summary-action" type="button" @click="emit('update:showEquity', !showEquity)">
        {{ showEquity ? '隐藏收益曲线' : '展示收益曲线' }}
      </button>
    </div>
    <EquityCurveChart v-if="showEquity" :points="result.equity_curve" />
  </div>
</template>

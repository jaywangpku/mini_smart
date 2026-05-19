<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'strategyResearch'" class="research-layout">
        <aside class="panel research-controls">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>策略研究</span>
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
          <label>
            策略
            <select v-model="strategyResearchStrategyId">
              <option v-for="strategy in enabledCustomStrategies" :key="strategy.id" :value="strategy.id">{{ strategy.name }}</option>
            </select>
          </label>
          <button class="ghost param-button strategy-param-button" type="button" @click="openResearchStrategyParamDialog">策略参数</button>
          <label>
            开始日期
            <input v-model="strategyResearchStart" type="date" />
          </label>
          <label>
            结束日期
            <input v-model="strategyResearchEnd" type="date" />
          </label>
          <label>
            初始资金
            <input v-model.number="strategyInitialCash" type="number" min="1" />
          </label>
          <label>
            手续费率
            <input v-model.number="strategyFeeRate" type="number" min="0" step="0.0001" />
          </label>
          <label>
            滑点率
            <input v-model.number="strategySlippageRate" type="number" min="0" step="0.0001" />
          </label>
          <button class="submit" :disabled="!strategyResearchStrategyId || !researchSymbol" @click="runStrategyResearch">
            <Play :size="17" />
            <span>运行策略</span>
          </button>
        </aside>

        <section class="main-panel research-panel">
          <div class="chart-head">
            <div>
              <h2>{{ selectedResearchStrategy?.name || '请选择策略' }} · {{ researchSymbol || '请选择股票' }}</h2>
              <p>{{ strategyResearchCandles.length }} 根K线 · {{ strategyResearchResult?.signals.length || 0 }} 个信号</p>
            </div>
          </div>
          <KlineChart
            :candles="strategyResearchCandles"
            :factors="[]"
            :selected-factors="[]"
            :factor-series="[]"
            :fit-key="strategyResearchFitKey"
            :show-vwap="showVwap"
            :show-ma="showMa"
            :show-ema="showEma"
            :show-bollinger="showBollinger"
            :ma-period="maPeriod"
            :ema-period="emaPeriod"
            :bollinger-period="bollingerPeriod"
            :bollinger-multiplier="bollingerMultiplier"
            :trade-signals="strategyResearchResult?.signals || []"
            v-model:visible-candle-count="visibleCandleCount"
            @load-older="() => {}"
          />
          <StrategyResultPanel v-if="strategyResearchResult" :result="strategyResearchResult" show-cash-position v-model:show-equity="showStrategyResearchEquity" />
          <div v-if="strategyResearchResult?.trades.length" class="task-table strategy-table">
            <div class="strategy-trade-row header">
              <span>买入时间</span>
              <span>卖出时间</span>
              <span>数量</span>
              <span>买入价</span>
              <span>卖出价</span>
              <span>盈亏</span>
              <span>收益率</span>
            </div>
            <div v-for="trade in strategyResearchResult.trades.slice(-20).reverse()" :key="`${trade.buy_time}-${trade.sell_time}`" class="strategy-trade-row">
              <span>{{ new Date(trade.buy_time * 1000).toLocaleString() }}</span>
              <span>{{ new Date(trade.sell_time * 1000).toLocaleString() }}</span>
              <span>{{ trade.quantity }}</span>
              <span>{{ formatMoney(trade.buy_price) }}</span>
              <span>{{ formatMoney(trade.sell_price) }}</span>
              <span>{{ formatMoney(trade.pnl) }}</span>
              <span>{{ formatPct(trade.return_pct) }}</span>
            </div>
          </div>
        </section>
      </section>
</template>

<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, researchStart, researchEnd, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'history'" class="research-layout">
        <aside class="panel research-controls">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>历史看板</span>
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
            开始日期
            <input v-model="researchStart" type="date" />
          </label>
          <label>
            结束日期
            <input v-model="researchEnd" type="date" />
          </label>
          <button class="ghost config-action-button" type="button" @click="openRealtimeIndicatorDialog">
            K线指标 · {{ [showVwap, showMa, showEma, showBollinger].filter(Boolean).length }} 项
          </button>
          <button class="submit" @click="loadHistoryChart({ resetView: true })">
            <RefreshCw :size="17" />
            <span>刷新图表</span>
          </button>
        </aside>

        <section class="main-panel research-panel">
          <div class="chart-head">
            <div>
              <h2>{{ researchSymbol || '请选择股票' }} · {{ period }}</h2>
              <p>{{ historyCandles.length }} 根历史K线</p>
            </div>
          </div>
          <KlineChart
            :candles="historyCandles"
            :factors="[]"
            :selected-factors="[]"
            :factor-series="[]"
            :fit-key="historyFitKey"
            :show-vwap="showVwap"
            :show-ma="showMa"
            :show-ema="showEma"
            :show-bollinger="showBollinger"
            :ma-period="maPeriod"
            :ema-period="emaPeriod"
            :bollinger-period="bollingerPeriod"
            :bollinger-multiplier="bollingerMultiplier"
            v-model:visible-candle-count="visibleCandleCount"
            @load-older="loadOlderHistoryChartData"
          />
        </section>
      </section>
</template>

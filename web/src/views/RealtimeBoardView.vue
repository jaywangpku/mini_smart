<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'realtime'" class="research-layout">
        <aside class="panel research-controls">
          <div class="panel-title">
            <Activity :size="17" />
            <span>实时看板</span>
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
            刷新秒数
            <input v-model.number="realtimePollInterval" type="number" min="1" max="60" step="1" />
          </label>
          <button class="ghost param-button strategy-param-button" type="button" @click="openRealtimeIndicatorDialog">
            K线指标 · {{ [showVwap, showMa, showEma, showBollinger].filter(Boolean).length }} 项
          </button>
          <button class="ghost param-button strategy-param-button" type="button" @click="openRealtimeFactorDialog">
            实时因子 · {{ realtimeSelectedFactors.length }} / 2
          </button>
          <label>
            实时策略
            <select v-model="realtimeStrategyId">
              <option value="">不运行策略</option>
              <option v-for="strategy in enabledCustomStrategies" :key="strategy.id" :value="strategy.id">{{ strategy.name }}</option>
            </select>
          </label>
          <button class="ghost param-button strategy-param-button" type="button" :disabled="!realtimeStrategyId" @click="openRealtimeStrategyParamDialog">策略参数</button>
          <div class="sync-actions realtime-actions">
            <button class="submit compact" :disabled="realtimeConnected" @click="startRealtime">
              <Play :size="17" />
              <span>启动</span>
            </button>
            <button class="submit secondary compact" @click="refreshRealtime">
              <RefreshCw :size="17" />
              <span>刷新</span>
            </button>
            <button class="submit danger compact" :disabled="!realtimeConnected" @click="() => stopRealtime()">
              <Trash2 :size="17" />
              <span>停止</span>
            </button>
          </div>
        </aside>

        <section class="main-panel research-panel">
          <div class="chart-head">
            <div>
              <h2>实时行情与信号</h2>
              <p>
                {{ realtimeStatus }} · {{ realtimeSource }}
                <template v-if="realtimeUpdatedAt"> · {{ realtimeUpdatedAt }}</template>
              </p>
            </div>
          </div>
          <div v-if="realtimeWarning" class="empty-state">{{ realtimeWarning }}</div>
          <KlineChart
            :candles="realtimeCandles"
            :factors="realtimeFactors"
            :selected-factors="realtimeSelectedFactors"
            :factor-series="factorSeriesMeta"
            :fit-key="realtimeFitKey"
            :show-vwap="showVwap"
            :show-ma="showMa"
            :show-ema="showEma"
            :show-bollinger="showBollinger"
            :ma-period="maPeriod"
            :ema-period="emaPeriod"
            :bollinger-period="bollingerPeriod"
            :bollinger-multiplier="bollingerMultiplier"
            :trade-signals="realtimeStrategyResult?.signals || []"
            lock-today-range
            v-model:visible-candle-count="visibleCandleCount"
            @load-older="() => {}"
          />
          <StrategyResultPanel
            v-if="realtimeStrategyResult"
            :result="realtimeStrategyResult"
            show-cash-position
            v-model:show-equity="showRealtimeEquity"
          />
        </section>
      </section>
</template>

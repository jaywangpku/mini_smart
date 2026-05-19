<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'sync'" class="tab-grid">
      <aside class="panel">
        <div class="panel-title">
          <Play :size="17" />
          <span>同步参数</span>
        </div>
        <label>
          股票池
          <select v-model="selectedPoolId">
            <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
          </select>
        </label>
        <label>
          周期
          <select v-model="period">
            <option value="all">全部周期</option>
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
          同步方式
          <select v-model="syncMode">
            <option value="incremental">增量更新</option>
            <option value="range">指定时间范围</option>
          </select>
        </label>
        <label>
          开始日期
          <input v-model="start" type="date" :disabled="syncMode === 'incremental'" />
        </label>
        <label>
          结束日期
          <input v-model="end" type="date" />
        </label>
        <div class="sync-actions">
          <button class="submit" :disabled="loading || !selectedSymbols.length || period === 'all'" @click="submitSelectedSync">
            <Play :size="17" />
            <span>同步选中的股票</span>
          </button>
          <button class="submit secondary" :disabled="loading || !enabledPoolSymbols.length" @click="submitPoolSync">
            <RefreshCw :size="17" />
            <span>同步当前股票池</span>
          </button>
        </div>
      </aside>

      <section class="main-panel">
        <div class="chart-head">
          <div>
            <h2>选择同步股票</h2>
            <p>已选择 {{ selectedSymbols.length }} / {{ enabledPoolSymbols.length }}</p>
          </div>
          <button class="ghost" @click="selectAllEnabled">全选启用</button>
        </div>
        <div class="selector-grid">
          <button
            v-for="row in enabledPoolSymbols"
            :key="row.symbol"
            :class="{ selected: selectedSymbols.includes(row.symbol) }"
            @click="toggleSelectedSymbol(row.symbol)"
          >
            <strong>{{ symbolLabel(row) }}</strong>
            <small v-if="row.name">{{ row.symbol }}</small>
          </button>
        </div>
        <div class="tasks">
          <div class="tasks-head">
            <div>
              <h2>同步任务</h2>
              <p>最新 20 条</p>
            </div>
            <button class="ghost" @click="loadTasks">刷新任务</button>
          </div>
          <div class="task-table">
            <div class="task-row header">
              <span>任务</span>
              <span>标的</span>
              <span>名称</span>
              <span>状态</span>
              <span>写入</span>
              <span>错误</span>
            </div>
            <div v-for="task in tasks" :key="task.id" class="task-row">
              <span>{{ task.id }}</span>
              <span>{{ task.symbol }}</span>
              <span>{{ taskSymbolLabel(task) }}</span>
              <span :class="['status', task.status]">{{ task.status }}</span>
              <span>{{ task.rows_written }}</span>
              <span class="task-error">{{ task.error || '' }}</span>
            </div>
          </div>
        </div>
      </section>
      </section>
</template>

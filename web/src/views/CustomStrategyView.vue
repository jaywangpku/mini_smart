<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from lucide-vue-next
import CodeEditor from ../components/CodeEditor.vue
import KlineChart from ../components/KlineChart.vue
import StrategyResultPanel from ../components/StrategyResultPanel.vue
import { useAppBindings } from ../appContext

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'customStrategies'" class="custom-factor-layout">
        <aside class="panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>自定义策略</span>
          </div>
          <button class="submit secondary" @click="openNewCustomStrategyDialog">
            <Plus :size="17" />
            <span>新建策略</span>
          </button>
          <div class="custom-factor-list">
            <button
              v-for="strategy in customStrategies"
              :key="strategy.id"
              :class="{ selected: selectedCustomStrategyId === strategy.id }"
              type="button"
              @click="selectCustomStrategy(strategy)"
            >
              <strong>{{ strategy.name }}</strong>
              <span>{{ strategy.code }} · {{ strategy.enabled ? '启用' : '停用' }}</span>
            </button>
          </div>
          <div v-if="selectedCustomStrategy" class="factor-side-actions">
            <div class="factor-side-summary">
              <strong>{{ customStrategyForm.name }}</strong>
              <span>{{ customStrategyForm.code }} · {{ customStrategyForm.enabled ? '启用' : '停用' }}</span>
              <p v-if="customStrategyForm.description">{{ customStrategyForm.description }}</p>
            </div>
            <div class="sync-actions">
              <button class="submit secondary" title="修改信息" @click="openEditCustomStrategyDialog">
                <Edit3 :size="17" />
              </button>
              <button class="submit" title="保存代码" @click="saveCustomStrategy">
                <Save :size="17" />
              </button>
              <button class="submit danger" title="删除策略" @click="removeCustomStrategy">
                <Trash2 :size="17" />
              </button>
            </div>
          </div>
        </aside>

        <section class="main-panel custom-factor-editor">
          <div v-if="selectedCustomStrategy" class="factor-workbench">
            <div class="param-strip">
              <span>策略参数</span>
              <code>{{ customStrategyForm.default_params.replace(/\s+/g, ' ') }}</code>
              <button class="ghost" @click="openStrategyParamDialog">编辑参数</button>
            </div>
            <CodeEditor v-model="customStrategyForm.source_code" language="python" />
            <div class="preview-config compact-preview">
              <label>
                股票池
                <select v-model="strategyPreviewPoolId">
                  <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
                </select>
              </label>
              <label>
                测试股票
                <select v-model="strategyPreviewSymbol">
                  <option v-for="row in strategyPreviewPoolSymbols" :key="row.symbol" :value="row.symbol">
                    {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
                  </option>
                </select>
              </label>
              <label>
                周期
                <select v-model="strategyPreviewPeriod">
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
                <select v-model="strategyPreviewAdjustType">
                  <option value="forward">前复权</option>
                  <option value="no_adjust">不复权</option>
                </select>
              </label>
              <label>
                样本数
                <input v-model.number="strategyPreviewLimit" type="number" min="20" max="5000" />
              </label>
              <button class="submit secondary compact" :disabled="!selectedCustomStrategyId" @click="runCustomStrategyPreview">
                <Play :size="16" />
                <span>试运行</span>
              </button>
            </div>
            <div class="preview-config compact-preview">
              <label>
                初始资金
                <input v-model.number="strategyPreviewInitialCash" type="number" min="1" />
              </label>
              <label>
                手续费率
                <input v-model.number="strategyPreviewFeeRate" type="number" min="0" step="0.0001" />
              </label>
              <label>
                滑点率
                <input v-model.number="strategyPreviewSlippageRate" type="number" min="0" step="0.0001" />
              </label>
            </div>
            <KlineChart
              v-if="strategyPreviewCandles.length"
              :candles="strategyPreviewCandles"
              :factors="[]"
              :selected-factors="[]"
              :factor-series="[]"
              :fit-key="strategyPreviewFitKey"
              :show-vwap="showVwap"
              :show-ma="false"
              :show-ema="false"
              :show-bollinger="false"
              :ma-period="maPeriod"
              :ema-period="emaPeriod"
              :bollinger-period="bollingerPeriod"
              :bollinger-multiplier="bollingerMultiplier"
              :trade-signals="strategyPreviewResult?.signals || []"
              v-model:visible-candle-count="visibleCandleCount"
              @load-older="() => {}"
            />
            <StrategyResultPanel v-if="strategyPreviewResult" :result="strategyPreviewResult" v-model:show-equity="showStrategyPreviewEquity" />
          </div>
          <div v-else class="empty-state">请先在左侧新建或选择一个自定义策略</div>
        </section>
      </section>
</template>

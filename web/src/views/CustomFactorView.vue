<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'customFactors'" class="custom-factor-layout">
        <aside class="panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>自定义因子</span>
          </div>
          <button class="submit secondary" @click="openNewCustomFactorDialog">
            <Plus :size="17" />
            <span>新建因子</span>
          </button>
          <div class="custom-factor-list">
            <button
              v-for="factor in customFactors"
              :key="factor.id"
              :class="{ selected: selectedCustomFactorId === factor.id }"
              type="button"
              @click="selectCustomFactor(factor)"
            >
              <strong>{{ factor.name }}</strong>
              <span>{{ factor.code }} · {{ factor.enabled ? '启用' : '停用' }}</span>
            </button>
          </div>
          <div v-if="selectedCustomFactor" class="factor-side-actions">
            <div class="factor-side-summary">
              <strong>{{ customFactorForm.name }}</strong>
              <span>{{ customFactorForm.code }} · {{ customFactorForm.enabled ? '启用' : '停用' }}</span>
              <p v-if="customFactorForm.description">{{ customFactorForm.description }}</p>
            </div>
            <div class="sync-actions">
              <button class="submit secondary" title="修改信息" @click="openEditCustomFactorDialog">
                <Edit3 :size="17" />
              </button>
              <button class="submit" title="保存代码" @click="saveCustomFactor">
                <Save :size="17" />
              </button>
              <button class="submit danger" title="删除因子" @click="removeCustomFactor">
                <Trash2 :size="17" />
              </button>
            </div>
          </div>
        </aside>

        <section class="main-panel custom-factor-editor">
          <div v-if="selectedCustomFactor" class="factor-workbench">
            <div class="param-strip">
              <span>因子参数</span>
              <code>{{ customFactorForm.default_params.replace(/\s+/g, ' ') }}</code>
              <button class="ghost" @click="openParamDialog">编辑参数</button>
            </div>
            <CodeEditor v-model="customFactorForm.source_code" language="python" />
            <div class="preview-config compact-preview">
              <label>
                股票池
                <select v-model="customPreviewPoolId">
                  <option v-for="pool in pools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
                </select>
              </label>
              <label>
                测试股票
                <select v-model="customPreviewSymbol">
                  <option v-for="row in customPreviewPoolSymbols" :key="row.symbol" :value="row.symbol">
                    {{ row.symbol }}{{ row.name ? ` · ${row.name}` : '' }}
                  </option>
                </select>
              </label>
              <label>
                周期
                <select v-model="customPreviewPeriod">
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
                <select v-model="customPreviewAdjustType">
                  <option value="forward">前复权</option>
                  <option value="no_adjust">不复权</option>
                </select>
              </label>
              <label>
                样本数
                <input v-model.number="customPreviewLimit" type="number" min="20" max="1000" />
              </label>
              <button class="submit secondary compact" :disabled="!selectedCustomFactorId" @click="runCustomFactorPreview">
                <Play :size="16" />
                <span>试运行</span>
              </button>
            </div>
            <KlineChart
              v-if="customPreviewCandles.length"
              :candles="customPreviewCandles"
              :factors="customPreviewFactors"
              :selected-factors="[previewFactorKey]"
              :factor-series="previewFactorSeries"
              :fit-key="customPreviewFitKey"
              :show-vwap="false"
              :show-ma="false"
              :show-ema="false"
              :show-bollinger="false"
              :ma-period="maPeriod"
              :ema-period="emaPeriod"
              :bollinger-period="bollingerPeriod"
              :bollinger-multiplier="bollingerMultiplier"
              v-model:visible-candle-count="visibleCandleCount"
              @load-older="() => {}"
            />
          </div>
          <div v-else class="empty-state">请先在左侧新建或选择一个自定义因子</div>
        </section>
      </section>
</template>

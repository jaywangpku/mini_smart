<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from 'lucide-vue-next'
import CodeEditor from '../components/CodeEditor.vue'
import KlineChart from '../components/KlineChart.vue'
import StrategyResultPanel from '../components/StrategyResultPanel.vue'
import { useAppBindings } from '../appContext'

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <div v-if="showNewFactorDialog" class="modal-backdrop" @click.self="closeNewCustomFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>新建自定义因子</span>
          </div>
          <label>
            因子编码
            <input v-model="newFactorDraft.code" placeholder="例如 rsi_factor" @keyup.enter="createCustomFactorFromDialog" />
          </label>
          <label>
            因子名称
            <input v-model="newFactorDraft.name" placeholder="例如 RSI 因子" @keyup.enter="createCustomFactorFromDialog" />
          </label>
          <label>
            描述
            <textarea v-model="newFactorDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewCustomFactorDialog">取消</button>
            <button class="submit compact" @click="createCustomFactorFromDialog">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditFactorDialog" class="modal-backdrop" @click.self="closeEditCustomFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>修改因子信息</span>
          </div>
          <label>
            因子编码
            <input v-model="editFactorDraft.code" placeholder="例如 rsi_factor" />
          </label>
          <label>
            因子名称
            <input v-model="editFactorDraft.name" placeholder="例如 RSI 因子" />
          </label>
          <label>
            描述
            <textarea v-model="editFactorDraft.description" placeholder="可选"></textarea>
          </label>
          <label class="check-row custom-enabled">
            <input v-model="editFactorDraft.enabled" type="checkbox" />
            启用
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditCustomFactorDialog">取消</button>
            <button class="submit compact" @click="saveCustomFactorMeta">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showNewStrategyDialog" class="modal-backdrop" @click.self="closeNewCustomStrategyDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>新建自定义策略</span>
          </div>
          <label>
            策略编码
            <input v-model="newStrategyDraft.code" placeholder="例如 momentum_strategy" @keyup.enter="createCustomStrategyFromDialog" />
          </label>
          <label>
            策略名称
            <input v-model="newStrategyDraft.name" placeholder="例如 动量策略" @keyup.enter="createCustomStrategyFromDialog" />
          </label>
          <label>
            描述
            <textarea v-model="newStrategyDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewCustomStrategyDialog">取消</button>
            <button class="submit compact" @click="createCustomStrategyFromDialog">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditStrategyDialog" class="modal-backdrop" @click.self="closeEditCustomStrategyDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>修改策略信息</span>
          </div>
          <label>
            策略编码
            <input v-model="editStrategyDraft.code" placeholder="例如 momentum_strategy" />
          </label>
          <label>
            策略名称
            <input v-model="editStrategyDraft.name" placeholder="例如 动量策略" />
          </label>
          <label>
            描述
            <textarea v-model="editStrategyDraft.description" placeholder="可选"></textarea>
          </label>
          <label class="check-row custom-enabled">
            <input v-model="editStrategyDraft.enabled" type="checkbox" />
            启用
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditCustomStrategyDialog">取消</button>
            <button class="submit compact" @click="saveCustomStrategyMeta">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showParamDialog" class="modal-backdrop" @click.self="closeParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>编辑因子参数 JSON</span>
          </div>
          <CodeEditor v-model="customFactorForm.default_params" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showStrategyParamDialog" class="modal-backdrop" @click.self="closeStrategyParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>编辑策略参数 JSON</span>
          </div>
          <CodeEditor v-model="customStrategyForm.default_params" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeStrategyParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showResearchStrategyParamDialog" class="modal-backdrop" @click.self="closeResearchStrategyParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>策略研究参数 JSON</span>
          </div>
          <CodeEditor v-model="strategyResearchParams" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeResearchStrategyParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showRealtimeStrategyParamDialog" class="modal-backdrop" @click.self="closeRealtimeStrategyParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>{{ selectedRealtimeStrategy?.name || '实时策略' }} 参数 JSON</span>
          </div>
          <CodeEditor v-model="realtimeStrategyParams" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeRealtimeStrategyParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showResearchParamDialog" class="modal-backdrop" @click.self="closeResearchParamDialog">
        <section class="modal-panel param-modal">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>{{ researchParamLabel(editingResearchParamKey) }} 参数 JSON</span>
          </div>
          <CodeEditor v-model="customFactorParamText[editingResearchParamKey]" language="json" />
          <div class="modal-actions">
            <button class="ghost" @click="closeResearchParamDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showRealtimeIndicatorDialog" class="modal-backdrop" @click.self="closeRealtimeIndicatorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>K线指标</span>
          </div>
          <div class="factor-picker modal-check-list">
            <div class="indicator-option-row">
              <label class="check-row">
                <input v-model="showVwap" type="checkbox" />
                VWAP
              </label>
            </div>
            <div class="indicator-option-row">
              <label class="check-row">
                <input v-model="showMa" type="checkbox" />
                MA
              </label>
              <button v-if="showMa" class="ghost param-button" type="button" @click="openSimpleParamDialog('ma')">参数配置</button>
            </div>
            <div class="indicator-option-row">
              <label class="check-row">
                <input v-model="showEma" type="checkbox" />
                EMA
              </label>
              <button v-if="showEma" class="ghost param-button" type="button" @click="openSimpleParamDialog('ema')">参数配置</button>
            </div>
            <div class="indicator-option-row">
              <label class="check-row">
                <input v-model="showBollinger" type="checkbox" />
                BOLL
              </label>
              <button v-if="showBollinger" class="ghost param-button" type="button" @click="openSimpleParamDialog('boll')">参数配置</button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="ghost" @click="closeRealtimeIndicatorDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showRealtimeFactorDialog" class="modal-backdrop" @click.self="closeRealtimeFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>实时因子（最多2个）</span>
          </div>
          <div class="factor-picker modal-check-list">
            <div v-for="factor in enabledCustomFactors" :key="factor.id" class="factor-option-row">
              <label class="check-row">
                <input
                  v-model="realtimeSelectedFactors"
                  type="checkbox"
                  :value="customFactorKey(factor.id)"
                  :disabled="!realtimeSelectedFactors.includes(customFactorKey(factor.id)) && realtimeSelectedFactors.length >= 2"
                />
                {{ factor.name }}
              </label>
              <button
                v-if="realtimeSelectedFactors.includes(customFactorKey(factor.id))"
                class="ghost param-button"
                type="button"
                @click="openResearchParamDialog(customFactorKey(factor.id))"
              >
                参数配置
              </button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="ghost" @click="closeRealtimeFactorDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="showResearchFactorDialog" class="modal-backdrop" @click.self="closeResearchFactorDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Code2 :size="17" />
            <span>因子指标</span>
          </div>
          <div class="factor-picker modal-check-list">
            <div v-for="factor in enabledCustomFactors" :key="factor.id" class="factor-option-row">
              <label class="check-row">
                <input v-model="selectedFactors" type="checkbox" :value="customFactorKey(factor.id)" />
                {{ factor.name }}
              </label>
              <button
                v-if="selectedFactors.includes(customFactorKey(factor.id))"
                class="ghost param-button"
                type="button"
                @click="openResearchParamDialog(customFactorKey(factor.id))"
              >
                参数配置
              </button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="ghost" @click="closeResearchFactorDialog">完成</button>
          </div>
        </section>
      </div>

      <div v-if="activeParamDialog" class="modal-backdrop" @click.self="closeSimpleParamDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <BarChart3 :size="17" />
            <span>{{ simpleParamTitle() }}</span>
          </div>
          <label v-if="activeParamDialog === 'ma'">
            周期
            <input v-model.number="maPeriod" type="number" min="1" max="240" />
          </label>
          <label v-if="activeParamDialog === 'ema'">
            周期
            <input v-model.number="emaPeriod" type="number" min="1" max="240" />
          </label>
          <template v-if="activeParamDialog === 'boll'">
            <label>
              周期
              <input v-model.number="bollingerPeriod" type="number" min="1" max="240" />
            </label>
            <label>
              倍数
              <input v-model.number="bollingerMultiplier" type="number" min="0.1" max="10" step="0.1" />
            </label>
          </template>
          <div class="modal-actions">
            <button class="ghost" @click="closeSimpleParamDialog">完成</button>
          </div>
        </section>
      </div>
</template>

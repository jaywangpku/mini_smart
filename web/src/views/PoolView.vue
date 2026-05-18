<script setup lang="ts">
import { Activity, BarChart3, Code2, Database, Edit3, Play, Plus, RefreshCw, Save, Search, Trash2 } from lucide-vue-next
import CodeEditor from ../components/CodeEditor.vue
import KlineChart from ../components/KlineChart.vue
import StrategyResultPanel from ../components/StrategyResultPanel.vue
import { useAppBindings } from ../appContext

const { activeTab, navCollapsed, pools, selectedPoolId, poolSymbols, customFactors, customStrategies, tasks, candles, historyCandles, historyFitKey, factors, selectedSymbols, researchSymbol, showNewPoolDialog, showEditPoolDialog, newPoolDraft, editPoolDraft, newSymbol, newSymbolName, securityMarket, securityQuery, securityResults, selectedSecurity, searchingSecurities, period, adjustType, syncMode, start, end, selectedFactors, selectedCustomFactorId, showNewFactorDialog, showEditFactorDialog, showParamDialog, showResearchParamDialog, showRealtimeIndicatorDialog, showRealtimeFactorDialog, showResearchFactorDialog, editingResearchParamKey, activeParamDialog, newFactorDraft, editFactorDraft, customFactorForm, customFactorPreview, customPreviewCandles, customPreviewFactors, customPreviewFitKey, customPreviewSymbol, customPreviewPoolId, customPreviewPoolSymbols, customPreviewPeriod, customPreviewAdjustType, customPreviewLimit, customFactorParamText, selectedCustomStrategyId, showNewStrategyDialog, showEditStrategyDialog, showStrategyParamDialog, showResearchStrategyParamDialog, newStrategyDraft, editStrategyDraft, customStrategyForm, strategyPreviewPoolId, strategyPreviewPoolSymbols, strategyPreviewSymbol, strategyPreviewPeriod, strategyPreviewAdjustType, strategyPreviewLimit, strategyPreviewInitialCash, strategyPreviewFeeRate, strategyPreviewSlippageRate, strategyPreviewCandles, strategyPreviewResult, strategyPreviewFitKey, showStrategyPreviewEquity, strategyResearchStrategyId, strategyResearchParams, strategyResearchCandles, strategyResearchResult, strategyResearchFitKey, showStrategyResearchEquity, realtimeSelectedFactors, realtimeStrategyId, realtimeStrategyParams, realtimeCandles, realtimeFactors, realtimeStrategyResult, realtimeFitKey, realtimeWarmupBars, realtimePollInterval, realtimeStatus, realtimeSource, realtimeUpdatedAt, realtimeWarning, realtimeConnected, realtimeSubscriptionId, realtimeSince, showRealtimeEquity, showRealtimeStrategyParamDialog, strategyInitialCash, strategyFeeRate, strategySlippageRate, strategyResearchStart, strategyResearchEnd, showVwap, showMa, showEma, showBollinger, maPeriod, emaPeriod, bollingerPeriod, bollingerMultiplier, visibleCandleCount, chartFitKey, loadingOlder, reachedHistoryStart, loadingOlderHistory, reachedHistoryStartForHistory, loading, message, error, selectedPool, enabledPoolSymbols, hasRunningTask, enabledCustomFactors, selectedCustomFactor, enabledCustomStrategies, selectedCustomStrategy, selectedResearchStrategy, selectedRealtimeStrategy, previewFactorKey, previewFactorSeries, selectedCustomFactors, factorSeriesMeta, setError, showToast, loadPools, loadPoolSymbols, loadCustomFactors, loadCustomStrategies, loadTasks, loadChart, loadHistoryChart, loadOlderChartData, loadOlderHistoryChartData, loadFactorValues, bootstrap, customFactorKey, customFactorIdFromKey, customFactorColor, prettyJson, parseJsonObject, selectCustomFactor, selectCustomStrategy, resetCustomStrategyForm, openNewCustomStrategyDialog, closeNewCustomStrategyDialog, openEditCustomStrategyDialog, closeEditCustomStrategyDialog, openStrategyParamDialog, closeStrategyParamDialog, openResearchStrategyParamDialog, closeResearchStrategyParamDialog, openRealtimeStrategyParamDialog, closeRealtimeStrategyParamDialog, openNewCustomFactorDialog, closeNewCustomFactorDialog, openEditCustomFactorDialog, closeEditCustomFactorDialog, openParamDialog, closeParamDialog, openResearchParamDialog, closeResearchParamDialog, openRealtimeIndicatorDialog, closeRealtimeIndicatorDialog, openRealtimeFactorDialog, closeRealtimeFactorDialog, openResearchFactorDialog, closeResearchFactorDialog, openSimpleParamDialog, closeSimpleParamDialog, simpleParamTitle, researchParamLabel, compactJson, resetCustomFactorForm, createCustomFactorFromDialog, saveCustomFactor, saveCustomFactorMeta, removeCustomFactor, runCustomFactorPreview, createCustomStrategyFromDialog, saveCustomStrategy, saveCustomStrategyMeta, removeCustomStrategy, strategyRunPayload, runCustomStrategyPreview, runStrategyResearch, realtimePayload, applyRealtimeSnapshot, mergeStrategySignals, pullRealtimeUpdates, scheduleRealtimePolling, startRealtime, stopRealtime, refreshRealtime, openNewPoolDialog, closeNewPoolDialog, openEditPoolDialog, closeEditPoolDialog, handleCreatePool, handleUpdatePool, handleDeletePool, handleAddPoolSymbol, handleSearchSecurities, selectSecurity, addSelectedSecurity, savePoolSymbolName, togglePoolSymbol, deletePoolSymbol, toggleSelectedSymbol, selectAllEnabled, symbolLabel, taskSymbolLabel, submitSelectedSync, submitPoolSync, formatMoney, formatPct } = useAppBindings()
</script>

<template>
      <section v-if="activeTab === 'pools'" class="tab-grid">
      <aside class="panel">
        <div class="panel-title">
          <Database :size="17" />
          <span>股票池</span>
        </div>
        <button class="submit secondary" @click="openNewPoolDialog">
          <Plus :size="17" />
          <span>新建股票池</span>
        </button>
        <div class="pool-card-list">
          <button
            v-for="pool in pools"
            :key="pool.id"
            :class="{ selected: selectedPoolId === pool.id }"
            type="button"
            @click="selectedPoolId = pool.id"
          >
            <strong>{{ pool.name }}</strong>
            <span>{{ pool.symbol_count || 0 }} 只股票</span>
            <small v-if="pool.description">{{ pool.description }}</small>
          </button>
        </div>
        <div class="factor-side-actions">
          <div class="sync-actions">
            <button class="submit secondary" title="修改股票池" @click="openEditPoolDialog">
              <Edit3 :size="17" />
            </button>
            <button class="submit danger" title="删除股票池" :disabled="selectedPoolId === 'default'" @click="handleDeletePool">
              <Trash2 :size="17" />
            </button>
          </div>
        </div>
      </aside>

      <div v-if="showNewPoolDialog" class="modal-backdrop" @click.self="closeNewPoolDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Database :size="17" />
            <span>新建股票池</span>
          </div>
          <label>
            股票池名称
            <input v-model="newPoolDraft.name" placeholder="例如：杠杆ETF研究池" @keyup.enter="handleCreatePool" />
          </label>
          <label>
            描述
            <textarea v-model="newPoolDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeNewPoolDialog">取消</button>
            <button class="submit compact" @click="handleCreatePool">
              <Plus :size="16" />
              <span>创建</span>
            </button>
          </div>
        </section>
      </div>

      <div v-if="showEditPoolDialog" class="modal-backdrop" @click.self="closeEditPoolDialog">
        <section class="modal-panel">
          <div class="panel-title">
            <Database :size="17" />
            <span>修改股票池</span>
          </div>
          <label>
            股票池名称
            <input v-model="editPoolDraft.name" placeholder="股票池名称" @keyup.enter="handleUpdatePool" />
          </label>
          <label>
            描述
            <textarea v-model="editPoolDraft.description" placeholder="可选"></textarea>
          </label>
          <div class="modal-actions">
            <button class="ghost" @click="closeEditPoolDialog">取消</button>
            <button class="submit compact" @click="handleUpdatePool">
              <Save :size="16" />
              <span>保存</span>
            </button>
          </div>
        </section>
      </div>

      <section class="main-panel">
        <div class="chart-head">
          <div>
            <h2>{{ selectedPool?.name || '股票池' }}</h2>
            <p>{{ poolSymbols.length }} 只股票，{{ enabledPoolSymbols.length }} 只启用</p>
          </div>
        </div>
        <div class="security-search">
          <div class="security-search-bar">
            <select v-model="securityMarket" title="市场">
              <option value="US">美股</option>
              <option value="HK">港股</option>
              <option value="CN">A股</option>
              <option value="SG">新加坡</option>
            </select>
            <input v-model="securityQuery" placeholder="搜索股票代码或名称，例如 MSTU / MicroStrategy" @keyup.enter="handleSearchSecurities" />
            <button class="submit secondary compact" :disabled="searchingSecurities" @click="handleSearchSecurities">
              <Search :size="16" />
              <span>{{ searchingSecurities ? '查询中' : '查询' }}</span>
            </button>
          </div>
          <div v-if="securityResults.length" class="security-results">
            <button
              v-for="row in securityResults"
              :key="row.symbol"
              :class="{ selected: selectedSecurity?.symbol === row.symbol }"
              type="button"
              @click="selectSecurity(row)"
            >
              <strong>{{ row.symbol }}</strong>
              <span>{{ row.name || row.name_cn || row.name_hk || row.name_en || '-' }}</span>
              <small>{{ row.market || securityMarket }}</small>
            </button>
          </div>
          <div v-if="selectedSecurity" class="security-info">
            <div>
              <strong>{{ selectedSecurity.symbol }}</strong>
              <span>{{ selectedSecurity.name || selectedSecurity.name_cn || selectedSecurity.name_hk || selectedSecurity.name_en || '-' }}</span>
            </div>
            <dl>
              <div><dt>交易所</dt><dd>{{ selectedSecurity.exchange || '-' }}</dd></div>
              <div><dt>币种</dt><dd>{{ selectedSecurity.currency || '-' }}</dd></div>
              <div><dt>每手</dt><dd>{{ selectedSecurity.lot_size || '-' }}</dd></div>
              <div><dt>EPS</dt><dd>{{ selectedSecurity.eps_ttm ?? selectedSecurity.eps ?? '-' }}</dd></div>
              <div><dt>BPS</dt><dd>{{ selectedSecurity.bps ?? '-' }}</dd></div>
              <div><dt>股息率</dt><dd>{{ selectedSecurity.dividend_yield ?? '-' }}</dd></div>
            </dl>
            <button class="submit compact" @click="addSelectedSecurity">
              <Plus :size="16" />
              <span>加入股票池</span>
            </button>
          </div>
          <details class="manual-add">
            <summary>手动添加</summary>
            <div class="add-symbol-row">
              <input v-model="newSymbol" placeholder="MSTU.US" @keyup.enter="handleAddPoolSymbol" />
              <input v-model="newSymbolName" placeholder="股票名称，例如 MicroStrategy" @keyup.enter="handleAddPoolSymbol" />
              <button class="icon-button primary" title="加入股票池" @click="handleAddPoolSymbol">
                <Plus :size="18" />
              </button>
            </div>
          </details>
        </div>
        <div class="pool-table">
          <div class="pool-row header">
            <span>股票</span>
            <span>名称</span>
            <span>启用</span>
            <span>操作</span>
          </div>
          <div v-for="row in poolSymbols" :key="row.symbol" class="pool-row">
            <span>{{ row.symbol }}</span>
            <input v-model="row.name" class="name-input" placeholder="股票名称" @keyup.enter="savePoolSymbolName(row)" />
            <input type="checkbox" :checked="Boolean(row.enabled)" @change="togglePoolSymbol(row)" />
            <button class="icon-button" title="保存名称" @click="savePoolSymbolName(row)">
              <Save :size="16" />
            </button>
            <button class="icon-button danger" title="移除" @click="deletePoolSymbol(row)">
              <Trash2 :size="16" />
            </button>
          </div>
        </div>
      </section>
      </section>
</template>

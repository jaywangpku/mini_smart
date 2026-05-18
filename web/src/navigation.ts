import { Activity, BarChart3, Code2, Database, Play } from 'lucide-vue-next'

export type TabName = 'pools' | 'sync' | 'history' | 'realtime' | 'research' | 'customFactors' | 'strategyResearch' | 'customStrategies'

export const tabs: Array<{ id: TabName; label: string; icon: unknown }> = [
  { id: 'pools', label: '股票池管理', icon: Database },
  { id: 'sync', label: '数据同步', icon: Play },
  { id: 'history', label: '历史看板', icon: BarChart3 },
  { id: 'realtime', label: '实时看板', icon: Activity },
  { id: 'customFactors', label: '自定义因子', icon: Code2 },
  { id: 'research', label: '因子研究', icon: BarChart3 },
  { id: 'customStrategies', label: '自定义策略', icon: Code2 },
  { id: 'strategyResearch', label: '策略研究', icon: BarChart3 }
]

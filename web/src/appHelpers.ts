export function chartLimitForPeriod(value: string) {
  if (value === 'day') return 500
  if (value === '60min') return 1000
  if (value === '30min') return 1200
  return 2000
}

export function mergeByTime<T extends { time: number }>(current: T[], incoming: T[]) {
  const byTime = new Map<number, T>()
  for (const item of current) byTime.set(item.time, item)
  for (const item of incoming) byTime.set(item.time, item)
  return [...byTime.values()].sort((a, b) => a.time - b.time)
}

export function customFactorKey(id: string) {
  return `custom:${id}`
}

export function customFactorIdFromKey(key: string) {
  return key.replace(/^custom:/, '')
}

export function customFactorColor(index: number) {
  return ['#a78bfa', '#22c55e', '#facc15', '#fb7185', '#2dd4bf', '#c084fc'][index % 6]
}

export function prettyJson(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw || '{}'), null, 2)
  } catch {
    return raw || '{}'
  }
}

export function parseJsonObject(raw: string) {
  const value = JSON.parse(raw || '{}')
  if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error('参数必须是 JSON object')
  return value as Record<string, unknown>
}

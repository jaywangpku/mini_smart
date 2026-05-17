export function localDateString(date = new Date()) {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function dateStartTs(value: string) {
  if (!value) return undefined
  const timestamp = new Date(`${value}T00:00:00`).getTime()
  return Number.isFinite(timestamp) ? Math.floor(timestamp / 1000) : undefined
}

export function dateEndTs(value: string) {
  if (!value) return undefined
  const timestamp = new Date(`${value}T23:59:59`).getTime()
  return Number.isFinite(timestamp) ? Math.floor(timestamp / 1000) : undefined
}

export function dateRange(startValue: string, endValue: string) {
  return {
    start: dateStartTs(startValue),
    end: dateEndTs(endValue)
  }
}

export function formatPct(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return `${(value * 100).toFixed(2)}%`
}

export function formatMoney(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return value.toFixed(2)
}

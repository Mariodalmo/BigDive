import dayjs from 'dayjs'
import 'dayjs/locale/it'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.locale('it')
dayjs.tz.setDefault('Europe/Rome')

export const now = () => dayjs().tz().toISOString()
export const addDaysISO = (iso: string, days: number) => dayjs(iso).add(days, 'day').toISOString()
export const daysUntil = (iso: string) => dayjs(iso).diff(dayjs(), 'day')
export const formatIT = (iso: string) => dayjs(iso).format('DD/MM/YYYY')
export const uuid = () => crypto.randomUUID()

export const exportCSV = (rows: Record<string, any>[], filename: string) => {
  if (!rows.length) return
  const colsSet: Set<string> = rows.reduce<Set<string>>((s, r) => {
    Object.keys(r).forEach(k => s.add(k))
    return s
  }, new Set<string>())
  const cols = Array.from(colsSet)
  const esc = (v: any) => JSON.stringify(v ?? '')
  const csv = [cols.join(','), ...rows.map(r => cols.map(c => esc(r[c])).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
}

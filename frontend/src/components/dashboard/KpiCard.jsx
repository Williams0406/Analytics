'use client'

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const formatValue = (value, unit) => {
  const num = parseFloat(value)
  if (unit === '$') {
    return num >= 1000
      ? `$${(num / 1000).toFixed(1)}k`
      : `$${num.toFixed(0)}`
  }
  if (unit === '%') return `${num.toFixed(1)}%`
  return num >= 1000 ? `${(num / 1000).toFixed(1)}k` : `${num.toFixed(0)}`
}

export default function KpiCard({ label, value, change_percent, unit, trend, loading }) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-2xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
        <div className="mb-4 h-3 w-24 rounded bg-[var(--surface-muted)]" />
        <div className="mb-3 h-8 w-32 rounded bg-[var(--surface-muted)]" />
        <div className="h-3 w-20 rounded bg-[var(--surface-muted)]" />
      </div>
    )
  }

  const isPositive = trend === 'up'
  const isNegative = trend === 'down'
  const absChange = Math.abs(parseFloat(change_percent || 0)).toFixed(1)

  return (
    <div className="group rounded-2xl border border-[var(--border)] bg-white p-5 transition-all hover:border-[var(--border-strong)] hover:shadow-[0_20px_48px_rgba(15,23,42,0.08)]">
      <div className="mb-3 flex items-start justify-between">
        <p className="text-sm text-[var(--text-secondary)]">{label}</p>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
            isPositive
              ? 'border border-[#dcebe6] bg-[#eef8f3] text-[#2f855a]'
              : isNegative
              ? 'border border-red-200 bg-red-50 text-red-700'
              : 'border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)]'
          }`}
        >
          {isPositive && <TrendingUp size={11} />}
          {isNegative && <TrendingDown size={11} />}
          {!isPositive && !isNegative && <Minus size={11} />}
          {absChange}%
        </span>
      </div>

      <p className="mb-1 text-3xl font-bold text-[var(--text-primary)]">{formatValue(value, unit)}</p>

      <p className="text-xs text-[var(--text-muted)]">vs. mes anterior</p>
    </div>
  )
}

'use client'

import { Card, CardContent } from '@/components/ui/Card'
import Skeleton from '@/components/ui/Skeleton'

const formatValue = (value, unit) => {
  const num = Number(value || 0)
  if (unit === '%') return `${num.toFixed(1)}%`
  if (unit === '$') return num >= 1000 ? `$${(num / 1000).toFixed(1)}k` : `$${num.toFixed(0)}`
  return num >= 1000 ? `${(num / 1000).toFixed(1)}k` : `${num.toLocaleString()}`
}

export default function DatasetStatCard({ label, value, unit = '#', caption = '', loading }) {
  if (loading) {
    return (
      <Card className="shadow-[var(--shadow-sm)]">
        <CardContent className="space-y-3 px-5 py-5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-3 w-32" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="transition-all duration-[var(--motion-fast)] hover:-translate-y-0.5 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]">
      <CardContent className="px-5 py-5">
        <p className="mb-3 text-[11px] uppercase tracking-[0.22em] text-[var(--text-muted)]">{label}</p>
        <p className="font-mono text-3xl font-semibold text-[var(--text-primary)]">{formatValue(value, unit)}</p>
        <p className="mt-2 text-xs text-[var(--text-secondary)]">{caption}</p>
      </CardContent>
    </Card>
  )
}

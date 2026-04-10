'use client'

import Badge from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'

export default function InsightCard({ insight }) {
  const priorityConfig = {
    high: { label: 'Alta', variant: 'danger' },
    medium: { label: 'Media', variant: 'warning' },
    low: { label: 'Baja', variant: 'neutral' },
  }

  const typeLabels = {
    summary: 'Resumen',
    anomaly: 'Anomalia',
    trend: 'Tendencia',
    recommendation: 'Recomendacion',
    forecast: 'Forecast',
  }

  const priority = priorityConfig[insight.priority] || priorityConfig.medium

  return (
    <Card
      className={`transition-all duration-[var(--motion-fast)] hover:-translate-y-0.5 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)] ${
        insight.is_read ? 'opacity-80' : ''
      }`}
    >
      <CardContent className="px-5 py-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <span className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
            {typeLabels[insight.insight_type] || insight.insight_type_display}
          </span>
          <Badge variant={priority.variant}>{priority.label}</Badge>
        </div>

        <h3 className="mb-2 text-sm font-semibold leading-snug text-[var(--text-primary)]">
          {insight.title}
        </h3>

        <p className="line-clamp-4 text-xs leading-relaxed text-[var(--text-secondary)]">
          {insight.content}
        </p>

        <p className="mt-4 text-xs text-[var(--text-muted)]">
          {new Date(insight.created_at).toLocaleString('es-PE')}
        </p>
      </CardContent>
    </Card>
  )
}

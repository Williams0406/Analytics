'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  CHART_AXIS,
  CHART_COLORS,
  CHART_GRID,
  CHART_TOOLTIP_STYLE,
  getChartColor,
} from '@/lib/chartTheme'

function TooltipCard({ active, payload, label }) {
  if (!active || !payload?.length) return null

  return (
    <div style={CHART_TOOLTIP_STYLE} className="rounded-2xl p-3 text-xs">
      <p className="text-slate-300 mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-3 text-slate-200 mb-1">
          <span>{entry.name}</span>
          <span className="text-white font-semibold">{Number(entry.value).toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

export default function InsightBarChart({
  title,
  subtitle,
  data = [],
  valueLabel = 'valor',
  secondaryLabel = 'secundario',
  color = '#3258ff',
  secondaryColor = '#0ea5a4',
}) {
  const hasSecondary = data.some((item) => item.secondary_value !== undefined && item.secondary_value !== null)

  return (
    <div className="rounded-[32px] border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
      <div className="mb-5">
        <h3 className="text-[var(--text-primary)] font-semibold text-sm">{title}</h3>
        {subtitle && <p className="text-[var(--text-secondary)] text-xs mt-1">{subtitle}</p>}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 0, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: CHART_AXIS, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: CHART_AXIS, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<TooltipCard />} />
          <Legend wrapperStyle={{ fontSize: '12px', color: CHART_AXIS, paddingTop: '12px' }} />
          <Bar
            dataKey="value"
            name={valueLabel}
            fill={color}
            radius={[10, 10, 0, 0]}
            maxBarSize={42}
          >
            {!hasSecondary && data.map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={getChartColor(index)} />
            ))}
          </Bar>
          {hasSecondary && (
            <Bar
              dataKey="secondary_value"
              name={secondaryLabel}
              fill={secondaryColor}
              radius={[10, 10, 0, 0]}
              maxBarSize={42}
            />
          )}
        </BarChart>
      </ResponsiveContainer>

      {!hasSecondary && data.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {data.slice(0, 6).map((item, index) => (
            <div key={`${item.label}-legend`} className="inline-flex items-center gap-2 rounded-full bg-[var(--surface-muted)] px-3 py-1.5 text-[11px] text-[var(--text-secondary)]">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
              />
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

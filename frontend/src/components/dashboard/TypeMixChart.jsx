'use client'

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import { CHART_COLORS, CHART_TOOLTIP_STYLE } from '@/lib/chartTheme'

export default function TypeMixChart({ title, data = [] }) {
  return (
    <div className="rounded-[32px] border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
      <div className="mb-5">
        <h3 className="text-[var(--text-primary)] font-semibold text-sm">{title}</h3>
        <p className="text-[var(--text-secondary)] text-xs mt-1">Como esta compuesto el modelo de datos</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)] gap-4 items-center">
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="label"
                innerRadius={58}
                outerRadius={82}
                paddingAngle={3}
              >
                {data.map((entry, index) => (
                  <Cell key={entry.label} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={item.label} className="flex items-center justify-between gap-4 rounded-2xl bg-[var(--surface-muted)] border border-[var(--border)] px-4 py-3">
              <div className="flex items-center gap-3">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                />
                <span className="text-[var(--text-secondary)] text-sm">{item.label}</span>
              </div>
              <span className="text-[var(--text-primary)] text-sm font-semibold">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

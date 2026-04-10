'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

import { CHART_AXIS, CHART_GRID, CHART_TOOLTIP_STYLE } from '@/lib/chartTheme'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={CHART_TOOLTIP_STYLE} className="rounded-xl p-3 text-xs shadow-xl">
      <p className="mb-2 font-medium text-slate-300">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="mb-1 flex items-center gap-2">
          <div className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="capitalize text-slate-300">{entry.name}:</span>
          <span className="font-semibold text-white">${Number(entry.value).toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

export default function RevenueChart({ data, loading }) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-2xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
        <div className="mb-6 h-4 w-40 rounded bg-[var(--surface-muted)]" />
        <div className="h-56 rounded-xl bg-[var(--surface-muted)]" />
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Revenue vs Gastos</h3>
          <p className="mt-0.5 text-xs text-[var(--text-secondary)]">Ultimos 8 meses</p>
        </div>
        <span className="rounded-full border border-[#d7dcff] bg-[#eef1ff] px-2.5 py-1 text-xs text-[#3258ff]">
          Demo Data
        </span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3258ff" stopOpacity={0.28} />
              <stop offset="95%" stopColor="#3258ff" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5a4" stopOpacity={0.28} />
              <stop offset="95%" stopColor="#0ea5a4" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
          <XAxis
            dataKey="month_label"
            tick={{ fill: CHART_AXIS, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: CHART_AXIS, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: '12px', color: CHART_AXIS, paddingTop: '12px' }} />
          <Area
            type="monotone"
            dataKey="revenue"
            name="Revenue"
            stroke="#3258ff"
            strokeWidth={2}
            fill="url(#colorRevenue)"
          />
          <Area
            type="monotone"
            dataKey="profit"
            name="Profit"
            stroke="#0ea5a4"
            strokeWidth={2}
            fill="url(#colorProfit)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

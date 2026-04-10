'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Sankey,
  Scatter,
  ScatterChart,
  Tooltip,
  Treemap,
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
import {
  SlideCanvas,
  buildCategoryAxisProps,
  clampTextStyle,
  getNarrativePanels,
} from '@/components/analytics/slideSystem'

function formatValue(value) {
  if (typeof value === 'number') {
    return value.toLocaleString()
  }

  return value || '0'
}

function getSemanticColor(signal, fallbackIndex = 0) {
  if (signal === 'positive') return '#2f855a'
  if (signal === 'negative') return '#f46d43'
  if (signal === 'neutral') return '#3258ff'
  return getChartColor(fallbackIndex)
}

function renderReferenceLines(slide, axisKey = 'y') {
  const acceptedAxes =
    axisKey === 'x' && slide.orientation === 'horizontal'
      ? new Set(['x', 'y'])
      : new Set([axisKey])

  return (slide.reference_lines || [])
    .filter((reference) => reference.kind === 'constant' && acceptedAxes.has(reference.axis))
    .map((reference) => (
      <ReferenceLine
        key={`${reference.label}-${reference.value}`}
        {...(axisKey === 'x' ? { x: reference.value } : { y: reference.value })}
        stroke="#111827"
        strokeDasharray="4 4"
        strokeOpacity={0.55}
        label={{ value: reference.label, position: 'insideTopRight', fill: CHART_AXIS, fontSize: 11 }}
      />
    ))
}

function renderAnnotations(slide) {
  return (slide.annotations || []).map((annotation, index) => (
    <ReferenceDot
      key={`${annotation.type}-${annotation.x}-${annotation.y}-${index}`}
      x={annotation.x}
      y={annotation.y}
      r={5}
      fill="#111827"
      stroke="#ffffff"
      strokeWidth={2}
      label={{ value: annotation.label, position: 'top', fill: CHART_AXIS, fontSize: 11 }}
    />
  ))
}

function SlideFrame({ children, slideIndex = 0, totalSlides = 1, stage = 'Data Story' }) {
  return (
    <SlideCanvas stage={stage} slideIndex={slideIndex} totalSlides={totalSlides} contentClassName="grid h-full min-h-0">
      {children}
    </SlideCanvas>
  )
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  return (
    <div style={CHART_TOOLTIP_STYLE} className="rounded-2xl p-3 text-xs">
      {label !== undefined && label !== null ? (
        <p className="mb-2 text-slate-300">{label}</p>
      ) : null}
      {payload.map((entry, index) => (
        <div
          key={`${entry.dataKey || entry.name}-${index}`}
          className="mb-1 flex justify-between gap-3 text-slate-200"
        >
          <span>{entry.name || entry.dataKey}</span>
          <span className="font-semibold text-white">{formatValue(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

function ScatterTooltip({ active, payload, slide }) {
  if (!active || !payload?.length) return null

  const point = payload[0]?.payload || {}
  return (
    <div style={CHART_TOOLTIP_STYLE} className="rounded-2xl p-3 text-xs">
      <div className="mb-1 flex justify-between gap-3 text-slate-200">
        <span>{slide.x_label}</span>
        <span className="font-semibold text-white">{formatValue(point.x)}</span>
      </div>
      <div className="flex justify-between gap-3 text-slate-200">
        <span>{slide.y_label}</span>
        <span className="font-semibold text-white">{formatValue(point.y)}</span>
      </div>
    </div>
  )
}

function SlideHeader({ slide, chartsCount = 1 }) {
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <span className="inline-flex rounded-full bg-[rgba(50,88,255,0.08)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--accent-indigo)]">
          {slide.stage || 'Data Story'}
        </span>
        <span className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
          {chartsCount > 1 ? `${chartsCount} visuales conectados` : 'Visual principal'}
        </span>
      </div>
      <h3 className="max-w-5xl text-[34px] font-semibold leading-tight text-[var(--text-primary)]">
        {slide.question || slide.title}
      </h3>
      <p className="mt-2 max-w-4xl text-sm leading-6 text-[var(--text-secondary)]" style={clampTextStyle(3)}>
        {slide.title !== slide.question ? `${slide.title}. ` : ''}
        {slide.subtitle}
      </p>
    </div>
  )
}

function StoryCard({ title, body, tone = 'light' }) {
  const tones = {
    light: 'border-[var(--border)] bg-white',
    dark: 'border-slate-900/10 bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] text-white',
    accent: 'border-[rgba(50,88,255,0.18)] bg-[rgba(50,88,255,0.06)]',
  }

  return (
    <div className={`rounded-[24px] border p-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)] ${tones[tone] || tones.light}`}>
      <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${tone === 'dark' ? 'text-slate-400' : 'text-[var(--text-muted)]'}`}>
        {title}
      </p>
      <p
        className={`mt-3 text-sm leading-6 ${tone === 'dark' ? 'text-slate-100' : 'text-[var(--text-primary)]'}`}
        style={clampTextStyle(4)}
      >
        {body}
      </p>
    </div>
  )
}

function blockTitle(block) {
  const titles = {
    kpi_badge: 'KPI',
    finding: 'Hallazgo',
    complication: 'Complicacion',
    conclusion: 'Conclusion',
    action: 'Accion',
    evidence: 'Evidencia',
    warning: 'Alerta',
  }

  return titles[block.role] || 'Insight'
}

function TextBlockCard({ block }) {
  const color = getSemanticColor(block.color_signal)
  const stripeColor =
    block.color_signal === 'warning'
      ? '212,167,44'
      : block.color_signal === 'negative'
        ? '244,109,67'
        : block.color_signal === 'positive'
          ? '47,133,90'
          : '50,88,255'
  const sizeClass = block.size === 'large'
    ? 'p-5'
    : block.size === 'small'
      ? 'p-3'
      : 'p-4'

  return (
    <div
      className={`rounded-[24px] border bg-white shadow-[0_16px_36px_rgba(15,23,42,0.05)] ${sizeClass}`}
      style={{
        borderColor: `rgba(${stripeColor}, 0.18)`,
        boxShadow: `inset 3px 0 0 ${color}`,
      }}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
        {blockTitle(block)}
      </p>
      {block.value ? (
        <div className="mt-3">
          <p className={`font-semibold text-[var(--text-primary)] ${block.role === 'kpi_badge' ? 'text-3xl' : 'text-xl'}`}>
            {block.value}
          </p>
          {block.label ? (
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">
              {block.label}
            </p>
          ) : null}
        </div>
      ) : null}
      {block.content ? (
        <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">{block.content}</p>
      ) : null}
    </div>
  )
}

function groupTextBlocks(blocks = []) {
  return blocks.reduce((accumulator, block) => {
    const key = block.position || 'bottom-left'
    if (!accumulator[key]) {
      accumulator[key] = []
    }
    accumulator[key].push(block)
    return accumulator
  }, {})
}

function NarrativeSidebar({ slide, slideIndex, totalSlides, charts = [] }) {
  const hasStructuredBlocks = Array.isArray(slide.text_blocks) && slide.text_blocks.length > 0
  const panels = hasStructuredBlocks ? [] : getNarrativePanels(slide, slide.confidence ? 2 : 3)

  return (
    <aside className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-4">
      <div className="rounded-[24px] border border-[var(--border)] bg-white/85 px-4 py-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
        <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">Slide</p>
            <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
            {String(slideIndex + 1).padStart(2, '0')} / {String(totalSlides).padStart(2, '0')}
          </p>
        </div>
        {slide.signal_value !== undefined ? (
          <div className="text-right">
              <p className="text-[28px] font-semibold leading-none text-[var(--text-primary)]">{slide.signal_value}</p>
            <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
              {slide.signal_label || 'signal'}
            </p>
          </div>
        ) : null}
      </div>
        {slide.confidence ? (
          <div className="mt-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">Confianza</p>
                <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
                  {slide.confidence.level} / {slide.confidence.score}/100
                </p>
              </div>
              <span
                className="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-white"
                style={{
                  backgroundColor:
                    slide.confidence.level === 'alta'
                      ? '#2f855a'
                      : slide.confidence.level === 'media'
                        ? '#d4a72c'
                        : '#f46d43',
                }}
              >
                {slide.confidence.level}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]" style={clampTextStyle(2)}>
              {slide.confidence.caveat}
            </p>
          </div>
        ) : null}
      </div>

      <div className="space-y-4 overflow-hidden">
        {panels.map((panel, index) => (
          <StoryCard key={`${panel.title}-${index}`} title={panel.title} body={panel.body} tone={panel.tone} />
        ))}
      </div>
    </aside>
  )
}

function ChartViewport({ children, className = '' }) {
  return <div className={`h-full min-h-0 w-full ${className}`}>{children}</div>
}

function HeatmapCell({ value }) {
  const intensity = Math.min(Math.abs(value || 0), 1)
  const hue = value >= 0 ? '14,165,164' : '244,109,67'
  const background = `rgba(${hue}, ${0.12 + intensity * 0.38})`

  return (
    <div
      className="flex h-14 items-center justify-center rounded-2xl border border-[var(--border)] text-xs font-semibold text-[var(--text-primary)]"
      style={{ background }}
    >
      {Number(value || 0).toFixed(2)}
    </div>
  )
}

function HeatmapChartSlide({ slide }) {
  const cellLookup = new Map((slide.data || []).map((cell) => [`${cell.y}::${cell.x}`, cell.value]))
  const values = (slide.data || []).map((cell) => Number(cell.value) || 0)
  const minValue = values.length ? Math.min(...values) : 0
  const maxValue = values.length ? Math.max(...values) : 0

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] gap-3">
      <div className="grid grid-cols-[140px_minmax(0,1fr)] items-end gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
          Segmentos
        </div>
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
          Variables
        </div>
      </div>
      <div
        className="grid min-h-0 gap-2 overflow-hidden"
        style={{ gridTemplateColumns: `140px repeat(${(slide.x_labels || []).length}, minmax(0, 1fr))` }}
      >
        <div />
        {(slide.x_labels || []).map((label) => (
          <div
            key={label}
            className="text-center text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]"
            style={clampTextStyle(2)}
          >
            {label}
          </div>
        ))}

        {(slide.y_labels || []).map((rowLabel) => (
          <div key={rowLabel} className="contents">
            <div className="flex items-center text-sm text-[var(--text-secondary)]">{rowLabel}</div>
            {(slide.x_labels || []).map((columnLabel) => (
              <HeatmapCell
                key={`${rowLabel}-${columnLabel}`}
                value={cellLookup.get(`${rowLabel}::${columnLabel}`)}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-[160px_minmax(0,1fr)_100px] items-center gap-3 text-[11px] text-[var(--text-muted)]">
        <span className="font-semibold uppercase tracking-[0.18em]">Correlation Strength</span>
        <div className="h-2 rounded-full bg-[linear-gradient(90deg,#f46d43_0%,#fff4ef_18%,#f8fafc_50%,#e7fbf8_82%,#0ea5a4_100%)]" />
        <div className="flex items-center justify-between">
          <span>{minValue.toFixed(2)}</span>
          <span>{maxValue.toFixed(2)}</span>
        </div>
      </div>
    </div>
  )
}

function MapChartSlide({ slide }) {
  const maxValue = Math.max(...(slide.data || []).map((item) => Number(item.value) || 0), 1)

  return (
    <div className="grid h-full min-h-0 grid-cols-[minmax(0,1.35fr)_280px] gap-4">
      <div className="rounded-[28px] border border-[var(--border)] bg-[linear-gradient(180deg,#fdfefe_0%,#f5f8fc_100%)] p-4">
        <div className="aspect-[100/55] h-full min-h-0 w-full">
          <svg viewBox="0 0 100 55" preserveAspectRatio="xMidYMid meet" className="h-full w-full">
          <rect x="0" y="0" width="100" height="55" rx="6" fill="#f7fafc" />
          <path d="M7 10 C14 7, 20 8, 24 14 C22 18, 18 21, 16 25 C12 28, 10 24, 9 19 C6 16, 6 12, 7 10 Z" fill="#dbe5f0" />
          <path d="M26 22 C29 20, 33 20, 35 24 C35 29, 33 35, 31 42 C28 48, 25 43, 24 36 C25 31, 25 26, 26 22 Z" fill="#dbe5f0" />
          <path d="M43 10 C49 9, 58 10, 63 15 C60 19, 57 23, 55 27 C51 29, 47 26, 45 21 C43 18, 42 13, 43 10 Z" fill="#dbe5f0" />
          <path d="M54 24 C58 25, 61 28, 61 33 C60 39, 58 44, 55 47 C51 44, 50 38, 51 31 C51 28, 52 25, 54 24 Z" fill="#dbe5f0" />
          <path d="M64 12 C73 10, 84 12, 89 18 C89 24, 82 26, 78 29 C74 31, 70 33, 67 31 C64 28, 63 23, 63 18 C63 15, 63 13, 64 12 Z" fill="#dbe5f0" />
          <path d="M79 35 C83 34, 88 36, 90 40 C89 43, 86 46, 83 47 C80 46, 78 41, 79 35 Z" fill="#dbe5f0" />

          {(slide.data || []).map((point, index) => {
            const radius = 2.4 + ((Number(point.value) || 0) / maxValue) * 4.8
            const color = getChartColor(index)

            return (
              <g key={`${point.label}-${point.x}-${point.y}`}>
                <circle cx={point.x} cy={point.y} r={radius} fill={color} fillOpacity="0.18" />
                <circle cx={point.x} cy={point.y} r={Math.max(1.6, radius * 0.48)} fill={color} />
                <text x={point.x + 2.2} y={point.y - 1.8} fill="#16202b" fontSize="1.9">
                  {point.label}
                </text>
              </g>
            )
          })}
          </svg>
        </div>
      </div>

      <div className="grid min-h-0 auto-rows-fr gap-3">
        {(slide.data || []).map((item, index) => (
          <div
            key={`${item.label}-legend`}
            className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-white px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: getChartColor(index) }}
              />
              <span className="text-sm text-[var(--text-secondary)]">{item.label}</span>
            </div>
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {formatValue(item.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function RadarChartSlide({ slide }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={slide.data || []}>
        <PolarGrid stroke={CHART_GRID} />
        <PolarAngleAxis dataKey="metric" tick={{ fill: CHART_AXIS, fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: CHART_AXIS, fontSize: 10 }} />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: '12px', color: CHART_AXIS }} />
        {(slide.series || []).map((seriesName, index) => (
          <Radar
            key={seriesName}
            name={seriesName}
            dataKey={seriesName}
            stroke={CHART_COLORS[index % CHART_COLORS.length]}
            fill={CHART_COLORS[index % CHART_COLORS.length]}
            fillOpacity={0.14}
            strokeWidth={2}
          />
        ))}
      </RadarChart>
    </ResponsiveContainer>
  )
}

function ComboLikeSlide({ slide }) {
  const xAxisProps = buildCategoryAxisProps(slide.data || [], 'label', { maxVisible: 7, maxLength: 12 })

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={slide.data || []} margin={{ top: 0, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} {...xAxisProps} />
        <YAxis yAxisId="left" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: CHART_AXIS, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          domain={slide.secondary_domain || ['auto', 'auto']}
        />
        <Tooltip content={<ChartTooltip />} />
        {renderReferenceLines(slide)}
        <Legend wrapperStyle={{ fontSize: '12px', color: CHART_AXIS }} />
        <Bar
          yAxisId="left"
          dataKey="value"
          name={slide.value_label || 'valor'}
          radius={[12, 12, 0, 0]}
          maxBarSize={42}
        >
          {(slide.data || []).map((entry, index) => (
            <Cell key={`${entry.label}-${index}`} fill={getSemanticColor(entry.color_signal, index)} />
          ))}
        </Bar>
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="secondary_value"
          name={slide.secondary_label || 'referencia'}
          stroke="#111827"
          strokeWidth={3}
          dot={{ r: 4, fill: '#f46d43', stroke: '#ffffff', strokeWidth: 2 }}
          activeDot={{ r: 6, fill: '#0ea5a4', stroke: '#ffffff', strokeWidth: 2 }}
        />
        {(slide.reference_lines || []).some((reference) => reference.kind === 'series') ? (
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="reference_value"
            name="Tendencia"
            stroke="#111827"
            strokeDasharray="4 4"
            strokeWidth={2}
            dot={false}
          />
        ) : null}
        {renderAnnotations(slide)}
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function WaterfallLikeSlide({ slide }) {
  const chartData = []
  let cumulative = 0
  ;(slide.data || []).forEach((item) => {
    const delta = Number(item.value) || 0
    const start = cumulative
    cumulative += delta
    chartData.push({
      ...item,
      start,
      delta: Math.abs(delta),
      end: cumulative,
      color_signal: delta >= 0 ? 'positive' : 'negative',
    })
  })

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 0, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: CHART_AXIS, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          {...buildCategoryAxisProps(chartData, 'label', { maxVisible: 7, maxLength: 12 })}
        />
        <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} />
        <Bar dataKey="start" stackId="waterfall" fill="transparent" stroke="transparent" />
        <Bar dataKey="delta" stackId="waterfall" name={slide.value_label || 'delta'} radius={[8, 8, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`${entry.label}-${index}`} fill={getSemanticColor(entry.color_signal, index)} />
          ))}
        </Bar>
        {renderAnnotations({ ...slide, annotations: buildAnnotationsFromWaterfall(chartData, slide.annotations) })}
      </BarChart>
    </ResponsiveContainer>
  )
}

function buildAnnotationsFromWaterfall(chartData, annotations = []) {
  return annotations.map((annotation) => {
    const target = chartData.find((item) => item.label === annotation.x)
    if (!target) return annotation
    return {
      ...annotation,
      y: target.end,
    }
  })
}

function BulletLikeSlide({ slide }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={slide.data || []} layout="vertical" margin={{ top: 0, right: 16, left: 20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis type="number" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          tick={{ fill: CHART_AXIS, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={130}
          tickFormatter={(value) => buildCategoryAxisProps(slide.data || [], 'label', { maxLength: 16 }).tickFormatter(value)}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: '12px', color: CHART_AXIS }} />
        <Bar dataKey="secondary_value" name={slide.secondary_label || 'baseline'} fill="rgba(22,32,43,0.12)" radius={[0, 12, 12, 0]} maxBarSize={26} />
        <Bar dataKey="value" name={slide.value_label || 'valor'} radius={[0, 12, 12, 0]} maxBarSize={14}>
          {(slide.data || []).map((entry, index) => (
            <Cell key={`${entry.label}-${index}`} fill={getSemanticColor(entry.color_signal || entry.status, index)} />
          ))}
        </Bar>
        {renderAnnotations(slide)}
      </BarChart>
    </ResponsiveContainer>
  )
}

function SankeyChartSlide({ slide }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <Sankey
        data={slide.data}
        nodePadding={30}
        nodeWidth={14}
        iterations={64}
        margin={{ top: 12, right: 24, bottom: 12, left: 24 }}
      >
        <Tooltip content={<ChartTooltip />} />
      </Sankey>
    </ResponsiveContainer>
  )
}

function TreemapContent({ x, y, width, height, index, name, value }) {
  if (width <= 0 || height <= 0) return null

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx="14"
        fill={getChartColor(index)}
        fillOpacity="0.86"
        stroke="#ffffff"
        strokeWidth="3"
      />
      {width > 84 && height > 46 ? (
        <>
          <text x={x + 12} y={y + 22} fill="#ffffff" fontSize="12" fontWeight="600">
            {name}
          </text>
          <text x={x + 12} y={y + 40} fill="rgba(255,255,255,0.84)" fontSize="11">
            {formatValue(value)}
          </text>
        </>
      ) : null}
    </g>
  )
}

function TreemapChartSlide({ slide }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <Treemap
        data={slide.data || []}
        dataKey="value"
        nameKey="name"
        aspectRatio={4 / 3}
        stroke="#ffffff"
        content={<TreemapContent />}
      >
        <Tooltip content={<ChartTooltip />} />
      </Treemap>
    </ResponsiveContainer>
  )
}

function PieLikeSlide({ slide }) {
  const innerRadius = slide.chart_type === 'donut' ? 64 : 0

  return (
    <div className="grid h-full min-h-0 grid-cols-[320px_minmax(0,1fr)] items-center gap-5">
      <div className="h-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slide.data || []}
              dataKey="value"
              nameKey="label"
              innerRadius={innerRadius}
              outerRadius={108}
              paddingAngle={3}
            >
              {(slide.data || []).map((entry, index) => (
                <Cell key={`${entry.label}-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="grid min-h-0 auto-rows-fr gap-3">
        {(slide.data || []).map((item, index) => (
          <div
            key={`${item.label}-item`}
            className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-white px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
              />
              <span className="text-sm text-[var(--text-secondary)]">{item.label}</span>
            </div>
            <span className="text-sm font-semibold text-[var(--text-primary)]">{formatValue(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function BarLikeSlide({ slide }) {
  const horizontal = slide.orientation === 'horizontal'
  const categoryAxisProps = buildCategoryAxisProps(slide.data || [], 'label', { maxVisible: 7, maxLength: 12 })

  if (horizontal) {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={slide.data || []}
          layout="vertical"
          margin={{ top: 0, right: 16, left: 20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
          <XAxis type="number" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fill: CHART_AXIS, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={120}
            tickFormatter={categoryAxisProps.tickFormatter}
          />
          <Tooltip content={<ChartTooltip />} />
          {renderReferenceLines(slide, 'x')}
          <Bar dataKey="value" name={slide.value_label || 'valor'} radius={[0, 12, 12, 0]} maxBarSize={38}>
            {(slide.data || []).map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={getSemanticColor(entry.color_signal, index)} />
            ))}
          </Bar>
          {renderAnnotations(slide)}
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={slide.data || []} margin={{ top: 0, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} {...categoryAxisProps} />
        <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} />
        {renderReferenceLines(slide)}
        <Bar dataKey="value" name={slide.value_label || 'valor'} radius={[12, 12, 0, 0]} maxBarSize={44}>
          {(slide.data || []).map((entry, index) => (
            <Cell key={`${entry.label}-${index}`} fill={getSemanticColor(entry.color_signal, index)} />
          ))}
        </Bar>
        {renderAnnotations(slide)}
      </BarChart>
    </ResponsiveContainer>
  )
}

function LineLikeSlide({ slide }) {
  const xAxisProps = buildCategoryAxisProps(slide.data || [], 'label', { maxVisible: 7, maxLength: 12 })

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={slide.data || []} margin={{ top: 0, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} {...xAxisProps} />
        <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} />
        {renderReferenceLines(slide)}
        <Line
          type="monotone"
          dataKey="value"
          name={slide.value_label || 'valor'}
          stroke="#3258ff"
          strokeWidth={3}
          dot={{ r: 4, fill: '#0ea5a4', stroke: '#ffffff', strokeWidth: 2 }}
          activeDot={{ r: 6, fill: '#f46d43', stroke: '#ffffff', strokeWidth: 2 }}
        />
        {(slide.reference_lines || []).some((reference) => reference.kind === 'series') ? (
          <Line
            type="monotone"
            dataKey="reference_value"
            name="Tendencia"
            stroke="#111827"
            strokeDasharray="4 4"
            dot={false}
            strokeWidth={2}
          />
        ) : null}
        {renderAnnotations(slide)}
      </LineChart>
    </ResponsiveContainer>
  )
}

function ScatterLikeSlide({ slide }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
        <XAxis
          type="number"
          dataKey="x"
          name={slide.x_label}
          tick={{ fill: CHART_AXIS, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={slide.y_label}
          tick={{ fill: CHART_AXIS, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<ScatterTooltip slide={slide} />} cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={slide.data || []}>
          {(slide.data || []).map((point, index) => (
            <Cell key={`${point.x}-${point.y}-${index}`} fill={getSemanticColor(point.color_signal, index)} />
          ))}
        </Scatter>
        {renderAnnotations(slide)}
      </ScatterChart>
    </ResponsiveContainer>
  )
}

function ChartBody({ slide }) {
  if (slide.chart_type === 'combo') return <ComboLikeSlide slide={slide} />
  if (slide.chart_type === 'waterfall') return <WaterfallLikeSlide slide={slide} />
  if (slide.chart_type === 'bullet') return <BulletLikeSlide slide={slide} />
  if (slide.chart_type === 'bar_horizontal') return <BarLikeSlide slide={{ ...slide, chart_type: 'bar', orientation: 'horizontal' }} />
  if (slide.chart_type === 'bar') return <BarLikeSlide slide={slide} />
  if (slide.chart_type === 'line') return <LineLikeSlide slide={slide} />
  if (slide.chart_type === 'scatter') return <ScatterLikeSlide slide={slide} />
  if (slide.chart_type === 'heatmap') return <HeatmapChartSlide slide={slide} />
  if (slide.chart_type === 'treemap') return <TreemapChartSlide slide={slide} />
  if (slide.chart_type === 'sankey') return <SankeyChartSlide slide={slide} />
  if (slide.chart_type === 'map') return <MapChartSlide slide={slide} />
  if (slide.chart_type === 'pie' || slide.chart_type === 'donut') return <PieLikeSlide slide={slide} />
  if (slide.chart_type === 'radar') return <RadarChartSlide slide={slide} />
  return <BarLikeSlide slide={{ ...slide, chart_type: 'bar' }} />
}

function ChartPanel({ chart, isPrimary = false }) {
  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] rounded-[28px] border border-[var(--border)] bg-[linear-gradient(180deg,#ffffff_0%,#f7f9fc_100%)] p-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
      {chart.title || chart.subtitle || chart.narrative_link ? (
        <div className="mb-3">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="inline-flex rounded-full bg-[rgba(22,32,43,0.06)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
              {chart.role || (isPrimary ? 'primary' : 'supporting')}
            </span>
            {chart.narrative_link ? (
              <span className="text-[11px] text-[var(--text-secondary)]">{chart.narrative_link}</span>
            ) : null}
          </div>
          {chart.title ? (
            <p className={`font-semibold text-[var(--text-primary)] ${isPrimary ? 'text-lg' : 'text-base'}`}>
              {chart.title}
            </p>
          ) : null}
          {chart.subtitle ? (
            <p className="mt-1 text-sm text-[var(--text-secondary)]" style={clampTextStyle(2)}>{chart.subtitle}</p>
          ) : null}
        </div>
      ) : null}
      <ChartViewport>
        <ChartBody slide={chart} />
      </ChartViewport>
    </div>
  )
}

function getLayoutConfig(slide) {
  if (slide.layout && typeof slide.layout === 'object') return slide.layout
  if (slide.layout_name || slide.layout) {
    return { template_name: slide.layout_name || slide.layout }
  }
  return null
}

function getZoneStyle(zone) {
  if (!Array.isArray(zone) || zone.length !== 4) return undefined
  const [x, y, width, height] = zone
  return {
    gridColumn: `${x + 1} / span ${width}`,
    gridRow: `${y + 1} / span ${height}`,
    minWidth: 0,
  }
}

function StructuredCanvas({ slide, charts }) {
  const primaryChart = charts[0]
  const supportingCharts = charts.slice(1)
  const blockGroups = groupTextBlocks(slide.text_blocks || [])
  const layoutConfig = getLayoutConfig(slide)
  const layoutName = layoutConfig?.template_name || 'chart_dominant'
  const zones = layoutConfig?.zones || {}
  const topBlocks = [
    ...(blockGroups['top-left'] || []),
    ...(blockGroups['top-center'] || []),
    ...(blockGroups['top-right'] || []),
  ]
  const sideBlocks = [
    ...(blockGroups['sidebar-left'] || []),
    ...(blockGroups['sidebar-right'] || []),
  ]
  const bottomLeftBlocks = blockGroups['bottom-left'] || []
  const bottomCenterBlocks = blockGroups['bottom-center'] || []
  const bottomRightBlocks = blockGroups['bottom-right'] || []

  if (zones.visual) {
    const headlineContent = topBlocks
    const footerContent = [...bottomLeftBlocks, ...bottomCenterBlocks, ...bottomRightBlocks]
    const inlineSupporting = zones.insight ? [] : supportingCharts
    const insightContent = [
      ...supportingCharts.filter(() => Boolean(zones.insight)),
      ...sideBlocks,
    ]

    return (
      <div className="grid h-full min-h-0 grid-cols-12 grid-rows-10 gap-4">
        {headlineContent.length ? (
          <div style={getZoneStyle(zones.headline)} className="grid min-h-0 auto-rows-fr gap-3">
            {headlineContent.map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-headline`} block={block} />
            ))}
          </div>
        ) : null}

        <div style={getZoneStyle(zones.visual)} className="grid min-h-0 grid-rows-[minmax(0,1fr)_auto] gap-4">
          <ChartPanel chart={primaryChart} isPrimary />
          {inlineSupporting.length ? (
            <div className="grid grid-cols-2 gap-4">
              {inlineSupporting.map((chart, index) => (
                <div key={`${chart.chart_type || 'support'}-${index}-visual`} className="min-h-0">
                  <ChartPanel chart={chart} />
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {zones.insight && insightContent.length ? (
          <div
            style={{
              ...getZoneStyle(zones.insight),
              gridTemplateRows: `repeat(${Math.max(insightContent.length, 1)}, minmax(0, 1fr))`,
            }}
            className="grid min-h-0 gap-4"
          >
            {supportingCharts.map((chart, index) => (
              <div key={`${chart.chart_type || 'support'}-${index}-insight`} className="min-h-0">
                <ChartPanel chart={chart} />
              </div>
            ))}
            {sideBlocks.map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-insight`} block={block} />
            ))}
          </div>
        ) : null}

        {footerContent.length ? (
          <div
            style={{
              ...getZoneStyle(zones.footer),
              gridTemplateColumns: `repeat(${Math.min(Math.max(footerContent.length, 1), 3)}, minmax(0, 1fr))`,
            }}
            className="grid min-h-0 gap-4"
          >
            {footerContent.map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-footer`} block={block} />
            ))}
          </div>
        ) : null}
      </div>
    )
  }

  let visualSection
  if (layoutName === 'split_horizontal' && supportingCharts.length > 0) {
    visualSection = (
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartPanel chart={primaryChart} isPrimary />
        <ChartPanel chart={supportingCharts[0]} />
      </div>
    )
  } else if ((layoutName === 'dual_chart' || layoutName === 'evidence_grid') && supportingCharts.length > 0) {
    visualSection = (
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.18fr)_340px]">
        <ChartPanel chart={primaryChart} isPrimary />
        <div className="space-y-4">
          {supportingCharts.map((chart, index) => (
            <ChartPanel key={`${chart.chart_type || 'support'}-${index}-${chart.title || 'panel'}`} chart={chart} />
          ))}
          {sideBlocks.map((block, index) => (
            <TextBlockCard key={`${block.role}-${index}-side`} block={block} />
          ))}
        </div>
      </div>
    )
  } else {
    visualSection = (
      <div className="space-y-4">
        <ChartPanel chart={primaryChart} isPrimary />
        {supportingCharts.length ? (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {supportingCharts.map((chart, index) => (
              <ChartPanel key={`${chart.chart_type || 'support'}-${index}-${chart.title || 'inline'}`} chart={chart} />
            ))}
          </div>
        ) : null}
        {sideBlocks.length ? (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {sideBlocks.map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-inline`} block={block} />
            ))}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {topBlocks.length ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          {topBlocks.map((block, index) => (
            <TextBlockCard key={`${block.role}-${index}-top`} block={block} />
          ))}
        </div>
      ) : null}

      {visualSection}

      {bottomLeftBlocks.length || bottomCenterBlocks.length || bottomRightBlocks.length ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <div className="space-y-4">
            {[...bottomLeftBlocks, ...bottomCenterBlocks].map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-bottom-left`} block={block} />
            ))}
          </div>
          <div className="space-y-4">
            {bottomRightBlocks.map((block, index) => (
              <TextBlockCard key={`${block.role}-${index}-bottom-right`} block={block} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default function AnalyticsChartSlide({ slide, slideIndex = 0, totalSlides = 1 }) {
  const charts = Array.isArray(slide.charts) && slide.charts.length
    ? slide.charts
    : [{ ...slide, role: 'primary' }]
  const useSidebar = charts.length > 1 || ['root_cause_story', 'risk_alert'].includes(slide.visual_intent)

  return (
    <SlideFrame
      slideIndex={slideIndex}
      totalSlides={totalSlides}
      stage={slide.stage || 'Data Story'}
    >
      <div className={`grid h-full min-h-0 gap-6 ${useSidebar ? 'grid-cols-[minmax(0,1fr)_300px]' : 'grid-cols-1'}`}>
        <div className="grid min-h-0 grid-rows-[96px_minmax(0,1fr)] gap-5">
          <SlideHeader slide={slide} chartsCount={charts.length} />
          <StructuredCanvas slide={slide} charts={charts} />
        </div>
        {useSidebar ? (
          <NarrativeSidebar slide={slide} slideIndex={slideIndex} totalSlides={totalSlides} charts={charts} />
        ) : null}
      </div>
    </SlideFrame>
  )
}

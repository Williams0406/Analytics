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
import { Fragment, useEffect, useRef, useState } from 'react'

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

// ─── Paleta alineada al design system (light_editorial) ───────────────────────
const MAP_OCEAN     = '#dce8f5'
const MAP_LAND      = '#dde7f3'
const MAP_BORDER    = '#8aadd4'
 
function hexToRgb(hex) {
  const n = parseInt(hex.replace('#', ''), 16)
  return `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`
}
 
function getBubbleRadius(value, maxValue) {
  const MIN = 5, MAX = 22
  if (!maxValue) return MIN
  return MIN + Math.sqrt(Math.max(0, value) / maxValue) * (MAX - MIN)
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

function useSlideScale() {
  const ref = useRef(null)
  const [scale, setScale] = useState(1)

  useEffect(() => {
    function resize() {
      if (!ref.current) return

      const height = ref.current.clientHeight
      const width = ref.current.clientWidth

      const baseHeight = 900
      const baseWidth = 1600

      const scaleFactor = Math.min(
        width / baseWidth,
        height / baseHeight,
        1
      )

      setScale(scaleFactor)
    }

    resize()
    window.addEventListener('resize', resize)

    return () => window.removeEventListener('resize', resize)
  }, [])

  return { ref, scale }
}

function SlideFrame({ children }) {
  return (
    <div className="w-full h-full aspect-[16/9] overflow-hidden">
      <div
        className="w-full h-full"
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </div>
    </div>
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
      <h3 className="max-w-5xl text-[28px] xl:text-[32px] font-semibold leading-tight text-[var(--text-primary)]">
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
    <div className={`self-start rounded-[24px] border p-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)] ${tones[tone] || tones.light}`}>
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
      className={`inline-block w-fit max-w-full self-start rounded-[24px] border bg-white shadow-[0_16px_36px_rgba(15,23,42,0.05)] ${sizeClass}`}
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

function getCellBackground(value) {
  if (value === null || value === undefined) return null
  const intensity = Math.min(Math.abs(value), 1)
  const hue = value >= 0 ? '14,165,164' : '244,109,67'
  const alpha = (0.08 + intensity * 0.62).toFixed(2)
  return `rgba(${hue}, ${alpha})`
}
 
function getCellTextColor(value) {
  if (value === null || value === undefined) return 'var(--text-secondary)'
  const intensity = Math.abs(value)
  if (intensity > 0.55) return value >= 0 ? '#085041' : '#993c1d'
  return 'var(--text-primary)'
}
 
function formatCellValue(value) {
  if (value === null || value === undefined) return '—'
  const n = Number(value)
  if (Math.abs(n) < 10) return n.toFixed(2)
  return n.toLocaleString()
}
 
function HeatmapCell({ value, rowLabel, colLabel, isActive, onEnter, onLeave }) {
  const bg        = getCellBackground(value)
  const textColor = getCellTextColor(value)
  const isNull    = bg === null
 
  return (
    <div
      className="relative flex items-center justify-center text-[11px] font-semibold transition-all duration-100 cursor-pointer select-none"
      style={{
        borderRadius: 6,
        background:   isNull ? 'var(--surface-muted, #f1f5f9)' : bg,
        color:        isNull ? 'var(--text-muted)' : textColor,
        outline:      isActive ? '2px solid #3258ff' : 'none',
        outlineOffset: '1px',
        transform:    isActive ? 'scale(1.06)' : 'scale(1)',
        zIndex:       isActive ? 2 : 0,
      }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
      {formatCellValue(value)}
 
      {isActive && !isNull && (
        <div
          className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[11px] text-white"
          style={{
            background: '#16202b',
            border: '1px solid rgba(255,255,255,0.08)',
            zIndex: 20,
          }}
        >
          <span className="text-slate-400">{rowLabel} · {colLabel}: </span>
          <span className="font-semibold">{formatCellValue(value)}</span>
        </div>
      )}
    </div>
  )
}
 
function HeatmapChartSlide({ slide }) {
  const [activeCell, setActiveCell] = useState(null)
  const containerRef                = useRef(null)
 
  // El slide canvas es 1600×900; el área útil del chart (dentro del ChartPanel)
  // es aproximadamente (1600 - padding - sidebar) × (900 - header - padding - scale).
  // Medimos el contenedor real con ResizeObserver para ser exactos.
  const [containerSize, setContainerSize] = useState({ w: 900, h: 520 })
 
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
 
    const measure = () => {
      setContainerSize({ w: el.clientWidth, h: el.clientHeight })
    }
    measure()
 
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(measure)
      ro.observe(el)
      return () => ro.disconnect()
    }
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])
 
  const cellLookup = new Map(
    (slide.data || []).map((cell) => [`${cell.y}::${cell.x}`, cell.value])
  )
  const values   = (slide.data || []).map((cell) => Number(cell.value) || 0)
  const minValue = values.length ? Math.min(...values) : 0
  const maxValue = values.length ? Math.max(...values) : 0
 
  const xLabels = slide.x_labels || []
  const yLabels = slide.y_labels || []
 
  // ── Altura reservada para header de columnas + barra de escala + gaps ──
  const HEADER_H   = 36   // px — fila de labels de columnas
  const SCALE_H    = 32   // px — barra de escala inferior
  const GAP        = 3    // px — gap entre celdas
  const ROW_LABEL_W = 110 // px — ancho columna de etiquetas de fila
 
  // Espacio neto disponible para la matriz de celdas
  const matrixH = containerSize.h - HEADER_H - SCALE_H - 24  // 24 = gaps entre rows del grid
  const matrixW = containerSize.w - ROW_LABEL_W - 8
 
  // Tamaño de celda cuadrada que encaja exactamente en la matriz, sin scroll
  const cellByH = yLabels.length > 0 ? Math.floor((matrixH - GAP * (yLabels.length - 1)) / yLabels.length) : 40
  const cellByW = xLabels.length > 0 ? Math.floor((matrixW - GAP * (xLabels.length - 1)) / xLabels.length) : 40
 
  // Usamos el mínimo para que entren tanto filas como columnas
  // Clamp: mínimo 22px (legible), máximo 56px (no desperdicia espacio)
  const cellSize = Math.max(22, Math.min(cellByH, cellByW, 56))
 
  // Font size se adapta al tamaño de celda
  const cellFontSize = cellSize < 30 ? 9 : cellSize < 38 ? 10 : 11
 
  // Ancho de etiquetas de fila se ajusta si hay poco espacio horizontal
  const rowLabelW = Math.min(
    ROW_LABEL_W,
    Math.max(90, Math.floor(containerSize.w * 0.12))
  )
 
  return (
    <div
      ref={containerRef}
      className="grid h-full min-h-0 w-full"
      style={{ gridTemplateRows: `${HEADER_H}px minmax(0,1fr) ${SCALE_H}px`, gap: '6px' }}
    >
 
      {/* ── Header: esquina + labels de columnas ───────────────────── */}
      <div
        className="grid items-end"
        style={{
          gridTemplateColumns: `${rowLabelW}px repeat(${xLabels.length}, ${cellSize}px)`,
          gap: `${GAP}px`,
        }}
      >
        <div className="flex items-end pb-1">
          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">
            {slide.y_axis_label || 'Segmentos'}
          </span>
        </div>
        {xLabels.map((label) => (
          <div
            key={label}
            className="text-center text-[10px] font-medium uppercase tracking-[0.14em] text-[var(--text-muted)] leading-tight"
            style={{
              // Trunca labels largos para que no desborden la celda
              maxWidth: cellSize,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={label}
          >
            {label}
          </div>
        ))}
      </div>
 
      {/* ── Matriz de celdas ─────────────────────────────────────────── */}
      {/* overflow: hidden — el tamaño calculado debe ser exacto, no necesita scroll */}
      <div className="min-h-0 min-w-0 overflow-hidden">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `${rowLabelW}px repeat(${xLabels.length}, ${cellSize}px)`,
            gridTemplateRows:    `repeat(${yLabels.length}, ${cellSize}px)`,
            gap: `${GAP}px`,
          }}
        >
          {yLabels.map((rowLabel) => (
            <Fragment key={rowLabel}>
              {/* Etiqueta de fila */}
              <div
                className="flex items-center justify-end text-[var(--text-secondary)]"
                style={{
                  fontSize: cellFontSize + 1,
                  paddingRight: 8,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={rowLabel}
              >
                {rowLabel}
              </div>
 
              {/* Celdas */}
              {xLabels.map((colLabel) => {
                const key    = `${rowLabel}::${colLabel}`
                const rawVal = cellLookup.get(key)
                const value  = rawVal !== undefined ? Number(rawVal) : null
 
                return (
                  <HeatmapCell
                    key={key}
                    value={value}
                    rowLabel={rowLabel}
                    colLabel={colLabel}
                    isActive={activeCell === key}
                    onEnter={() => setActiveCell(key)}
                    onLeave={() => setActiveCell(null)}
                  />
                )
              })}
            </Fragment>
          ))}
        </div>
      </div>
 
      {/* ── Barra de escala ─────────────────────────────────────────── */}
      <div
        className="grid items-center"
        style={{
          gridTemplateColumns: `${rowLabelW}px repeat(${xLabels.length}, ${cellSize}px)`,
          gap: `${GAP}px`,
        }}
      >
        <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">
          Correlation
        </span>

        <div
          style={{
            gridColumn: `2 / span ${xLabels.length}`,
          }}
          className="flex flex-col gap-1"
        >
          <div className="h-[5px] rounded-full bg-[linear-gradient(90deg,#f46d43_0%,#fff4ef_18%,#f8fafc_50%,#e7fbf8_82%,#0ea5a4_100%)]" />
          <div className="flex justify-between text-[10px] text-[var(--text-muted)]">
            <span>{minValue.toFixed(2)}</span>
            <span>0.00</span>
            <span>{maxValue.toFixed(2)}</span>
          </div>
        </div>
      </div>
 
    </div>
  )
}

function MapChartSlide({ slide }) {
  const svgRef                    = useRef(null)
  const [active, setActive]       = useState(null)
  const [rendered, setRendered]   = useState(false)
  const [error, setError]         = useState(false)
 
  const data     = slide.data || []
  const maxValue = Math.max(...data.map((d) => Number(d.value) || 0), 1)
 
  useEffect(() => {
    let cancelled = false
 
    async function draw() {
      // ── Importa D3 y TopoJSON desde node_modules (instalados) ──────────────
      const [d3, { feature }] = await Promise.all([
        import('d3'),
        import('topojson-client'),
      ])
      if (cancelled) return
 
      // ── Carga el GeoJSON del mundo ──────────────────────────────────────────
      let world
      try {
        world = await d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
      } catch {
        setError(true)
        return
      }
      if (cancelled) return
 
      const svgEl = svgRef.current
      if (!svgEl) return
      while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild)
 
      const W = svgEl.clientWidth  || 600
      const H = svgEl.clientHeight || 360
 
      const svg = d3.select(svgEl)
        .attr('viewBox', `0 0 ${W} ${H}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
 
      // ── Proyección: se auto-centra en los puntos de datos ──────────────────
      // Si hay puntos, centra automáticamente; si no, usa vista mundial
      const lngs = data.map((d) => Number(d.lng ?? d.x)).filter((v) => !isNaN(v))
      const lats = data.map((d) => Number(d.lat ?? d.y)).filter((v) => !isNaN(v))
 
      let projection
      if (lngs.length > 0) {
        const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2
        const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2
        const spanLng   = Math.max(...lngs) - Math.min(...lngs)
        const spanLat   = Math.max(...lats) - Math.min(...lats)
        // Escala según el span geográfico de los datos
        const scale = Math.min(
          (W / Math.max(spanLng, 10)) * 28,
          (H / Math.max(spanLat, 10)) * 28,
          800
        )
        projection = d3.geoMercator()
          .center([centerLng, centerLat])
          .scale(scale)
          .translate([W / 2, H / 2])
      } else {
        // Vista mundial por defecto
        projection = d3.geoNaturalEarth1()
          .scale(W / 6.5)
          .translate([W / 2, H / 2])
      }
 
      const path      = d3.geoPath().projection(projection)
      const countries = feature(world, world.objects.countries)
 
      // ── Fondo océano ────────────────────────────────────────────────────────
      svg.append('rect')
        .attr('width', W).attr('height', H)
        .attr('rx', 12)
        .attr('fill', MAP_OCEAN)
 
      // ── Países ──────────────────────────────────────────────────────────────
      svg.selectAll('.country')
        .data(countries.features)
        .join('path')
        .attr('class', 'country')
        .attr('d', path)
        .attr('fill', MAP_LAND)
        .attr('stroke', MAP_BORDER)
        .attr('stroke-width', 0.4)
 
      // ── Burbujas de datos ───────────────────────────────────────────────────
      data.forEach((point, index) => {
        const lng = Number(point.lng ?? point.x)
        const lat = Number(point.lat ?? point.y)
        if (isNaN(lng) || isNaN(lat)) return
 
        const coords = projection([lng, lat])
        if (!coords) return
        const [px, py] = coords
        if (px < 0 || py < 0 || px > W || py > H) return
 
        const r     = getBubbleRadius(Number(point.value) || 0, maxValue)
        const color = getChartColor(index)
 
        // Halo
        svg.append('circle')
          .attr('cx', px).attr('cy', py).attr('r', r + 6)
          .attr('fill', color).attr('fill-opacity', 0.1)
          .style('pointer-events', 'none')
 
        // Burbuja
        svg.append('circle')
          .attr('cx', px).attr('cy', py).attr('r', r)
          .attr('fill', color).attr('fill-opacity', 0.82)
          .attr('stroke', '#ffffff').attr('stroke-width', 2)
          .style('cursor', 'pointer')
          .on('mouseenter', () => setActive(index))
          .on('mouseleave', () => setActive(null))
 
        // Label pill
        const g   = svg.append('g').style('pointer-events', 'none')
        const txt = g.append('text')
          .attr('x', px + r + 5).attr('y', py)
          .attr('dominant-baseline', 'middle')
          .attr('font-size', 11).attr('font-weight', 500)
          .attr('fill', '#16202b')
          .text(point.label)
 
        try {
          const b = txt.node().getBBox()
          if (b.width > 0) {
            g.insert('rect', 'text')
              .attr('x', b.x - 4).attr('y', b.y - 3)
              .attr('width', b.width + 8).attr('height', b.height + 6)
              .attr('rx', 5).attr('fill', 'white').attr('fill-opacity', 0.92)
              .attr('stroke', MAP_BORDER).attr('stroke-width', 0.5)
          }
        } catch (_) {}
      })
 
      setRendered(true)
    }
 
    draw().catch((err) => {
      console.error('MapChartSlide draw error:', err)
      setError(true)
      setRendered(true)
    })
 
    return () => { cancelled = true }
  }, [data, maxValue])
 
  const activeItem = active !== null ? data[active] : null
 
  return (
    <div className="grid h-full min-h-0 grid-cols-[minmax(0,1.35fr)_280px] gap-4">
 
      {/* ── Área del mapa ─────────────────────────────────────────────────── */}
      <div
        className="relative rounded-[24px] border border-[var(--border)] overflow-hidden"
        style={{ background: MAP_OCEAN }}
      >
        <svg
          ref={svgRef}
          className="h-full w-full"
          style={{ display: 'block' }}
        />
 
        {/* Estado: cargando */}
        {!rendered && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
              Cargando mapa…
            </span>
          </div>
        )}
 
        {/* Estado: error */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
              No se pudo cargar el mapa
            </span>
          </div>
        )}
 
        {/* Tooltip hover */}
        {activeItem && (
          <div
            className="pointer-events-none absolute bottom-4 left-4 rounded-2xl px-3 py-2 text-xs"
            style={{
              background: '#16202b',
              color: '#f1f5f9',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <p className="font-semibold text-white">{activeItem.label}</p>
            <p className="mt-0.5 text-slate-300">{formatValue(Number(activeItem.value))}</p>
          </div>
        )}
 
        {/* Escala de burbujas */}
        <div
          className="pointer-events-none absolute bottom-4 right-4 flex items-center gap-2 rounded-xl px-3 py-2"
          style={{
            background: 'rgba(255,255,255,0.85)',
            border: `0.5px solid ${MAP_BORDER}`,
          }}
        >
          <svg width="44" height="18" style={{ overflow: 'visible' }}>
            <circle cx="6"  cy="15" r="3"  fill="#3258ff" fillOpacity="0.6" stroke="#3258ff" strokeWidth="1" />
            <circle cx="20" cy="12" r="6"  fill="#3258ff" fillOpacity="0.6" stroke="#3258ff" strokeWidth="1" />
            <circle cx="38" cy="8"  r="10" fill="#3258ff" fillOpacity="0.6" stroke="#3258ff" strokeWidth="1" />
          </svg>
          <span className="text-[10px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
            volumen
          </span>
        </div>
      </div>
 
      {/* ── Leyenda lateral ────────────────────────────────────────────────── */}
      <div className="grid min-h-0 auto-rows-max content-start gap-2 overflow-y-auto">
        <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
          {slide.legend_label || 'Ubicaciones'}
        </p>
 
        {data.map((item, index) => {
          const pct      = Math.round((Math.max(0, Number(item.value) || 0) / maxValue) * 100)
          const color    = getChartColor(index)
          const isActive = active === index
 
          return (
            <div
              key={`${item.label}-legend`}
              className="cursor-pointer rounded-[16px] border px-4 py-3 transition-all duration-150"
              style={{
                borderColor: isActive ? color : 'var(--border)',
                background:  isActive ? `rgba(${hexToRgb(color)}, 0.06)` : 'white',
                boxShadow:   isActive ? `inset 3px 0 0 ${color}` : 'none',
              }}
              onMouseEnter={() => setActive(index)}
              onMouseLeave={() => setActive(null)}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span
                    className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-sm text-[var(--text-secondary)]">{item.label}</span>
                </div>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {formatValue(Number(item.value))}
                </span>
              </div>
 
              <div className="mt-2 h-[3px] w-full overflow-hidden rounded-full bg-[var(--surface-muted,#f1f5f9)]">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
 
              <p className="mt-1 text-right text-[10px] text-[var(--text-muted)]">
                {pct}% del máximo
              </p>
            </div>
          )
        })}
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
    <div className="grid h-full min-h-0 grid-cols-[minmax(260px,0.9fr)_minmax(0,1.1fr)] items-center gap-5">
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

      <div className="grid min-h-0 auto-rows-max content-start gap-3">
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

function getSmartLayout(slide, charts) {
  const chartType = (
    charts?.[0]?.chart_type ||
    slide.chart_type ||
    ''
  ).toLowerCase()

  const left70Charts = new Set([
    'bar',
    'bar_horizontal',
    'heatmap',
    'pie',
    'donut',
    'radar',
    'bullet',
    'treemap',
  ])

  return left70Charts.has(chartType)
    ? 'LEFT_70'
    : 'TOP_70'
}

function StructuredCanvas({
  slide,
  charts,
  slideIndex = 0,
  totalSlides = 1,
}) {
  const primaryChart = charts[0]
  const supportingCharts = charts.slice(1)

  const smartLayout = getSmartLayout(slide, charts)

  const blockGroups = groupTextBlocks(slide.text_blocks || [])

  const bottomLeftBlocks = blockGroups['bottom-left'] || []
  const bottomCenterBlocks = blockGroups['bottom-center'] || []
  const bottomRightBlocks = blockGroups['bottom-right'] || []

  let visualSection

  if (smartLayout === 'LEFT_70') {
    const allBlocks = [
      ...bottomLeftBlocks,
      ...bottomCenterBlocks,
      ...bottomRightBlocks,
    ]

    const kpiBlocks = allBlocks.filter(
      (b) => b.role === 'kpi_badge'
    )

    const textBlocks = allBlocks.filter(
      (b) => b.role !== 'kpi_badge'
    )

    visualSection = (
      <div className="grid h-full min-h-0 grid-cols-[70%_30%] gap-5">
        
        {/* LEFT 70% CHART */}
        <div className="min-h-0 h-full overflow-hidden">
          <ChartPanel chart={primaryChart} isPrimary />
        </div>

        {/* RIGHT 30% CONTENT */}
        <div className="grid h-full min-h-0 grid-rows-[auto_auto_1fr] gap-4">

          {/* SLIDE */}
          <div className="rounded-[24px] border bg-white p-4">
            <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
              Slide
            </p>
            <p className="mt-1 text-lg font-semibold">
              {String(slideIndex + 1).padStart(2, '0')} / {String(totalSlides).padStart(2, '0')}
            </p>
          </div>

          {/* KPI */}
          {kpiBlocks.map((block, index) => (
            <TextBlockCard key={`kpi-${index}`} block={block} />
          ))}

          {/* TEXT BLOCKS */}
          <div className="grid auto-rows-max content-start gap-4 overflow-hidden">
            {textBlocks.map((block, index) => (
              <TextBlockCard key={`text-${index}`} block={block} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  else {
    const allBlocks = [
      ...bottomLeftBlocks,
      ...bottomCenterBlocks,
      ...bottomRightBlocks,
    ]

    const kpiBlocks = allBlocks.filter(
      (b) => b.role === 'kpi_badge'
    )

    const textBlocks = allBlocks.filter(
      (b) => b.role !== 'kpi_badge'
    )

    visualSection = (
      <div className="grid h-full min-h-0 grid-rows-[70%_30%] gap-5">

        {/* TOP 70% */}
        <div className="relative min-h-0 overflow-hidden">

          {/* FLOATING SLIDE + KPI */}
          <div className="absolute top-4 right-4 z-20 w-[260px] space-y-3">

            <div className="rounded-[24px] border bg-white p-4 shadow">
              <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
                Slide
              </p>
              <p className="mt-1 text-lg font-semibold">
                {String(slideIndex + 1).padStart(2, '0')} / {String(totalSlides).padStart(2, '0')}
              </p>
            </div>

            {kpiBlocks.map((block, index) => (
              <TextBlockCard key={`top-kpi-${index}`} block={block} />
            ))}
          </div>

          <ChartPanel chart={primaryChart} isPrimary />
        </div>

        {/* BOTTOM 30% */}
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${Math.min(
              Math.max(textBlocks.length, 1),
              3
            )}, minmax(0, 1fr))`,
          }}
        >
          {textBlocks.map((block, index) => (
            <TextBlockCard key={`bottom-${index}`} block={block} />
          ))}
        </div>
      </div>
    )
  }

  return visualSection
}

export default function AnalyticsChartSlide({ slide, slideIndex = 0, totalSlides = 1 }) {
  const charts = Array.isArray(slide.charts) && slide.charts.length
    ? slide.charts
    : [{ ...slide, role: 'primary' }]
  const useSidebar = false

  return (
    <SlideCanvas
      slideIndex={slideIndex}
      totalSlides={totalSlides}
      stage={slide.stage || 'Data Story'}
    >
      <SlideFrame
        slideIndex={slideIndex}
        totalSlides={totalSlides}
        stage={slide.stage || 'Data Story'}
      >
        <div className={`grid h-full min-h-0 gap-6 ${useSidebar ? 'grid-cols-[minmax(0,1fr)_clamp(220px,18vw,260px)]' : 'grid-cols-1'}`}>
          <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-5">
            <SlideHeader slide={slide} chartsCount={charts.length} />
            <StructuredCanvas
              slide={slide}
              charts={charts}
              slideIndex={slideIndex}
              totalSlides={totalSlides}
            />
          </div>
          {useSidebar ? (
            <NarrativeSidebar slide={slide} slideIndex={slideIndex} totalSlides={totalSlides} charts={charts} />
          ) : null}
        </div>
      </SlideFrame>
    </SlideCanvas>
  )
}

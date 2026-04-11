const HEAVY_CHART_TYPES = new Set(['heatmap', 'map', 'sankey'])
const MEDIUM_CHART_TYPES = new Set(['scatter', 'treemap', 'radar', 'pie', 'donut', 'combo'])
const DENSE_LAYOUTS = new Set(['evidence_grid', 'dual_chart', 'split_horizontal', 'chart_dominant'])

function normalizeText(value) {
  return String(value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}

function normalizeNumber(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) {
    return value ?? ''
  }
  return Math.round(number * 1000) / 1000
}

function stableSerialize(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(',')}]`
  }

  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${key}:${stableSerialize(value[key])}`).join(',')}}`
  }

  if (typeof value === 'number') {
    return String(normalizeNumber(value))
  }

  if (typeof value === 'string') {
    return normalizeText(value)
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }

  return value == null ? '' : String(value)
}

function pickPointFields(item = {}) {
  return Object.fromEntries(
    Object.entries(item).filter(([key, value]) => (
      ['label', 'name', 'metric', 'x', 'y', 'value', 'secondary_value', 'reference_value', 'source', 'target'].includes(key)
      && value !== undefined
      && value !== null
      && value !== ''
    )).map(([key, value]) => [
      key,
      typeof value === 'number' ? normalizeNumber(value) : normalizeText(value),
    ]),
  )
}

function buildChartSignature(chart = {}) {
  const data = Array.isArray(chart.data)
    ? chart.data.map((item) => (item && typeof item === 'object' ? pickPointFields(item) : item))
    : chart.data && typeof chart.data === 'object'
      ? {
          nodes: Array.isArray(chart.data.nodes) ? chart.data.nodes.map((item) => pickPointFields(item)) : [],
          links: Array.isArray(chart.data.links) ? chart.data.links.map((item) => pickPointFields(item)) : [],
        }
      : chart.data

  return stableSerialize({
    chart_type: normalizeText(chart.chart_type),
    orientation: normalizeText(chart.orientation),
    value_label: normalizeText(chart.value_label),
    secondary_label: normalizeText(chart.secondary_label),
    x_label: normalizeText(chart.x_label),
    y_label: normalizeText(chart.y_label),
    x_labels: Array.isArray(chart.x_labels) ? chart.x_labels.map((item) => normalizeText(item)) : [],
    y_labels: Array.isArray(chart.y_labels) ? chart.y_labels.map((item) => normalizeText(item)) : [],
    series: Array.isArray(chart.series) ? chart.series.map((item) => normalizeText(item)) : [],
    data,
  })
}

function hasNarrativeDensity(slide) {
  return Boolean(
    slide?.confidence
    || slide?.finding
    || slide?.conclusion
    || slide?.recommendation
    || slide?.complication
    || (Array.isArray(slide?.text_blocks) && slide.text_blocks.length > 2)
  )
}

function collectNarrativeText(slide = {}) {
  const blockText = (slide.text_blocks || []).map((block) => block?.content || '').join(' ')
  return [
    slide.finding,
    slide.conclusion,
    slide.recommendation,
    slide.complication,
    slide.subtitle,
    blockText,
  ].filter(Boolean).join(' ')
}

function estimateTextDensity(slide = {}) {
  const textBlocks = Array.isArray(slide?.text_blocks) ? slide.text_blocks.length : 0
  const callouts = Array.isArray(slide?.callouts) ? slide.callouts.length : 0
  const evidence = Array.isArray(slide?.evidence) ? slide.evidence.length : 0
  const narrativeWeight = hasNarrativeDensity(slide) ? 0.55 : 0
  const denseLayoutWeight = DENSE_LAYOUTS.has(String(slide?.layout_name || slide?.layout || '')) ? 0.35 : 0
  const characterWeight = Math.min(0.85, normalizeText(collectNarrativeText(slide)).length / 420)

  return narrativeWeight + denseLayoutWeight + characterWeight + Math.min(1.15, (textBlocks * 0.2) + (callouts * 0.12) + (evidence * 0.08))
}

function estimateChartWeight(chart = {}) {
  const chartType = String(chart.chart_type || '').toLowerCase()
  if (HEAVY_CHART_TYPES.has(chartType)) return 2
  if (MEDIUM_CHART_TYPES.has(chartType)) return 1.35
  return 1
}

function dedupeCharts(charts = [], seenChartKeys = new Set()) {
  return charts.filter((chart) => {
    const signature = buildChartSignature(chart)
    if (!signature || seenChartKeys.has(signature)) {
      return false
    }
    seenChartKeys.add(signature)
    return true
  })
}

function splitChartSlide(slide, seenChartKeys) {
  const rawCharts = Array.isArray(slide?.charts) && slide.charts.length
    ? slide.charts
    : [slide]
  const charts = dedupeCharts(rawCharts, seenChartKeys)

  if (!charts.length) return []
  if (charts.length === 1) {
    return [{ ...slide, charts }]
  }

  const capacity = Math.max(1, 2.7 - estimateTextDensity(slide))
  const chunks = []
  let currentChunk = []
  let currentWeight = 0

  for (const chart of charts) {
    const weight = estimateChartWeight(chart)
    if (currentChunk.length && currentWeight + weight > capacity) {
      chunks.push(currentChunk)
      currentChunk = [chart]
      currentWeight = weight
      continue
    }
    currentChunk.push(chart)
    currentWeight += weight
  }

  if (currentChunk.length) {
    chunks.push(currentChunk)
  }

  if (chunks.length <= 1) {
    return [{ ...slide, charts }]
  }

  return chunks.map((chunk, index) => ({
    ...slide,
    charts: chunk,
    title:
      index === 0
        ? slide.title
        : `${slide.title || slide.question || 'Evidencia'} - Parte ${index + 1}`,
    subtitle:
      index === 0
        ? slide.subtitle
        : `Graficos adicionales para ${slide.question || slide.title || 'esta lectura'}.`,
    finding: index === 0 ? slide.finding : '',
    conclusion: index === 0 ? slide.conclusion : '',
    recommendation: index === 0 ? slide.recommendation : '',
    complication: index === 0 ? slide.complication : '',
    confidence: index === 0 ? slide.confidence : undefined,
    signal_value: index === 0 ? slide.signal_value : chunk.length,
    signal_label: index === 0 ? slide.signal_label : 'graficos',
    text_blocks: index === 0 ? slide.text_blocks : [],
  }))
}

export function normalizePresentationSlides(slides = []) {
  const seenChartKeys = new Set()

  return (slides || []).flatMap((slide) => {
    if ((slide?.type || '') === 'chart') {
      return splitChartSlide(slide, seenChartKeys)
    }
    return [slide]
  })
}

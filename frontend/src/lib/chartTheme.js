export const CHART_COLORS = [
  '#3258ff',
  '#0ea5a4',
  '#f46d43',
  '#8b5cf6',
  '#d4a72c',
  '#2f855a',
]

export const CHART_GRID = '#e8e0d5'
export const CHART_AXIS = '#7b8794'
export const CHART_TEXT = '#16202b'
export const CHART_TOOLTIP_STYLE = {
  background: '#16202b',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '18px',
  color: '#f8fafc',
  fontSize: '12px',
  boxShadow: '0 18px 40px rgba(15, 23, 42, 0.18)',
}

export function getChartColor(index = 0) {
  return CHART_COLORS[index % CHART_COLORS.length]
}

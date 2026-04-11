'use client'

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import AnalyticsChartSlide from '@/components/analytics/AnalyticsChartSlide'
import { normalizePresentationSlides } from '@/components/analytics/presentationUtils'
import {
  CHART_AXIS,
  CHART_GRID,
  CHART_TOOLTIP_STYLE,
  getChartColor,
} from '@/lib/chartTheme'
import MarkdownMath from '@/components/ui/MarkdownMath'
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

function StoryCard({ title, body, tone = 'light' }) {
  const tones = {
    light: 'border-[var(--border)] bg-white',
    accent: 'border-[rgba(50,88,255,0.18)] bg-[rgba(50,88,255,0.06)]',
    dark: 'border-slate-900/10 bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] text-white',
  }

  return (
    <div className={`rounded-[24px] border p-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)] ${tones[tone] || tones.light}`}>
      <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${tone === 'dark' ? 'text-slate-400' : 'text-[var(--text-muted)]'}`}>
        {title}
      </p>
      <MarkdownMath
        content={body}
        className={`mt-3 text-sm leading-6 ${tone === 'dark' ? 'text-slate-100' : 'text-[var(--text-primary)]'}`}
      />
    </div>
  )
}

function SlideFrame({ children, slideIndex = 0, totalSlides = 1, stage = 'Story' }) {
  return (
    <SlideCanvas stage={stage} slideIndex={slideIndex} totalSlides={totalSlides} contentClassName="grid h-full min-h-0">
      {children}
    </SlideCanvas>
  )
}

function StoryStack({ slide }) {
  const panels = getNarrativePanels(slide, slide.confidence ? 2 : 3)
  if (!panels.length && !slide.confidence) return null

  return (
    <div className="space-y-4">
      {slide.confidence ? (
        <div className="rounded-[24px] border border-[var(--border)] bg-white px-4 py-4 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">Confianza</p>
              <p className="mt-1 text-base font-semibold text-[var(--text-primary)]">
                {slide.confidence.level} · {slide.confidence.score}/100
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
          <p className="mt-3 text-xs leading-5 text-[var(--text-secondary)]" style={clampTextStyle(2)}>{slide.confidence.caveat}</p>
        </div>
      ) : null}
      {panels.map((panel, index) => (
        <StoryCard key={`${panel.title}-${index}`} title={panel.title} body={panel.body} tone={panel.tone} />
      ))}
    </div>
  )
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  return (
    <div style={CHART_TOOLTIP_STYLE} className="rounded-2xl p-3 text-xs">
      <p className="mb-2 text-slate-300">{label}</p>
      {payload.map((entry, index) => (
        <div
          key={`${entry.dataKey || entry.name}-${index}`}
          className="mb-1 flex justify-between gap-3 text-slate-200"
        >
          <span>{entry.name}</span>
          <span className="font-semibold text-white">{formatValue(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

function HeroSlide({ slide, slideIndex, totalSlides }) {
  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.eyebrow || slide.stage || 'Story'}>
      <div className="grid h-full min-h-0 grid-cols-[minmax(0,1.18fr)_360px] gap-8">
        <div className="grid min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-6">
          <div>
            <p className="mb-3 text-xs uppercase tracking-[0.32em] text-[#3258ff]">{slide.eyebrow}</p>
            <MarkdownMath
              content={slide.title}
              className="max-w-4xl text-[54px] font-semibold leading-[1.02] text-[var(--text-primary)]"
            />
            <MarkdownMath
              content={slide.subtitle}
              className="mt-4 max-w-3xl text-[21px] leading-8 text-[var(--text-secondary)]"
            />
          </div>

          {slide.question ? (
            <div className="rounded-[28px] border border-[rgba(50,88,255,0.16)] bg-[rgba(50,88,255,0.05)] px-5 py-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--accent-indigo)]">
                Pregunta Central
              </p>
              <MarkdownMath
                content={slide.question}
                className="mt-3 text-[28px] font-semibold leading-9 text-[var(--text-primary)]"
              />
            </div>
          ) : null}

          <div className="grid min-h-0 grid-cols-2 gap-3">
            {(slide.bullets || []).slice(0, 4).map((bullet, index) => (
              <div
                key={`${slide.title || slide.eyebrow || 'hero'}-${index}-${bullet}`}
                className="rounded-3xl border border-[var(--border)] bg-[rgba(248,244,238,0.7)] px-4 py-4 text-sm leading-6 text-[var(--text-secondary)]"
                style={{
                  boxShadow: `inset 3px 0 0 ${getChartColor(index)}`,
                }}
              >
                <MarkdownMath content={bullet} />
              </div>
            ))}
          </div>
        </div>

        <div className="grid min-h-0 grid-rows-[240px_minmax(0,1fr)] gap-4">
          <div className="rounded-[28px] border border-slate-900/10 bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] p-6 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
            <p className="mb-3 text-xs uppercase tracking-[0.28em] text-slate-400">Signal</p>
            <p className="text-[72px] font-semibold leading-none text-white">{formatValue(slide.accent_value)}</p>
            <p className="mt-4 text-sm leading-6 text-slate-300">{slide.accent_label}</p>
          </div>
          <div className="min-h-0 overflow-hidden">
            <StoryStack slide={slide} />
          </div>
        </div>
      </div>
    </SlideFrame>
  )
}

function IndexSlide({ slide, slideIndex, totalSlides }) {
  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.eyebrow || 'Roadmap'}>
      <div className="grid h-full min-h-0 grid-cols-[320px_minmax(0,1fr)] gap-8">
        <div>
          <p className="mb-3 text-xs uppercase tracking-[0.32em] text-[#0ea5a4]">{slide.eyebrow}</p>
          <MarkdownMath
            content={slide.title}
            className="text-[48px] font-semibold leading-[1.04] text-[var(--text-primary)]"
          />
          <MarkdownMath
            content={slide.subtitle}
            className="mt-4 max-w-md text-lg leading-8 text-[var(--text-secondary)]"
          />
        </div>

        <div className="grid min-h-0 grid-cols-2 gap-4">
          {(slide.entries || []).map((entry, index) => (
            <div
              key={`${entry.number}-${entry.title}`}
              className="rounded-[28px] border border-[var(--border)] bg-white px-5 py-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]"
            >
              <div className="inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-white" style={{ backgroundColor: getChartColor(index) }}>
                {String(entry.number).padStart(2, '0')}
              </div>
              <MarkdownMath content={entry.title} className="mt-4 text-xl font-semibold text-[var(--text-primary)]" />
              <MarkdownMath content={entry.detail} className="mt-2 text-sm leading-6 text-[var(--text-secondary)]" />
            </div>
          ))}
        </div>
      </div>
    </SlideFrame>
  )
}

function BarChartSlide({ slide, slideIndex, totalSlides }) {
  const xAxisProps = buildCategoryAxisProps(slide.data || [], 'label', { maxVisible: 7, maxLength: 12 })

  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.stage || 'Story'}>
      <div className="grid h-full min-h-0 grid-rows-[96px_minmax(0,1fr)] gap-5">
        <div>
          <MarkdownMath content={slide.title} className="text-[34px] font-semibold leading-tight text-[var(--text-primary)]" />
          <MarkdownMath content={slide.subtitle} className="mt-2 text-sm leading-6 text-[var(--text-secondary)]" />
        </div>

        <div className="min-h-0 rounded-[28px] border border-[var(--border)] bg-white p-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={slide.data || []} margin={{ top: 12, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
              <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} {...xAxisProps} />
            <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="value" name={slide.value_label || 'valor'} radius={[12, 12, 0, 0]} maxBarSize={56}>
              {(slide.data || []).map((entry, index) => (
                <Cell key={`${entry.label}-${index}`} fill={getChartColor(index)} />
              ))}
            </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </SlideFrame>
  )
}

function WorkflowSlide({ slide, slideIndex, totalSlides }) {
  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.eyebrow || 'Workflow'}>
      <div className="grid h-full min-h-0 grid-rows-[100px_minmax(0,1fr)] gap-6">
        <div>
          <p className="mb-3 text-xs uppercase tracking-[0.32em] text-[#2f855a]">{slide.eyebrow}</p>
          <MarkdownMath content={slide.title} className="max-w-3xl text-[42px] font-semibold leading-tight text-[var(--text-primary)]" />
          <MarkdownMath content={slide.subtitle} className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]" />
        </div>

        <div className="relative min-h-0 overflow-hidden">
        {(slide.steps || []).map((step, index) => (
          <div key={`${index}-${step.title}`} className="relative pb-6 pl-14 last:pb-0">
            {index < (slide.steps || []).length - 1 ? (
              <div className="absolute bottom-0 left-[19px] top-10 w-px bg-[linear-gradient(180deg,#3258ff_0%,#0ea5a4_45%,rgba(212,167,44,0)_100%)]" />
            ) : null}

            <div
              className="absolute left-0 top-1 flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,88,255,0.2)]"
              style={{ backgroundColor: getChartColor(index) }}
            >
              {index + 1}
            </div>

            <div className="rounded-[28px] border border-[var(--border)] bg-white px-5 py-5 shadow-[0_16px_36px_rgba(15,23,42,0.05)]">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <MarkdownMath content={step.title} className="text-xl font-semibold text-[var(--text-primary)]" />
                  <MarkdownMath content={step.detail} className="mt-2 max-w-3xl text-sm text-[var(--text-secondary)]" />
                </div>
                <div className="inline-flex items-center justify-center rounded-full bg-slate-950 px-3 py-1.5 text-xs uppercase tracking-[0.24em] text-white">
                  {step.signal}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      </div>
    </SlideFrame>
  )
}

function TrendSlide({ slide, chartId, slideIndex, totalSlides }) {
  const xAxisProps = buildCategoryAxisProps(slide.data || [], 'label', { maxVisible: 7, maxLength: 12 })

  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.stage || 'Trend'}>
      <div className="grid h-full min-h-0 grid-rows-[96px_minmax(0,1fr)] gap-5">
        <div>
          <MarkdownMath content={slide.title} className="text-[34px] font-semibold text-[var(--text-primary)]" />
          <MarkdownMath content={slide.subtitle} className="mt-2 text-sm leading-6 text-[var(--text-secondary)]" />
        </div>

        <div className="min-h-0 rounded-[28px] border border-[var(--border)] bg-white p-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={slide.data || []} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={chartId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3258ff" stopOpacity={0.42} />
                <stop offset="95%" stopColor="#3258ff" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
              <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} {...xAxisProps} />
            <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              name={slide.value_label || 'valor'}
              stroke="#3258ff"
              fill={`url(#${chartId})`}
              strokeWidth={3}
            />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </SlideFrame>
  )
}

function TableFocusSlide({ slide, slideIndex, totalSlides }) {
  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.stage || 'Action Plan'}>
      <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-6">
        <div className="grid min-h-0 grid-rows-[104px_minmax(0,1fr)] gap-5">
          <div>
            <MarkdownMath
              content={slide.question || slide.title}
              className="max-w-4xl text-[34px] font-semibold leading-tight text-[var(--text-primary)]"
            />
            <MarkdownMath
              content={slide.title !== slide.question ? `${slide.title}. ${slide.subtitle}` : slide.subtitle}
              className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]"
            />
          </div>

          <div className="grid min-h-0 grid-cols-2 gap-4">
            {(slide.tables || []).map((table, index) => (
              <div
                key={`${table.name}-${index}`}
                className="rounded-[28px] border border-[var(--border)] bg-white p-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]"
              >
                <div className="flex items-center justify-between gap-3">
                  <MarkdownMath content={table.name} className="text-xl font-semibold text-[var(--text-primary)]" inline />
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: getChartColor(index) }}
                  />
                </div>
                <MarkdownMath content={table.detail} className="mt-2 text-sm leading-6 text-[var(--text-secondary)]" />
                <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1.5 text-xs text-white">
                  Campo destacado
                  <MarkdownMath
                    content={table.highlight}
                    inline
                    className="font-semibold"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="min-h-0 overflow-hidden">
          <StoryStack slide={slide} />
        </div>
      </div>
    </SlideFrame>
  )
}

function RichTextSlide({ slide, slideIndex, totalSlides }) {
  const callouts = Array.isArray(slide.callouts) ? slide.callouts.slice(0, 4) : []

  return (
    <SlideFrame slideIndex={slideIndex} totalSlides={totalSlides} stage={slide.stage || 'Insight'}>
      <div className="grid h-full min-h-0 grid-cols-[minmax(0,1.2fr)_320px] gap-6">
        <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-5">
          <div>
            <MarkdownMath content={slide.title} className="text-[38px] font-semibold leading-tight text-[var(--text-primary)]" />
            {slide.subtitle ? (
              <MarkdownMath content={slide.subtitle} className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]" />
            ) : null}
          </div>

          <div className="min-h-0 rounded-[28px] border border-[var(--border)] bg-white px-6 py-6 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
            <MarkdownMath content={slide.body} className="text-base leading-8 text-[var(--text-primary)]" />
          </div>
        </div>

        <div className="grid min-h-0 auto-rows-max content-start gap-4">
          {callouts.length ? (
            callouts.map((callout, index) => (
              <div
                key={`${callout.label}-${index}`}
                className="self-start rounded-[24px] border border-[var(--border)] bg-white px-5 py-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]"
                style={{ boxShadow: `inset 3px 0 0 ${getChartColor(index)}` }}
              >
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
                  {callout.label}
                </p>
                <MarkdownMath content={callout.value} className="mt-3 text-sm leading-6 text-[var(--text-primary)]" />
              </div>
            ))
          ) : (
            <div className="self-start rounded-[24px] border border-[var(--border)] bg-[rgba(248,244,238,0.72)] px-5 py-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
                Lectura
              </p>
              <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">
                Esta diapositiva se adapto a la pregunta y solo aparece cuando aporta contexto adicional.
              </p>
            </div>
          )}
        </div>
      </div>
    </SlideFrame>
  )
}

export default function PresentationDeck({ slides = [] }) {
  const normalizedSlides = normalizePresentationSlides(slides)

  if (!normalizedSlides.length) {
    return (
      <div className="rounded-[32px] border border-dashed border-[var(--border)] bg-white p-8 text-center text-[var(--text-secondary)]">
        Aun no hay slides para esta lectura.
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-[1880px] flex-col gap-10 pb-10">
      {normalizedSlides.map((slide, index) => {
        const sharedProps = {
          slideIndex: index,
          totalSlides: normalizedSlides.length,
        }

        if (slide.type === 'index') return <IndexSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        if (slide.type === 'workflow') return <WorkflowSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        if (slide.type === 'chart') return <AnalyticsChartSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        if (slide.type === 'hero') return <HeroSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        if (slide.type === 'trend') {
          return (
            <TrendSlide
              key={`${slide.type}-${index}`}
              slide={slide}
              chartId={`presentation-area-${index}`}
              {...sharedProps}
            />
          )
        }
        if (slide.type === 'rich_text') return <RichTextSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        if (slide.type === 'table_focus') return <TableFocusSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
        return <BarChartSlide key={`${slide.type}-${index}`} slide={slide} {...sharedProps} />
      })}
    </div>
  )
}

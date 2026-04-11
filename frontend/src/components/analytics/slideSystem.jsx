'use client'

import { useEffect, useRef, useState } from 'react'

export const SLIDE_WIDTH = 1600
export const SLIDE_HEIGHT = 900

function joinClasses(...parts) {
  return parts.filter(Boolean).join(' ')
}

export function clampTextStyle(lines = 4) {
  return {
    display: '-webkit-box',
    WebkitLineClamp: lines,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  }
}

export function shortenLabel(value, maxLength = 14) {
  const text = String(value ?? '')
  if (text.length <= maxLength) return text
  return `${text.slice(0, Math.max(4, maxLength - 1)).trim()}…`
}

export function buildCategoryAxisProps(data = [], key = 'label', options = {}) {
  const values = (data || []).map((item) => String(item?.[key] ?? ''))
  const total = values.length
  const maxVisible = options.maxVisible ?? 6
  const maxLength = options.maxLength ?? 14
  const interval = total <= maxVisible ? 0 : Math.max(0, Math.ceil(total / maxVisible) - 1)
  const rotate = total >= (options.rotateThreshold ?? 8)

  return {
    interval,
    minTickGap: total > maxVisible ? 18 : 8,
    tickFormatter: (value) => shortenLabel(value, maxLength),
    angle: rotate ? -18 : 0,
    textAnchor: rotate ? 'end' : 'middle',
    height: rotate ? 54 : 28,
  }
}

export function getNarrativePanels(slide, limit = 3) {
  const panels = []

  if (slide.finding) {
    panels.push({ title: 'Hallazgo', body: slide.finding, tone: 'accent' })
  }
  if (slide.conclusion) {
    panels.push({ title: 'Conclusion', body: slide.conclusion, tone: 'light' })
  }
  if (slide.recommendation) {
    panels.push({ title: 'Accion', body: slide.recommendation, tone: 'dark' })
  }
  if (slide.complication) {
    panels.push({ title: 'Complicacion', body: slide.complication, tone: 'light' })
  }

  return panels.slice(0, limit)
}

export function SlideCanvas({
  children,
  stage = 'Story',
  slideIndex = 0,
  totalSlides = 1,
  contentClassName = '',
  surfaceClassName = '',
}) {
  const hostRef = useRef(null)
  const frameRef = useRef(null)
  const [renderWidth, setRenderWidth] = useState(SLIDE_WIDTH)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return undefined

    const updateSize = () => {
      const measuredWidth = Math.round(host.clientWidth || SLIDE_WIDTH)
      const nextWidth = Math.max(320, Math.min(measuredWidth, SLIDE_WIDTH))
      setRenderWidth((currentWidth) => (
        Math.abs(currentWidth - nextWidth) >= 1 ? nextWidth : currentWidth
      ))
    }

    const scheduleUpdate = () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current)
      }
      frameRef.current = requestAnimationFrame(() => {
        frameRef.current = null
        updateSize()
      })
    }

    updateSize()

    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', scheduleUpdate)
      return () => {
        window.removeEventListener('resize', scheduleUpdate)
        if (frameRef.current) {
          cancelAnimationFrame(frameRef.current)
        }
      }
    }

    const observer = new ResizeObserver(scheduleUpdate)
    observer.observe(host)
    return () => {
      observer.disconnect()
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current)
      }
    }
  }, [])

  const scale = renderWidth / SLIDE_WIDTH

  return (
    <div ref={hostRef} className="w-full">
      <div
        className="relative mx-auto"
        style={{ width: renderWidth, height: SLIDE_HEIGHT * scale }}
      >
        <article
          className={joinClasses(
            'absolute left-0 top-0 overflow-hidden rounded-[36px] border border-[var(--border)] bg-[linear-gradient(180deg,#ffffff_0%,#fbfcff_100%)] shadow-[0_28px_90px_rgba(15,23,42,0.12)]',
            surfaceClassName,
          )}
          style={{
            width: SLIDE_WIDTH,
            height: SLIDE_HEIGHT,
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
          }}
        >
          <div className="absolute -left-18 top-12 h-44 w-44 rounded-full bg-[rgba(50,88,255,0.08)] blur-3xl" />
          <div className="absolute -right-12 bottom-8 h-40 w-40 rounded-full bg-[rgba(14,165,164,0.08)] blur-3xl" />
          <div className="absolute inset-x-0 top-0 h-1 bg-[linear-gradient(90deg,#3258ff_0%,#0ea5a4_28%,#f46d43_54%,#8b5cf6_82%,#d4a72c_100%)]" />
          <div className="absolute right-10 top-10 flex items-center gap-3">
            <span className="inline-flex rounded-full bg-[rgba(50,88,255,0.08)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--accent-indigo)]">
              {stage}
            </span>
            <span className="inline-flex rounded-full border border-[var(--border)] bg-white/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--text-muted)]">
              {String(slideIndex + 1).padStart(2, '0')} / {String(totalSlides).padStart(2, '0')}
            </span>
          </div>
          <div className={joinClasses('relative grid h-full min-h-0 p-10', contentClassName)}>
            {children}
          </div>
        </article>
      </div>
    </div>
  )
}

'use client'

import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Columns3, KeyRound, Link2 } from 'lucide-react'

const CARD_WIDTH = 320
const COLUMN_GAP = 120
const ROW_GAP = 72
const PADDING = 28

const typeClasses = {
  integer: 'border-[#d8e5ff] bg-[#edf3ff] text-[#3258ff]',
  decimal: 'border-[#cceae7] bg-[#edf9f8] text-[#0ea5a4]',
  boolean: 'border-[#dcebe6] bg-[#eef8f3] text-[#2f855a]',
  datetime: 'border-[#eadcff] bg-[#f5efff] text-[#8b5cf6]',
  string: 'border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)]',
  text: 'border-[#f0e0b2] bg-[#fff8e8] text-[#9a6700]',
  unknown: 'border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-muted)]',
}

function estimateCardHeight(table) {
  return 130 + table.columns.length * 34 + 16
}

function buildLayout(tables) {
  const columns = tables.length >= 7 ? 3 : tables.length >= 3 ? 2 : 1
  const columnHeights = new Array(columns).fill(PADDING)

  return tables.map((table, index) => {
    const columnIndex = index % columns
    const height = estimateCardHeight(table)
    const x = PADDING + columnIndex * (CARD_WIDTH + COLUMN_GAP)
    const y = columnHeights[columnIndex]
    columnHeights[columnIndex] += height + ROW_GAP

    return {
      ...table,
      layout: {
        x,
        y,
        height,
      },
    }
  })
}

function confidenceColor(confidence) {
  if (confidence >= 0.95) return '#3258ff'
  if (confidence >= 0.85) return '#0ea5a4'
  return '#94a3b8'
}

export default function SchemaDiagram({ tables = [], relationships = [] }) {
  const containerRef = useRef(null)
  const nodeRefs = useRef({})
  const [paths, setPaths] = useState([])

  const positionedTables = useMemo(
    () => buildLayout([...tables].sort((a, b) => a.name.localeCompare(b.name))),
    [tables]
  )

  const surfaceSize = useMemo(() => {
    if (!positionedTables.length) {
      return { width: 0, height: 0 }
    }

    const width = Math.max(...positionedTables.map((table) => table.layout.x + CARD_WIDTH)) + PADDING
    const height = Math.max(...positionedTables.map((table) => table.layout.y + table.layout.height)) + PADDING

    return { width, height }
  }, [positionedTables])

  useLayoutEffect(() => {
    const measure = () => {
      if (!containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const nextPaths = relationships
        .map((relationship) => {
          const sourceCard = nodeRefs.current[relationship.source_table_name]
          const targetCard = nodeRefs.current[relationship.target_table_name]

          if (!sourceCard || !targetCard) return null

          const sourceRow =
            sourceCard.querySelector(`[data-column="${relationship.source_column_name}"]`) || sourceCard
          const targetRow =
            targetCard.querySelector(`[data-column="${relationship.target_column_name}"]`) || targetCard

          const sourceRect = sourceRow.getBoundingClientRect()
          const targetRect = targetRow.getBoundingClientRect()
          const sourceOnLeft = sourceRect.left <= targetRect.left

          const startX = sourceOnLeft
            ? sourceRect.right - containerRect.left
            : sourceRect.left - containerRect.left
          const endX = sourceOnLeft
            ? targetRect.left - containerRect.left
            : targetRect.right - containerRect.left
          const startY = sourceRect.top - containerRect.top + sourceRect.height / 2
          const endY = targetRect.top - containerRect.top + targetRect.height / 2
          const curveOffset = Math.max(72, Math.abs(endX - startX) / 2)
          const controlX = sourceOnLeft ? startX + curveOffset : startX - curveOffset
          const targetControlX = sourceOnLeft ? endX - curveOffset : endX + curveOffset

          return {
            key: `${relationship.source_table_name}-${relationship.source_column_name}-${relationship.target_table_name}-${relationship.target_column_name}`,
            d: `M ${startX} ${startY} C ${controlX} ${startY}, ${targetControlX} ${endY}, ${endX} ${endY}`,
            color: confidenceColor(relationship.confidence),
          }
        })
        .filter(Boolean)

      setPaths(nextPaths)
    }

    const frame = requestAnimationFrame(measure)
    window.addEventListener('resize', measure)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', measure)
    }
  }, [positionedTables, relationships])

  if (!tables.length) {
    return (
      <div className="rounded-3xl border border-dashed border-[var(--border)] bg-white p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--surface-muted)] text-[var(--text-muted)]">
          <Columns3 size={20} />
        </div>
        <h3 className="mb-2 font-semibold text-[var(--text-primary)]">Aun no hay schema para mostrar</h3>
        <p className="mx-auto max-w-lg text-sm text-[var(--text-secondary)]">
          Sube uno o varios archivos tabulares y Lumiq inferira tablas, columnas y relaciones del
          negocio.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-auto rounded-3xl border border-[var(--border)] bg-white shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
      <div
        ref={containerRef}
        className="relative"
        style={{
          width: `${surfaceSize.width}px`,
          height: `${surfaceSize.height}px`,
          backgroundImage:
            'radial-gradient(circle at 1px 1px, rgba(148,163,184,0.18) 1px, transparent 0)',
          backgroundSize: '24px 24px',
        }}
      >
        <svg className="pointer-events-none absolute inset-0" width={surfaceSize.width} height={surfaceSize.height}>
          <defs>
            <marker
              id="schema-arrow"
              markerWidth="10"
              markerHeight="10"
              refX="8"
              refY="5"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3258ff" />
            </marker>
          </defs>

          {paths.map((path) => (
            <path
              key={path.key}
              d={path.d}
              stroke={path.color}
              strokeWidth="2.25"
              fill="none"
              strokeDasharray="7 6"
              markerEnd="url(#schema-arrow)"
              opacity="0.95"
            />
          ))}
        </svg>

        {positionedTables.map((table) => (
          <section
            key={table.id}
            ref={(element) => {
              nodeRefs.current[table.name] = element
            }}
            className="absolute rounded-3xl border border-[var(--border)] bg-white shadow-[0_18px_44px_rgba(15,23,42,0.08)]"
            style={{
              width: `${CARD_WIDTH}px`,
              left: `${table.layout.x}px`,
              top: `${table.layout.y}px`,
            }}
          >
            <div className="rounded-t-3xl border-b border-slate-900/10 bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] px-5 py-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{table.name}</p>
                  <p className="mt-1 text-xs text-slate-400">{table.source_file}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-semibold text-white">{table.row_count.toLocaleString()}</p>
                  <p className="text-[11px] text-slate-400">filas</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-3 text-[11px] text-[var(--text-muted)]">
              <span>{table.column_count} columnas</span>
              <span>PK: {table.primary_key_name || 'no detectada'}</span>
            </div>

            <div className="space-y-1 px-3 py-3">
              {table.columns.map((column) => (
                <div
                  key={column.id}
                  data-column={column.name}
                  className="flex items-center justify-between gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="flex min-w-0 items-center gap-2">
                      {column.is_primary_key ? (
                        <KeyRound size={13} className="shrink-0 text-[#d4a72c]" />
                      ) : (
                        <Link2 size={13} className="shrink-0 text-slate-400" />
                      )}
                      <span className="truncate text-sm text-[var(--text-primary)]">{column.name}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                      {column.is_nullable ? 'nullable' : 'required'}
                      {' | '}
                      unicos {Math.round((column.uniqueness_ratio || 0) * 100)}%
                    </p>
                  </div>

                  <span
                    className={`whitespace-nowrap rounded-full border px-2 py-1 text-[11px] font-medium ${
                      typeClasses[column.inferred_type] || typeClasses.unknown
                    }`}
                  >
                    {column.inferred_type}
                  </span>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

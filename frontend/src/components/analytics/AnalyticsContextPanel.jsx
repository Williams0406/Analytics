'use client'

const FIELD_ROLE_LABELS = {
  primary_key: 'PK',
  measure: 'medida',
  date: 'fecha',
  dimension: 'dimension',
  quality: 'calidad',
}

const ANALYSIS_MODE_LABELS = {
  quality: 'calidad',
  numeric: 'numerico',
  categorical: 'categorico',
  time_series: 'serie temporal',
  correlation: 'correlacion',
  outliers: 'outliers',
  text: 'texto',
  scatter: 'scatter',
  heatmap: 'heatmap',
  flow: 'flujo',
  geo: 'geo',
  treemap: 'treemap',
  radar: 'radar',
}

function SummaryMetric({ label, value }) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 shadow-[0_10px_28px_rgba(15,23,42,0.04)]">
      <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">{label}</p>
      <p className="mt-2 text-lg font-semibold text-[var(--text-primary)]">{value}</p>
    </div>
  )
}

export default function AnalyticsContextPanel({ context }) {
  if (!context?.tables?.length) return null

  const summary = context.summary || {}

  return (
    <section className="mb-6 space-y-5">
      <div className="rounded-[32px] border border-[var(--border)] bg-white p-6 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="mb-3 text-xs uppercase tracking-[0.32em] text-[#0ea5a4]">Dataset Context</p>
            <h3 className="text-3xl font-semibold text-[var(--text-primary)]">
              Lo que Lumiq entiende de tu dataset
            </h3>
            <p className="mt-3 max-w-3xl text-sm text-[var(--text-secondary)]">
              Antes de generar la presentacion, esta es la lectura estructural y semantica que la
              plataforma hizo de tus tablas y campos.
            </p>
          </div>

          {!!context.relationships?.length && (
            <div className="rounded-2xl border border-[var(--border)] bg-[rgba(248,244,238,0.78)] px-4 py-3 xl:max-w-md">
              <p className="mb-2 text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
                Relaciones detectadas
              </p>
              <div className="space-y-2">
                {context.relationships.slice(0, 3).map((relationship) => (
                  <p
                    key={`${relationship.source_table_name}-${relationship.source_column_name}-${relationship.target_table_name}`}
                    className="text-sm text-[var(--text-secondary)]"
                  >
                    {relationship.source_table_name}.{relationship.source_column_name} -&gt;{' '}
                    {relationship.target_table_name}.{relationship.target_column_name}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 xl:grid-cols-5">
          <SummaryMetric label="Tablas" value={summary.tables_count || 0} />
          <SummaryMetric label="Filas" value={Number(summary.total_rows || 0).toLocaleString()} />
          <SummaryMetric label="Columnas" value={summary.total_columns || 0} />
          <SummaryMetric
            label="Completitud"
            value={`${Number((summary.completeness_ratio || 0) * 100).toFixed(1)}%`}
          />
          <SummaryMetric
            label="Lentes"
            value={(summary.available_lenses || []).slice(0, 3).join(', ') || 'quality'}
          />
        </div>
      </div>

      <div className="space-y-4">
        {context.tables.map((table) => (
          <article
            key={table.name}
            className="rounded-[32px] border border-[var(--border)] bg-white p-6 shadow-[0_20px_48px_rgba(15,23,42,0.06)]"
          >
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h4 className="text-2xl font-semibold text-[var(--text-primary)]">{table.name}</h4>
                  {table.source_file ? (
                    <span className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2 py-1 text-[11px] text-[var(--text-secondary)]">
                      {table.source_file}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm text-[var(--text-secondary)]">
                  {Number(table.row_count || 0).toLocaleString()} filas | {table.column_count} columnas
                  {' | '}PK {table.primary_key_name || 'no detectada'}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {table.focus_measure_column ? (
                  <span className="rounded-full border border-[#d7dcff] bg-[#eef1ff] px-2 py-1 text-[11px] text-[#3258ff]">
                    Medida: {table.focus_measure_column}
                  </span>
                ) : null}
                {table.focus_date_column ? (
                  <span className="rounded-full border border-[#cceae7] bg-[#edf9f8] px-2 py-1 text-[11px] text-[#0ea5a4]">
                    Fecha: {table.focus_date_column}
                  </span>
                ) : null}
                {(table.analysis_modes || []).slice(0, 6).map((mode) => (
                  <span
                    key={mode}
                    className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2 py-1 text-[11px] text-[var(--text-secondary)]"
                  >
                    {ANALYSIS_MODE_LABELS[mode] || mode}
                  </span>
                ))}
              </div>
            </div>

            {!!table.field_highlights?.length && (
              <div className="mt-5 grid grid-cols-1 gap-3 xl:grid-cols-2">
                {table.field_highlights.map((item) => (
                  <div
                    key={`${table.name}-${item.column}-${item.role}`}
                    className="rounded-2xl border border-[var(--border)] bg-[rgba(248,244,238,0.65)] px-4 py-3"
                  >
                    <p className="text-sm font-medium text-[var(--text-primary)]">{item.column}</p>
                    <p className="mt-1 text-[11px] uppercase tracking-[0.24em] text-[#0ea5a4]">
                      {item.role}
                    </p>
                    <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                      {item.detail}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-5">
              <p className="mb-3 text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                Campos detectados
              </p>
              <div className="grid max-h-[520px] grid-cols-1 gap-3 overflow-auto pr-1 md:grid-cols-2 2xl:grid-cols-3">
                {(table.fields || []).map((field) => (
                  <div
                    key={`${table.name}-${field.name}`}
                    className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-[var(--text-primary)]">{field.name}</p>
                      <span className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2 py-1 text-[11px] text-[var(--text-secondary)]">
                        {field.inferred_type}
                      </span>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {(field.roles || []).map((role) => (
                        <span
                          key={`${field.name}-${role}`}
                          className="rounded-full border border-[#dcebe6] bg-[#eef8f3] px-2 py-1 text-[10px] text-[#2f855a]"
                        >
                          {FIELD_ROLE_LABELS[role] || role}
                        </span>
                      ))}
                      {field.is_nullable ? (
                        <span className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2 py-1 text-[10px] text-[var(--text-muted)]">
                          nullable
                        </span>
                      ) : null}
                    </div>

                    <p className="mt-3 text-xs text-[var(--text-secondary)]">
                      Unicidad {Number((field.uniqueness_ratio || 0) * 100).toFixed(1)}% | vacios{' '}
                      {Number(field.null_count || 0).toLocaleString()}
                    </p>

                    {!!field.sample_values?.length && (
                      <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                        Ejemplo: {field.sample_values.join(' | ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

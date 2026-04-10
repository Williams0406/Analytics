'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Database, FolderKanban, Sparkles } from 'lucide-react'

import apiClient from '@/lib/axios'
import { getStoredUser } from '@/lib/auth'
import DatasetStatCard from '@/components/dashboard/DatasetStatCard'
import InsightBarChart from '@/components/dashboard/InsightBarChart'
import TypeMixChart from '@/components/dashboard/TypeMixChart'
import Navbar from '@/components/layout/Navbar'
import Badge from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'

const ANALYSIS_MODE_LABELS = {
  quality: 'calidad',
  numeric: 'numerico',
  categorical: 'categorico',
  time_series: 'serie temporal',
  seasonality: 'estacionalidad',
  correlation: 'correlacion',
  outliers: 'outliers',
  text: 'texto',
  clusters: 'clusters',
  contribution: 'contribucion',
  scatter: 'scatter',
  heatmap: 'heatmap',
  flow: 'flujo',
  geo: 'geo',
  treemap: 'treemap',
  radar: 'radar',
}

export default function DashboardPage() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const user = getStoredUser()

  useEffect(() => {
    apiClient.get('/api/analytics/dashboard/')
      .then(({ data }) => setPayload(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <Navbar title="Dashboard" />

      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Vista Ejecutiva"
          icon={Sparkles}
          title={`Hola, ${user?.first_name || 'equipo'}`}
          description={payload?.subheadline || 'Estamos preparando una lectura ejecutiva de tu base de datos.'}
          actions={
            <>
              <Link
                href="/dashboard/connectors"
                className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                Ir a Conectores
              </Link>
              <Link
                href="/dashboard/analytics"
                className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
              >
                Abrir Analytics
              </Link>
            </>
          }
          meta={
            <Card className="min-w-[280px] shadow-[var(--shadow-sm)]">
              <CardContent className="px-4 py-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                    Fuente activa
                  </p>
                  <Badge variant={payload?.source === 'dataset' ? 'info' : 'neutral'}>
                    {payload?.source === 'dataset' ? 'Dataset real' : 'Modo demo'}
                  </Badge>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white shadow-[var(--shadow-sm)]">
                    <Database size={16} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                      {payload?.dataset_import?.name || 'Modo demo'}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                      {payload?.source === 'dataset'
                        ? 'Dashboard generado desde tu upload mas reciente'
                        : 'Sube un dataset en Conectores para reemplazar el demo'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          }
        />

        <div className="mb-6 grid grid-cols-2 gap-4 xl:grid-cols-4">
          {(loading ? Array(4).fill(null) : payload?.kpis || []).map((item, index) => (
            <DatasetStatCard
              key={item?.metric_type || index}
              label={item?.label}
              value={item?.value}
              unit={item?.unit}
              caption={item?.caption}
              loading={loading}
            />
          ))}
        </div>

        <div className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.95fr)]">
          <InsightBarChart
            title={payload?.primary_chart?.title}
            subtitle={payload?.primary_chart?.subtitle}
            data={payload?.primary_chart?.data || []}
            valueLabel={payload?.primary_chart?.value_label}
            secondaryLabel={payload?.primary_chart?.secondary_label}
          />

          {payload?.type_distribution ? (
            <TypeMixChart
              title={payload.type_distribution.title}
              data={payload.type_distribution.data}
            />
          ) : (
            <EmptyState
              icon={FolderKanban}
              title="Activa tu dataset"
              description="Cuando subas tus archivos en Conectores, Lumiq mostrara aqui el mix de columnas, la calidad del dato y la topologia de tus tablas."
              action={
                <Link
                  href="/dashboard/connectors"
                  className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
                >
                  Cargar datos
                </Link>
              }
            />
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
          {payload?.secondary_chart ? (
            <InsightBarChart
              title={payload.secondary_chart.title}
              subtitle={payload.secondary_chart.subtitle}
              data={payload.secondary_chart.data}
              valueLabel={payload.secondary_chart.value_label}
              color="#0ea5a4"
            />
          ) : (
            <EmptyState
              icon={FolderKanban}
              title="Siguiente paso recomendado"
              description="Carga uno o varios CSV o Excel desde Conectores. Lumiq inferira relaciones, construira el dashboard y dara contexto real a AI Insights."
              action={
                <Link
                  href="/dashboard/connectors"
                  className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
                >
                  Ir a Conectores
                </Link>
              }
            />
          )}

          <Card className="shadow-[var(--shadow-md)]">
            <CardContent className="px-5 py-5">
              <div className="mb-4 flex items-center gap-2">
                <Sparkles size={16} className="text-[var(--accent-indigo)]" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Lo mas relevante</h3>
              </div>

              <div className="mb-6 space-y-3">
                {(payload?.insights || []).map((insight, index) => (
                  <div
                    key={`${index}-${insight}`}
                    className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--text-secondary)]"
                    style={{ boxShadow: `inset 3px 0 0 ${['#3258ff', '#0ea5a4', '#f46d43', '#8b5cf6'][index % 4]}` }}
                  >
                    {insight}
                  </div>
                ))}
              </div>

              {!!payload?.table_spotlights?.length && (
                <div className="space-y-3">
                  {payload.table_spotlights.map((table) => (
                    <div
                      key={table.name}
                      className="rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-[var(--text-primary)]">{table.name}</p>
                        <span className="text-xs text-[var(--text-muted)]">
                          {table.row_count.toLocaleString()} filas
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--text-secondary)]">
                        {table.column_count} columnas | PK {table.primary_key_name || 'no detectada'}
                      </p>

                      {!!table.focus_measure_column && (
                        <p className="mt-2 text-[11px] text-[var(--accent-indigo)]">
                          Medida foco: {table.focus_measure_column}
                        </p>
                      )}

                      {!!table.analysis_modes?.length && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {table.analysis_modes.slice(0, 4).map((mode) => (
                            <Badge key={mode} variant="neutral">
                              {ANALYSIS_MODE_LABELS[mode] || mode}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {!!table.recommended_analyses?.length && (
                        <div className="mt-3 space-y-2">
                          {table.recommended_analyses.slice(0, 2).map((analysis) => (
                            <p key={analysis} className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
                              {analysis}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  )
}

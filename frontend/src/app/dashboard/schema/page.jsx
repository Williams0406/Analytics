'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, Database, GitBranch, RefreshCw, Table2, Trash2 } from 'lucide-react'

import AnalyticsContextPanel from '@/components/analytics/AnalyticsContextPanel'
import Navbar from '@/components/layout/Navbar'
import SchemaDiagram from '@/components/schema/SchemaDiagram'
import PageHeader from '@/components/ui/PageHeader'
import SegmentedControl from '@/components/ui/SegmentedControl'
import apiClient from '@/lib/axios'
import { buildDatasetContextFromImport } from '@/lib/datasetContext'

export default function SchemaPage() {
  const [imports, setImports] = useState([])
  const [activeImport, setActiveImport] = useState(null)
  const [selectedImportId, setSelectedImportId] = useState(null)
  const [viewMode, setViewMode] = useState('context')
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState('')

  const stats = useMemo(() => {
    if (!activeImport) return []

    const totalColumns = (activeImport.tables || []).reduce(
      (sum, table) => sum + table.column_count,
      0
    )

    return [
      {
        label: 'Tablas',
        value: activeImport.tables_count,
        icon: Table2,
      },
      {
        label: 'Relaciones',
        value: activeImport.relationships_count,
        icon: GitBranch,
      },
      {
        label: 'Columnas',
        value: totalColumns,
        icon: Database,
      },
    ]
  }, [activeImport])

  const datasetContext = useMemo(
    () => buildDatasetContextFromImport(activeImport),
    [activeImport]
  )

  const loadImportDetail = async (id) => {
    const { data } = await apiClient.get(`/api/datasets/imports/${id}/`)
    setSelectedImportId(id)
    setActiveImport(data)
    return data
  }

  const loadImports = async (preferredImportId = null, { silent = false } = {}) => {
    if (!silent) {
      setLoading(true)
    }
    setError('')

    try {
      const { data } = await apiClient.get('/api/datasets/imports/')
      const nextImports = Array.isArray(data) ? data : data.results || []
      setImports(nextImports)

      const targetId =
        preferredImportId ||
        nextImports.find((item) => item.status === 'ready')?.id ||
        nextImports[0]?.id
      if (targetId) {
        await loadImportDetail(targetId)
      } else {
        setSelectedImportId(null)
        setActiveImport(null)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudieron cargar tus imports.')
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadImports()
  }, [])

  useEffect(() => {
    const hasProcessingImports =
      imports.some((item) => item.status === 'processing') ||
      activeImport?.status === 'processing'
    if (!hasProcessingImports) return undefined

    const pollId = window.setInterval(() => {
      loadImports(selectedImportId, { silent: true }).catch(console.error)
    }, 4000)

    return () => window.clearInterval(pollId)
  }, [imports, activeImport?.status, selectedImportId])

  const handleDeleteImport = async (datasetImport) => {
    const confirmed = window.confirm(
      `Se eliminara "${datasetImport.name}" y todo su schema inferido. Esta accion no se puede deshacer.`
    )

    if (!confirmed) return

    setDeletingId(datasetImport.id)
    setError('')

    try {
      await apiClient.delete(`/api/datasets/imports/${datasetImport.id}/`)
      const nextPreferredId = selectedImportId === datasetImport.id ? null : selectedImportId
      await loadImports(nextPreferredId)
    } catch (err) {
      setError(
        err.response?.data?.error ||
          'No se pudo eliminar el dataset seleccionado.'
      )
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <Navbar title="Schema del Negocio" />

      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Modelo de Datos"
          icon={Database}
          title="Schema inferido del negocio"
          description="Aqui inspeccionas las tablas, columnas y relaciones detectadas a partir de los datasets que cargas en la vista Conectores."
          actions={
            <>
              <button
                onClick={() => loadImports(selectedImportId)}
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] bg-white px-3 py-2 text-xs text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]"
              >
                <RefreshCw size={13} />
                Actualizar vista
              </button>
              <Link
                href="/dashboard/connectors"
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--surface-dark)] px-3 py-2 text-xs text-white transition hover:bg-[#111a22]"
              >
                Cargar datos
                <ArrowRight size={13} />
              </Link>
            </>
          }
        />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
          <div className="space-y-6">
            <section className="rounded-3xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Imports recientes</h3>
                  <p className="text-xs text-[var(--text-secondary)]">
                    Selecciona una version para explorar su schema.
                  </p>
                </div>
                <span className="text-xs text-[var(--text-muted)]">{imports.length}</span>
              </div>

              {error && (
                <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-3">
                {loading ? (
                  Array(3).fill(0).map((_, index) => (
                    <div
                      key={index}
                      className="h-20 animate-pulse rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)]"
                    />
                  ))
                ) : imports.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface-muted)] p-4">
                    <p className="text-sm text-[var(--text-primary)]">
                      Aun no has cargado datasets en este workspace.
                    </p>
                    <p className="mt-2 text-xs text-[var(--text-secondary)]">
                      Empieza en Conectores con un CSV, TSV o Excel y aqui veras el modelo inferido.
                    </p>
                    <Link
                      href="/dashboard/connectors"
                      className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[var(--surface-dark)] px-4 py-2.5 text-sm text-white transition hover:bg-[#111a22]"
                    >
                      Ir a Conectores
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                ) : (
                  imports.map((item) => (
                    <div
                      key={item.id}
                      className={`w-full rounded-2xl border p-4 text-left transition ${
                        selectedImportId === item.id
                          ? 'border-[#d7dcff] bg-[#eef1ff]'
                          : 'border-[var(--border)] bg-white hover:border-[var(--border-strong)]'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-[var(--text-primary)]">{item.name}</p>
                          <p className="mt-1 text-xs text-[var(--text-secondary)]">
                            {new Date(item.created_at).toLocaleString('es-PE')}
                          </p>
                        </div>
                        <span className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2 py-1 text-[11px] uppercase text-[var(--text-secondary)]">
                          {item.status}
                        </span>
                      </div>

                      <div className="mt-3 flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                        <span>{item.file_count} archivos</span>
                        <span>{item.tables_count} tablas</span>
                        <span>{item.relationships_count} relaciones</span>
                      </div>

                      <div className="mt-4 flex flex-wrap justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => loadImportDetail(item.id)}
                          className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-xs text-[var(--text-primary)] transition hover:border-[var(--border-strong)]"
                        >
                          Ver schema
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteImport(item)}
                          disabled={deletingId === item.id || item.status === 'processing'}
                          className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 transition hover:bg-red-100 disabled:opacity-50"
                        >
                          <Trash2 size={13} />
                          {item.status === 'processing'
                            ? 'En procesamiento'
                            : deletingId === item.id
                              ? 'Eliminando...'
                              : 'Eliminar'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>

          <div className="min-w-0 space-y-6">
            {activeImport && (
              <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {stats.map((stat) => {
                  const Icon = stat.icon
                  return (
                    <div
                      key={stat.label}
                      className="rounded-3xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]"
                    >
                      <div className="mb-4 flex items-center justify-between">
                        <p className="text-sm text-[var(--text-secondary)]">{stat.label}</p>
                        <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white">
                          <Icon size={15} />
                        </div>
                      </div>
                      <p className="text-3xl font-bold text-[var(--text-primary)]">{stat.value}</p>
                    </div>
                  )
                })}
              </section>
            )}

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-[var(--text-primary)]">Explorador del schema</h3>
                  <p className="text-sm text-[var(--text-secondary)]">
                    {activeImport
                      ? `Vista inferida para "${activeImport.name}".`
                      : 'Carga un dataset en Conectores para empezar.'}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <SegmentedControl
                    value={viewMode}
                    onChange={setViewMode}
                    options={[
                      { value: 'context', label: 'Contexto' },
                      { value: 'diagram', label: 'Diagrama' },
                    ]}
                  />

                  {activeImport && (
                    <div className="text-right text-xs text-[var(--text-muted)]">
                      <p>{activeImport.file_count} archivos procesados</p>
                      <p>{activeImport.relationships_count} relaciones inferidas</p>
                    </div>
                  )}
                </div>
              </div>

              {activeImport && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => handleDeleteImport(activeImport)}
                    disabled={deletingId === activeImport.id || activeImport.status === 'processing'}
                    className="inline-flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 transition hover:bg-red-100 disabled:opacity-50"
                  >
                    <Trash2 size={13} />
                    {activeImport.status === 'processing'
                      ? 'Import en procesamiento'
                      : deletingId === activeImport.id
                        ? 'Eliminando dataset...'
                        : 'Eliminar este dataset'}
                  </button>
                </div>
              )}

              {viewMode === 'context' ? (
                activeImport ? (
                  activeImport.status === 'processing' ? (
                    <div className="rounded-3xl border border-dashed border-[var(--border)] bg-white p-8 text-center text-[var(--text-secondary)]">
                      El dataset "{activeImport.name}" sigue en procesamiento. El schema aparecera aqui apenas termine.
                    </div>
                  ) : activeImport.status === 'failed' ? (
                    <div className="rounded-3xl border border-red-200 bg-red-50 p-8 text-center text-red-700">
                      Este import fallo durante el procesamiento.
                      {activeImport.error_message ? ` Detalle: ${activeImport.error_message}` : ''}
                    </div>
                  ) : (
                    <AnalyticsContextPanel context={datasetContext} />
                  )
                ) : (
                  <div className="rounded-3xl border border-dashed border-[var(--border)] bg-white p-8 text-center text-[var(--text-secondary)]">
                    Carga un dataset en Conectores para ver el contexto inferido de tablas y campos.
                  </div>
                )
              ) : (
                <>
                  {activeImport?.status === 'processing' ? (
                    <div className="rounded-3xl border border-dashed border-[var(--border)] bg-white p-8 text-center text-[var(--text-secondary)]">
                      El diagrama estara disponible cuando termine la inferencia de tablas y relaciones.
                    </div>
                  ) : activeImport?.status === 'failed' ? (
                    <div className="rounded-3xl border border-red-200 bg-red-50 p-8 text-center text-red-700">
                      No se pudo generar el schema de este import.
                      {activeImport?.error_message ? ` Detalle: ${activeImport.error_message}` : ''}
                    </div>
                  ) : (
                    <SchemaDiagram
                      tables={activeImport?.tables || []}
                      relationships={activeImport?.relationships || []}
                    />
                  )}

                  {activeImport && activeImport.status === 'ready' && (activeImport.relationships || []).length > 0 && (
                    <section className="rounded-3xl border border-[var(--border)] bg-white p-5 shadow-[0_20px_48px_rgba(15,23,42,0.06)]">
                      <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
                        Relaciones detectadas
                      </h3>
                      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                        {activeImport.relationships.map((relationship) => (
                          <div
                            key={relationship.id}
                            className="rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3"
                          >
                            <p className="text-sm font-medium text-[var(--text-primary)]">
                              {relationship.source_table_name}.{relationship.source_column_name}
                            </p>
                            <p className="mt-1 text-xs text-[var(--text-secondary)]">
                              apunta a {relationship.target_table_name}.{relationship.target_column_name}
                            </p>
                            <p className="mt-2 text-[11px] text-[#3258ff]">
                              confianza {Math.round((relationship.confidence || 0) * 100)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}
            </section>
          </div>
        </div>
      </main>
    </>
  )
}

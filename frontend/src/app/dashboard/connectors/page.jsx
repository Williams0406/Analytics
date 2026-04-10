'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { ArrowRight, FileUp, RefreshCw, Sparkles, Trash2 } from 'lucide-react'

import ConnectorCard from '@/components/connectors/ConnectorCard'
import Navbar from '@/components/layout/Navbar'
import apiClient from '@/lib/axios'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'

const EMPTY_FORM = {
  name: '',
  files: [],
}

export default function ConnectorsPage() {
  const fileInputRef = useRef(null)
  const [catalog, setCatalog] = useState([])
  const [imports, setImports] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchImportsOnly = async () => {
    const importsRes = await apiClient.get('/api/datasets/imports/')
    const nextImports = Array.isArray(importsRes.data) ? importsRes.data : importsRes.data.results || []
    setImports(nextImports)
    return nextImports
  }

  const fetchData = async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true)
    }

    try {
      const [catalogRes, myRes] = await Promise.all([
        apiClient.get('/api/connectors/catalog/'),
        apiClient.get('/api/connectors/'),
        fetchImportsOnly(),
      ])

      const myMap = {}
      const connectorsList = Array.isArray(myRes.data) ? myRes.data : myRes.data.results || []
      connectorsList.forEach((connector) => {
        myMap[connector.connector_type] = connector.id
      })

      const enriched = catalogRes.data.catalog
        .filter((connector) => connector.type !== 'csv_upload')
        .map((connector) => ({
          ...connector,
          connected: !!myMap[connector.type],
          id: myMap[connector.type] || null,
        }))

      setCatalog(enriched)
    } catch (err) {
      console.error(err)
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    const hasProcessingImports = imports.some((item) => item.status === 'processing')
    if (!hasProcessingImports) return undefined

    const pollId = window.setInterval(() => {
      fetchImportsOnly().catch(console.error)
    }, 4000)

    return () => window.clearInterval(pollId)
  }, [imports])

  const handleFileChange = (event) => {
    setForm((prev) => ({
      ...prev,
      files: Array.from(event.target.files || []),
    }))
  }

  const handleUpload = async (event) => {
    event.preventDefault()

    if (!form.files.length) {
      setError('Selecciona al menos un archivo CSV, TSV o Excel.')
      return
    }

    setUploading(true)
    setError('')

    try {
      const body = new FormData()
      if (form.name.trim()) {
        body.append('name', form.name.trim())
      }
      form.files.forEach((file) => body.append('files', file))

      await apiClient.post('/api/datasets/imports/', body, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 0,
      })

      setForm(EMPTY_FORM)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      await fetchImportsOnly()
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.files?.[0] ||
          'No se pudo procesar el dataset.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteImport = async (datasetImport) => {
    const confirmed = window.confirm(
      `Se eliminara "${datasetImport.name}" y su schema inferido. Esta accion no se puede deshacer.`
    )

    if (!confirmed) return

    setDeletingId(datasetImport.id)
    setError('')

    try {
      await apiClient.delete(`/api/datasets/imports/${datasetImport.id}/`)
      await fetchData()
    } catch (err) {
      setError(
        err.response?.data?.error ||
          'No se pudo eliminar el dataset seleccionado.'
      )
    } finally {
      setDeletingId(null)
    }
  }

  const connected = catalog.filter((connector) => connector.connected)
  const available = catalog.filter((connector) => !connector.connected)
  const latestReadyImport = imports.find((item) => item.status === 'ready') || null
  const latestProcessingImport = imports.find((item) => item.status === 'processing') || null

  return (
    <>
      <Navbar title="Conectores de Datos" />
      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Ingestion de Datos"
          icon={FileUp}
          title="Fuentes de Datos"
          description="Conecta herramientas o carga un solo dataset manualmente. Lumiq analizara el upload mas reciente en Analytics, AI Insights y Schema."
          actions={
            <>
              <button
                onClick={fetchData}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                <RefreshCw size={14} />
                Actualizar
              </button>
              <Link
                href="/dashboard/schema"
                className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
              >
                Ver Schema
              </Link>
            </>
          }
          meta={
            latestProcessingImport ? (
              <Card className="min-w-[300px] shadow-[var(--shadow-sm)]">
                <CardContent className="px-4 py-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                      Importacion en progreso
                    </p>
                    <Badge variant="warning">Procesando</Badge>
                  </div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{latestProcessingImport.name}</p>
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">
                    {latestProcessingImport.file_count} archivo(s) en analisis. Analytics seguira usando el ultimo dataset listo hasta terminar.
                  </p>
                </CardContent>
              </Card>
            ) : latestReadyImport ? (
              <Card className="min-w-[300px] shadow-[var(--shadow-sm)]">
                <CardContent className="px-4 py-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                      Dataset activo
                    </p>
                    <Badge variant="info">Listo</Badge>
                  </div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{latestReadyImport.name}</p>
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">
                    {latestReadyImport.file_count} archivo(s) | {latestReadyImport.tables_count} tabla(s) | {latestReadyImport.relationships_count} relacion(es)
                  </p>
                </CardContent>
              </Card>
            ) : null
          }
        />

        <section className="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-[400px_minmax(0,1fr)]">
          <Card className="shadow-[var(--shadow-md)]">
            <CardContent className="px-5 py-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white shadow-[var(--shadow-sm)]">
                  <FileUp size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Carga manual de datasets</h3>
                  <p className="text-xs text-[var(--text-secondary)]">
                    Soporta un solo archivo o bundles de varios archivos.
                  </p>
                </div>
              </div>

              <form onSubmit={handleUpload} className="space-y-4">
                <Input
                  type="text"
                  label="Nombre del dataset"
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  placeholder="Ej. Ventas de marzo o CRM Q2"
                />

                <label className="block">
                  <span className="mb-1.5 block text-sm font-medium text-[var(--text-primary)]">Archivos</span>
                  <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-lg)] border border-dashed border-[var(--border-strong)] bg-[var(--surface-muted)] px-4 py-5 text-center transition-all duration-[var(--motion-fast)] hover:border-[var(--accent-indigo)]">
                    <FileUp size={20} className="text-[var(--accent-indigo)]" />
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      Seleccionar CSV, TSV o Excel
                    </span>
                    <span className="text-xs text-[var(--text-secondary)]">
                      Si subes un solo dataset, Lumiq igual generara insights y graficas especificas.
                    </span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.tsv,.xlsx,.xls"
                      multiple
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </label>

                {form.files.length > 0 && (
                  <Card variant="muted">
                    <CardContent className="space-y-2 px-4 py-4">
                      <p className="text-xs font-semibold text-[var(--text-primary)]">Archivos seleccionados</p>
                      {form.files.map((file) => (
                        <div
                          key={`${file.name}-${file.size}`}
                          className="flex items-center justify-between gap-3 text-xs text-[var(--text-secondary)]"
                        >
                          <span className="truncate">{file.name}</span>
                          <span>{Math.max(1, Math.round(file.size / 1024))} KB</span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {error ? (
                  <div className="rounded-[var(--radius-md)] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                ) : null}

                <Button type="submit" loading={uploading} className="w-full">
                  {uploading ? 'Procesando dataset...' : 'Cargar dataset'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="min-w-0 space-y-6">
            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <Sparkles size={16} className="text-[var(--accent-indigo)]" />
                      <h3 className="text-sm font-semibold text-[var(--text-primary)]">Dataset activo</h3>
                    </div>
                    {latestReadyImport ? (
                      <>
                        <p className="text-lg font-semibold text-[var(--text-primary)]">{latestReadyImport.name}</p>
                        <p className="mt-1 text-sm text-[var(--text-secondary)]">
                          {latestReadyImport.file_count} archivo(s) | {latestReadyImport.tables_count} tabla(s) | {latestReadyImport.relationships_count} relacion(es)
                        </p>
                        <p className="mt-3 text-xs text-[var(--text-secondary)]">
                          Este dataset alimenta AI Insights y Analytics con la lectura mas reciente.
                        </p>
                        {latestProcessingImport ? (
                          <p className="mt-2 text-xs text-[var(--accent-indigo)]">
                            Hay una nueva importacion en proceso. Cuando termine, esta vista se actualizara sola.
                          </p>
                        ) : null}
                      </>
                    ) : (
                      <p className="max-w-2xl text-sm text-[var(--text-secondary)]">
                        {latestProcessingImport
                          ? 'Tu primer dataset se esta procesando ahora mismo. Cuando quede listo, aparecera aqui automaticamente.'
                          : 'Aun no hay datasets cargados. Puedes empezar con un solo CSV o Excel y Lumiq lo analizara como una fuente valida.'}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {latestReadyImport ? (
                      <Button
                        type="button"
                        variant="danger"
                        onClick={() => handleDeleteImport(latestReadyImport)}
                        loading={deletingId === latestReadyImport.id}
                      >
                        <Trash2 size={14} />
                        {deletingId === latestReadyImport.id ? 'Eliminando...' : 'Eliminar dataset'}
                      </Button>
                    ) : null}
                    <Link
                      href="/dashboard/schema"
                      className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
                    >
                      Ver schema
                      <ArrowRight size={14} />
                    </Link>
                    <Link
                      href="/dashboard/analytics"
                      className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
                    >
                      Ver analytics
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">Datasets recientes</h3>
                    <p className="text-xs text-[var(--text-secondary)]">Historial de uploads procesados desde Conectores.</p>
                  </div>
                  <Badge variant="neutral">{imports.length} import(s)</Badge>
                </div>

                <div className="space-y-3">
                  {loading ? (
                    Array(3).fill(0).map((_, index) => (
                      <Skeleton key={index} className="h-20 rounded-[var(--radius-md)]" />
                    ))
                  ) : imports.length === 0 ? (
                    <EmptyState
                      icon={FileUp}
                      title="Todavia no hay datasets"
                      description="Empieza subiendo un CSV o Excel para activar el analisis del workspace."
                    />
                  ) : (
                    imports.map((item) => (
                      <div key={item.id} className="rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 py-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-medium text-[var(--text-primary)]">{item.name}</p>
                            <p className="mt-1 text-xs text-[var(--text-secondary)]">
                              {new Date(item.created_at).toLocaleString('es-PE')}
                            </p>
                          </div>
                          <Badge variant="neutral">{item.status}</Badge>
                        </div>

                        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-[var(--text-secondary)]">
                          <span>{item.file_count} archivos</span>
                          <span>{item.tables_count} tablas</span>
                          <span>{item.relationships_count} relaciones</span>
                        </div>

                        <div className="mt-4 flex justify-end">
                          <Button
                            type="button"
                            variant="danger"
                            size="sm"
                            onClick={() => handleDeleteImport(item)}
                            loading={deletingId === item.id}
                            disabled={item.status === 'processing'}
                          >
                            <Trash2 size={13} />
                            {item.status === 'processing'
                              ? 'En procesamiento'
                              : deletingId === item.id
                                ? 'Eliminando...'
                                : 'Eliminar'}
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {connected.length > 0 && (
          <section className="mb-8">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
                Conectados
              </h3>
              <Badge variant="success">{connected.length}</Badge>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {connected.map((connector) => (
                <ConnectorCard
                  key={connector.type}
                  connector={connector}
                  onConnect={fetchData}
                  onSync={fetchData}
                />
              ))}
            </div>
          </section>
        )}

        <section>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
              Todos los conectores
            </h3>
            <Badge variant="neutral">{available.length}</Badge>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {Array(8).fill(0).map((_, index) => (
                <Skeleton key={index} className="h-40 rounded-[var(--radius-lg)]" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {available.map((connector) => (
                <ConnectorCard
                  key={connector.type}
                  connector={connector}
                  onConnect={fetchData}
                  onSync={fetchData}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  )
}

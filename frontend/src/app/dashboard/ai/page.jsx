'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Database, Send, Sparkles, Trash2 } from 'lucide-react'

import PresentationDeck from '@/components/analytics/PresentationDeck'
import { normalizePresentationSlides } from '@/components/analytics/presentationUtils'
import Navbar from '@/components/layout/Navbar'
import apiClient from '@/lib/axios'
import { getAccessToken } from '@/lib/auth'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import { TextArea } from '@/components/ui/Input'

const QUICK_QUESTIONS = [
  'Que tablas parecen ser el nucleo operativo del negocio?',
  'Que relaciones detectaste entre las tablas y como deberia interpretarlas?',
  'Donde ves riesgos de calidad o columnas incompletas?',
  'Que metricas o series temporales puedo explotar desde esta base?',
]

function resolveLatestInsight(payload) {
  const insights = Array.isArray(payload) ? payload : payload?.results || []
  return (
    insights.find((item) => normalizePresentationSlides(item?.presentation?.slides || []).length > 0)
    || insights[0]
    || null
  )
}

export default function AIInsightsPage() {
  const [currentInsight, setCurrentInsight] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [statusText, setStatusText] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(true)
  const [deletingCurrent, setDeletingCurrent] = useState(false)

  const fetchLatestInsight = async () => {
    try {
      const { data } = await apiClient.get('/api/insights/')
      setCurrentInsight(resolveLatestInsight(data))
    } catch (err) {
      console.error(err)
    }
  }

  const fetchInitialState = async () => {
    setLoading(true)

    const [dashboardResult, insightsResult] = await Promise.allSettled([
      apiClient.get('/api/analytics/dashboard/'),
      apiClient.get('/api/insights/'),
    ])

    if (dashboardResult.status === 'fulfilled') {
      setDashboard(dashboardResult.value.data)
    } else {
      console.error(dashboardResult.reason)
    }

    if (insightsResult.status === 'fulfilled') {
      setCurrentInsight(resolveLatestInsight(insightsResult.value.data))
    } else {
      console.error(insightsResult.reason)
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchInitialState()
  }, [])

  const activeSlides = currentInsight?.presentation?.slides || []
  const activeSlidesCount = normalizePresentationSlides(activeSlides).length

  const handleStream = async (customQuestion = null) => {
    const q = customQuestion || question
    if (!q?.trim()) return

    setStreaming(true)
    setStatusText('Interpretando tu pregunta...')

    try {
      const token = getAccessToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await fetch(`${apiUrl}/api/insights/stream/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: q || null }),
      })

      if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => '')
        throw new Error(errorText || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const eventChunk of events) {
          const dataLine = eventChunk
            .split('\n')
            .find((line) => line.startsWith('data: '))
          if (!dataLine) continue
          try {
            const parsed = JSON.parse(dataLine.replace('data: ', ''))
            if (parsed.status) {
              setStatusText(parsed.status)
            }
            if (parsed.error) {
              setStatusText(`AI Insights devolvio un error: ${parsed.error}`)
            }
            if (parsed.insight) {
              setCurrentInsight(parsed.insight)
              setStatusText(parsed.insight.content || 'Presentacion lista.')
            }
          } catch {}
        }
      }
    } catch (err) {
      setStatusText('No pude conectar con el motor de AI Insights. Revisa tu proveedor configurado.')
    } finally {
      setStreaming(false)
      setQuestion('')
    }
  }

  const handleDeleteCurrentInsight = async () => {
    if (!currentInsight?.id) return
    if (!window.confirm('Esta accion eliminara la presentacion activa de AI Insights.')) {
      return
    }

    setDeletingCurrent(true)
    try {
      await apiClient.delete(`/api/insights/${currentInsight.id}/`)
      setStatusText('')
      await fetchLatestInsight()
    } catch (error) {
      console.error(error)
    } finally {
      setDeletingCurrent(false)
    }
  }

  return (
    <>
      <Navbar title="AI Insights" />
      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Analisis Asistido"
          icon={Sparkles}
          title="AI Insights"
          description="Haz preguntas sobre el dataset cargado y recibe una lectura visual en slides, adaptada al nivel de detalle que necesites."
          actions={
            <>
              <Link
                href="/dashboard/ai/history"
                className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                Ver historial
              </Link>
            </>
          }
          meta={
            <Card className="min-w-[300px] shadow-[var(--shadow-sm)]">
              <CardContent className="px-4 py-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                    Dataset activo
                  </p>
                  <Badge variant={dashboard?.source === 'dataset' ? 'info' : 'neutral'}>
                    {dashboard?.source === 'dataset' ? 'Contexto real' : 'Pendiente'}
                  </Badge>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white shadow-[var(--shadow-sm)]">
                    <Database size={16} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                      {dashboard?.dataset_import?.name || 'Sin dataset activo'}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                      {dashboard?.source === 'dataset'
                        ? 'La IA esta razonando sobre tu upload mas reciente'
                        : 'Sube archivos en Conectores para responder sobre tu base'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          }
        />

        <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1.55fr)_380px]">
          <div className="space-y-4">
            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white">
                    <Sparkles size={14} />
                  </div>
                  <span className="text-sm font-semibold text-[var(--text-primary)]">Respuesta en diapositivas</span>
                  <div className="ml-auto flex items-center gap-2">
                    {activeSlidesCount ? (
                      <Badge variant="info">{activeSlidesCount} slides</Badge>
                    ) : null}
                    <Badge variant={streaming ? 'info' : 'neutral'}>
                      {streaming ? 'Actualizando...' : currentInsight ? 'Ultima respuesta' : 'Sin presentacion'}
                    </Badge>
                  </div>
                </div>

                {statusText ? (
                  <div className="mb-4 rounded-[var(--radius-md)] border border-[rgba(50,88,255,0.14)] bg-[rgba(50,88,255,0.05)] px-4 py-3 text-sm text-[var(--text-secondary)]">
                    {statusText}
                  </div>
                ) : null}

                {loading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-16 rounded-[var(--radius-lg)]" />
                    <Skeleton className="h-[420px] rounded-[var(--radius-lg)]" />
                  </div>
                ) : activeSlides.length ? (
                  <>
                    {currentInsight ? (
                      <div className="mb-4 flex flex-wrap items-start justify-between gap-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-4">
                        <div className="min-w-0">
                          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                            {new Date(currentInsight.created_at).toLocaleString('es-PE')}
                          </p>
                          <h2 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">
                            {currentInsight.title}
                          </h2>
                          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
                            {currentInsight.content}
                          </p>
                        </div>

                        <Button
                          variant="danger"
                          size="sm"
                          onClick={handleDeleteCurrentInsight}
                          disabled={deletingCurrent}
                          className="shrink-0"
                        >
                          <Trash2 size={14} />
                          {deletingCurrent ? 'Eliminando...' : 'Eliminar'}
                        </Button>
                      </div>
                    ) : null}

                    <PresentationDeck slides={activeSlides} />
                  </>
                ) : (
                  <EmptyState
                    icon={Sparkles}
                    title="Todavia no hay una presentacion activa"
                    description={
                      streaming
                        ? 'La IA esta preparando una respuesta visual para tu pregunta.'
                        : 'La ultima respuesta generada aparecera aqui automaticamente. Si aun no hiciste una consulta, usa el panel lateral para crear la primera.'
                    }
                  />
                )}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-4 xl:sticky xl:top-24">
            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center gap-2">
                  <Send size={15} className="text-[var(--accent-indigo)]" />
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Hazle una pregunta a Lumiq</h3>
                </div>

                <TextArea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter' && !streaming) {
                      handleStream()
                    }
                  }}
                  placeholder="Pregunta por tablas, campos, metricas, relaciones o incluso formulas..."
                  disabled={streaming}
                  rows={8}
                />

                <div className="mt-3 flex items-center justify-between gap-3">
                  <p className="text-[11px] text-[var(--text-muted)]">Usa Ctrl + Enter para enviar mas rapido.</p>
                  <Badge variant="neutral">Slides adaptativas</Badge>
                </div>

                <Button
                  onClick={() => handleStream()}
                  disabled={streaming || !question.trim()}
                  className="mt-4 w-full"
                >
                  <Send size={15} />
                  {streaming ? 'Construyendo presentacion...' : 'Generar respuesta'}
                </Button>
              </CardContent>
            </Card>

            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <p className="mb-3 text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                  Prompts sugeridos
                </p>
                <div className="space-y-2">
                  {QUICK_QUESTIONS.map((quickQuestion, index) => (
                    <button
                      key={quickQuestion}
                      onClick={() => handleStream(quickQuestion)}
                      disabled={streaming}
                      className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-left text-xs text-[var(--text-secondary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:text-[var(--text-primary)] disabled:opacity-40"
                      style={{ boxShadow: `inset 3px 0 0 ${['#3258ff', '#0ea5a4', '#f46d43', '#8b5cf6'][index % 4]}` }}
                    >
                      {quickQuestion}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {dashboard?.insights?.length ? (
              <Card className="shadow-[var(--shadow-md)]">
                <CardContent className="px-5 py-5">
                  <p className="mb-3 text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                    Pistas del dataset
                  </p>
                  <div className="space-y-3">
                    {dashboard.insights.slice(0, 4).map((insight, index) => (
                      <div
                        key={`${index}-${insight}`}
                        className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--text-secondary)]"
                        style={{ boxShadow: `inset 3px 0 0 ${['#3258ff', '#0ea5a4', '#f46d43', '#8b5cf6'][index % 4]}` }}
                      >
                        {insight}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : null}
          </aside>
        </div>
      </main>
    </>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { Database, RefreshCw, Send, Sparkles } from 'lucide-react'

import InsightCard from '@/components/insights/InsightCard'
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

export default function AIInsightsPage() {
  const [insights, setInsights] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [streamText, setStreamText] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchInsights = async () => {
    try {
      const { data } = await apiClient.get('/api/insights/')
      setInsights(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchDashboardContext = async () => {
    try {
      const { data } = await apiClient.get('/api/analytics/dashboard/')
      setDashboard(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchInsights()
    fetchDashboardContext()
  }, [])

  const handleStream = async (customQuestion = null) => {
    const q = customQuestion || question
    setStreaming(true)
    setStreamText('')

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

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const parsed = JSON.parse(line.replace('data: ', ''))
            if (parsed.token) {
              setStreamText((prev) => prev + parsed.token)
            }
            if (parsed.error) {
              setStreamText(`AI Insights devolvio un error: ${parsed.error}`)
            }
            if (parsed.done) {
              await fetchInsights()
            }
          } catch {}
        }
      }
    } catch (err) {
      setStreamText('No pude conectar con el motor de AI Insights. Revisa tu proveedor configurado.')
    } finally {
      setStreaming(false)
      setQuestion('')
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
          description="Haz preguntas sobre el dataset cargado en Conectores: columnas clave, calidad del dato, relaciones y metricas detectadas."
          actions={
            <button
              onClick={fetchInsights}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
            >
              <RefreshCw size={14} />
              Actualizar historial
            </button>
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
            <Card className="min-h-60 shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white">
                    <Sparkles size={14} />
                  </div>
                  <span className="text-sm font-semibold text-[var(--text-primary)]">Respuesta en vivo</span>
                  <div className="ml-auto">
                    <Badge variant={streaming ? 'info' : 'neutral'}>
                      {streaming ? 'Analizando...' : 'En espera'}
                    </Badge>
                  </div>
                </div>

                {streamText ? (
                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-secondary)]">
                    {streamText}
                    {streaming ? (
                      <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded bg-[var(--accent-indigo)]" />
                    ) : null}
                  </div>
                ) : (
                  <EmptyState
                    icon={Sparkles}
                    title="Todavia no hay una lectura activa"
                    description={
                      streaming
                        ? 'Generando una lectura del dataset en tiempo real.'
                        : 'Las respuestas apareceran aqui mientras el motor explora tu dataset.'
                    }
                  />
                )}
              </CardContent>
            </Card>

            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
                    Historial
                  </h3>
                  <Badge variant="neutral">{insights.length}</Badge>
                </div>

                <div className="max-h-[720px] space-y-3 overflow-y-auto pr-1">
                  {loading ? (
                    Array(3).fill(0).map((_, index) => (
                      <Skeleton key={index} className="h-36 rounded-[var(--radius-lg)]" />
                    ))
                  ) : insights.length === 0 ? (
                    <EmptyState
                      icon={Sparkles}
                      title="Aun no hay insights generados"
                      description="Haz tu primera pregunta para activar el historial de respuestas."
                    />
                  ) : (
                    insights.map((insight) => (
                      <InsightCard key={insight.id} insight={insight} />
                    ))
                  )}
                </div>
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
                  placeholder="Escribe aqui tu pregunta sobre tablas, campos, metricas, calidad o relaciones..."
                  disabled={streaming}
                  rows={8}
                />

                <div className="mt-3 flex items-center justify-between gap-3">
                  <p className="text-[11px] text-[var(--text-muted)]">Usa Ctrl + Enter para enviar mas rapido.</p>
                  <Badge variant="neutral">Prompt</Badge>
                </div>

                <Button
                  onClick={() => handleStream()}
                  disabled={streaming || !question.trim()}
                  className="mt-4 w-full"
                >
                  <Send size={15} />
                  {streaming ? 'Analizando...' : 'Enviar prompt'}
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
                        key={insight}
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

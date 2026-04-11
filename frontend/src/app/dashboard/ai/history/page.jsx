'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ArrowLeft, History, RefreshCw, Trash2 } from 'lucide-react'

import PresentationDeck from '@/components/analytics/PresentationDeck'
import { normalizePresentationSlides } from '@/components/analytics/presentationUtils'
import Navbar from '@/components/layout/Navbar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import apiClient from '@/lib/axios'

function hasSlides(insight) {
  return normalizePresentationSlides(insight?.presentation?.slides || []).length > 0
}

function HistoryItem({ insight, isActive, deleting, onSelect, onDelete }) {
  const slidesCount = normalizePresentationSlides(insight?.presentation?.slides || []).length

  return (
    <Card
      className={`transition-all duration-[var(--motion-fast)] ${
        isActive ? 'border-[var(--accent-indigo)] shadow-[var(--shadow-md)]' : 'hover:border-[var(--border-strong)]'
      }`}
    >
      <CardContent className="px-5 py-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
              {new Date(insight.created_at).toLocaleString('es-PE')}
            </p>
            <h3 className="mt-2 text-sm font-semibold leading-snug text-[var(--text-primary)]">
              {insight.title}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {slidesCount ? <Badge variant="info">{slidesCount} slides</Badge> : null}
            <Badge variant={insight.priority === 'high' ? 'danger' : insight.priority === 'low' ? 'neutral' : 'warning'}>
              {insight.priority_display}
            </Badge>
          </div>
        </div>

        <p className="mt-3 line-clamp-4 text-xs leading-relaxed text-[var(--text-secondary)]">
          {insight.content}
        </p>

        <div className="mt-4 flex flex-wrap gap-3">
          <Button variant={isActive ? 'primary' : 'secondary'} size="sm" onClick={onSelect}>
            Ver presentacion
          </Button>
          <Button variant="danger" size="sm" onClick={onDelete} disabled={deleting}>
            <Trash2 size={14} />
            {deleting ? 'Eliminando...' : 'Eliminar'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function AIInsightsHistoryPage() {
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeInsightId, setActiveInsightId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [clearing, setClearing] = useState(false)

  const fetchInsights = async (preferredId = null) => {
    try {
      const { data } = await apiClient.get('/api/insights/')
      const nextInsights = Array.isArray(data) ? data : data.results || []
      setInsights(nextInsights)
      setActiveInsightId((currentId) => {
        if (preferredId && nextInsights.some((item) => item.id === preferredId)) {
          return preferredId
        }
        if (currentId && nextInsights.some((item) => item.id === currentId)) {
          return currentId
        }
        const firstDeck = nextInsights.find(hasSlides)
        return firstDeck?.id || nextInsights[0]?.id || null
      })
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInsights()
  }, [])

  const activeInsight =
    insights.find((item) => item.id === activeInsightId)
    || insights.find(hasSlides)
    || insights[0]
    || null

  const activeSlides = activeInsight?.presentation?.slides || []
  const activeSlidesCount = normalizePresentationSlides(activeSlides).length

  const handleDelete = async (insightId) => {
    if (!window.confirm('Esta accion eliminara este insight del historial.')) {
      return
    }

    setDeletingId(insightId)
    try {
      await apiClient.delete(`/api/insights/${insightId}/`)
      await fetchInsights(activeInsightId === insightId ? null : activeInsightId)
    } catch (error) {
      console.error(error)
    } finally {
      setDeletingId(null)
    }
  }

  const handleClear = async () => {
    if (!insights.length || !window.confirm('Esto eliminara todo el historial de AI Insights.')) {
      return
    }

    setClearing(true)
    try {
      await apiClient.delete('/api/insights/clear/')
      setInsights([])
      setActiveInsightId(null)
    } catch (error) {
      console.error(error)
    } finally {
      setClearing(false)
    }
  }

  return (
    <>
      <Navbar title="Historial AI Insights" />
      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Registro de respuestas"
          icon={History}
          title="Historial de AI Insights"
          description="Revisa presentaciones anteriores, vuelve a abrirlas y elimina libremente las que ya no necesites."
          actions={
            <>
              <Link
                href="/dashboard/ai"
                className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                <ArrowLeft size={14} />
                Volver a AI Insights
              </Link>
              <button
                onClick={() => fetchInsights(activeInsightId)}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-4 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                <RefreshCw size={14} />
                Actualizar
              </button>
              <Button variant="danger" onClick={handleClear} disabled={!insights.length || clearing}>
                <Trash2 size={15} />
                {clearing ? 'Borrando historial...' : 'Borrar todo'}
              </Button>
            </>
          }
          meta={(
            <Card className="min-w-[240px] shadow-[var(--shadow-sm)]">
              <CardContent className="px-4 py-3">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                  Respuestas guardadas
                </p>
                <p className="mt-2 text-2xl font-semibold text-[var(--text-primary)]">
                  {insights.length}
                </p>
              </CardContent>
            </Card>
          )}
        />

        <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1.5fr)_430px]">
          <div className="space-y-4">
            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white">
                    <History size={14} />
                  </div>
                  <span className="text-sm font-semibold text-[var(--text-primary)]">Presentacion seleccionada</span>
                  <div className="ml-auto flex items-center gap-2">
                    {activeSlidesCount ? <Badge variant="info">{activeSlidesCount} slides</Badge> : null}
                    {activeInsight ? <Badge variant="neutral">{activeInsight.priority_display}</Badge> : null}
                  </div>
                </div>

                {loading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-16 rounded-[var(--radius-lg)]" />
                    <Skeleton className="h-[420px] rounded-[var(--radius-lg)]" />
                  </div>
                ) : activeInsight ? (
                  <>
                    <div className="mb-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                        {new Date(activeInsight.created_at).toLocaleString('es-PE')}
                      </p>
                      <h2 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">
                        {activeInsight.title}
                      </h2>
                      <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">
                        {activeInsight.content}
                      </p>
                    </div>

                    {activeSlidesCount ? (
                      <PresentationDeck slides={activeSlides} />
                    ) : (
                      <EmptyState
                        icon={History}
                        title="Este insight no tiene slides visibles"
                        description="Puedes conservarlo en el historial o eliminarlo si ya no te aporta contexto."
                      />
                    )}
                  </>
                ) : (
                  <EmptyState
                    icon={History}
                    title="No hay historial disponible"
                    description="Genera un nuevo insight en AI Insights para empezar a guardar respuestas."
                  />
                )}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-4 xl:sticky xl:top-24">
            <Card className="shadow-[var(--shadow-md)]">
              <CardContent className="px-5 py-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
                    Historial completo
                  </h3>
                  <Badge variant="neutral">{insights.length}</Badge>
                </div>

                <div className="max-h-[760px] space-y-3 overflow-y-auto pr-1">
                  {loading ? (
                    Array(4).fill(0).map((_, index) => (
                      <Skeleton key={index} className="h-44 rounded-[var(--radius-lg)]" />
                    ))
                  ) : insights.length === 0 ? (
                    <EmptyState
                      icon={History}
                      title="No hay respuestas guardadas"
                      description="Cuando generes respuestas en AI Insights, apareceran aqui para volver a abrirlas o borrarlas."
                    />
                  ) : (
                    insights.map((insight) => (
                      <HistoryItem
                        key={insight.id}
                        insight={insight}
                        isActive={insight.id === activeInsight?.id}
                        deleting={deletingId === insight.id}
                        onSelect={() => setActiveInsightId(insight.id)}
                        onDelete={() => handleDelete(insight.id)}
                      />
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </aside>
        </div>
      </main>
    </>
  )
}

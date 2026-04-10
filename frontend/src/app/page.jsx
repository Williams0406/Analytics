'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ArrowRight, BarChart3, Database, ShieldCheck, Sparkles } from 'lucide-react'

import apiClient from '@/lib/axios'
import Badge from '@/components/ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import StatusBadge from '@/components/ui/StatusBadge'

const featureCards = [
  {
    icon: Database,
    title: 'Conecta y comprende tu data',
    description: 'Carga datasets, detecta schema, relaciones y contexto analitico sin configuracion pesada.',
  },
  {
    icon: Sparkles,
    title: 'Insights guiados por IA',
    description: 'Convierte tablas y metricas en respuestas claras, accionables y enfocadas al negocio.',
  },
  {
    icon: BarChart3,
    title: 'Presentaciones ejecutivas',
    description: 'Genera slides, graficos y narrativa visual alineada a una experiencia tipo SaaS premium.',
  },
]

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState({ loading: true, data: null, error: null })

  useEffect(() => {
    const checkApi = async () => {
      try {
        const { data } = await apiClient.get('/api/health/')
        setApiStatus({ loading: false, data, error: null })
      } catch (err) {
        setApiStatus({
          loading: false,
          data: null,
          error: err.message || 'No se pudo conectar con la API',
        })
      }
    }

    checkApi()
  }, [])

  return (
    <main className="min-h-screen px-6 py-8 lg:px-10">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-[var(--container-max)] flex-col">
        <header className="flex items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-sm font-bold text-white shadow-[var(--shadow-sm)]">
              LQ
            </div>
            <div>
              <p className="text-lg font-semibold text-[var(--text-primary)]">Lumiq</p>
              <p className="text-xs uppercase tracking-[0.22em] text-[var(--text-muted)]">
                Decision Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] px-4 text-sm font-medium text-[var(--text-secondary)] transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)]"
            >
              Iniciar sesion
            </Link>
            <Link
              href="/register"
              className="inline-flex h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-4 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
            >
              Crear cuenta
            </Link>
          </div>
        </header>

        <section className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <Badge variant="info" className="mb-5">
              <ShieldCheck size={12} />
              Plataforma analitica lista para produccion
            </Badge>

            <h1 className="max-w-3xl text-5xl font-semibold leading-[0.98] text-[var(--text-primary)] lg:text-6xl">
              Convierte datasets en decisiones claras, visuales y accionables.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--text-secondary)]">
              Lumiq combina ingestion de datos, comprension de schema, analytics visual y AI
              insights en una sola experiencia moderna para equipos de negocio.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/register"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--surface-dark)] px-5 text-sm font-medium text-white transition-all duration-[var(--motion-fast)] hover:bg-[var(--surface-dark-soft)]"
              >
                Empezar ahora
                <ArrowRight size={16} />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex h-12 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-5 text-sm font-medium text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]"
              >
                Ir al workspace
              </Link>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {featureCards.map((feature) => {
                const Icon = feature.icon
                return (
                  <Card key={feature.title} className="shadow-[var(--shadow-sm)]">
                    <CardContent className="px-5 py-5">
                      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-white">
                        <Icon size={18} />
                      </div>
                      <h3 className="text-sm font-semibold text-[var(--text-primary)]">{feature.title}</h3>
                      <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>

          <div className="space-y-5">
            <Card variant="elevated">
              <CardHeader>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <CardTitle>Estado del sistema</CardTitle>
                    <CardDescription>Verificacion rapida de la conexion con la API</CardDescription>
                  </div>
                  <StatusBadge loading={apiStatus.loading} error={apiStatus.error} />
                </div>
              </CardHeader>
              <CardContent className="pt-2">
                {apiStatus.loading ? (
                  <p className="text-sm text-[var(--text-secondary)]">Conectando con la API...</p>
                ) : apiStatus.error ? (
                  <div className="rounded-[var(--radius-md)] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {apiStatus.error}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(apiStatus.data || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-4">
                        <span className="text-sm capitalize text-[var(--text-secondary)]">{key}</span>
                        <span className="font-mono text-xs font-medium text-[var(--text-primary)]">
                          {String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="overflow-hidden">
              <CardHeader>
                <CardTitle>Que resuelve Lumiq</CardTitle>
                <CardDescription>
                  Un flujo continuo desde la carga hasta la lectura ejecutiva.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-1">
                {[
                  'Carga tus datasets desde Conectores.',
                  'Schema interpreta tablas, campos y relaciones.',
                  'Analytics construye una narrativa visual.',
                  'AI Insights responde preguntas sobre la data real.',
                ].map((item, index) => (
                  <div
                    key={item}
                    className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--text-secondary)]"
                    style={{ boxShadow: `inset 3px 0 0 ${['#3258ff', '#0ea5a4', '#f46d43', '#8b5cf6'][index % 4]}` }}
                  >
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  )
}

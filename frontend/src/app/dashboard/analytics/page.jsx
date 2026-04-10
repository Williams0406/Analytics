'use client'

import { useEffect, useState } from 'react'
import { GalleryVerticalEnd } from 'lucide-react'

import apiClient from '@/lib/axios'
import Navbar from '@/components/layout/Navbar'
import PresentationDeck from '@/components/analytics/PresentationDeck'
import { Card, CardContent } from '@/components/ui/Card'
import PageHeader from '@/components/ui/PageHeader'

export default function AnalyticsPage() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/api/analytics/presentation/')
      .then(({ data }) => setPayload(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <Navbar title="Analytics" />

      <main className="flex-1 overflow-auto p-6">
        <PageHeader
          eyebrow="Modo Presentacion"
          icon={GalleryVerticalEnd}
          title="Analytics Presentation"
          description="Una lectura visual tipo slides de la informacion mas relevante detectada en tu dataset."
          meta={
            payload?.dataset_import ? (
              <Card className="min-w-[260px] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)]">
                <CardContent className="px-4 py-3">
                  <p className="mb-1 text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">
                    Presentacion activa
                  </p>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">
                    {payload.dataset_import.name}
                  </p>
                </CardContent>
              </Card>
            ) : null
          }
        />

        {loading ? (
          <div className="h-[520px] animate-pulse rounded-[32px] border border-[var(--border)] bg-white" />
        ) : (
          <PresentationDeck slides={payload?.slides || []} />
        )}
      </main>
    </>
  )
}

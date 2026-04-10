'use client'

import { useState } from 'react'

import apiClient from '@/lib/axios'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'

export default function ConnectorCard({ connector, onConnect, onSync }) {
  const [loading, setLoading] = useState(false)

  const handleConnect = async () => {
    setLoading(true)
    try {
      await apiClient.post('/api/connectors/', {
        connector_type: connector.type,
        name: connector.name,
        config: {},
      })
      onConnect?.()
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async (id) => {
    setLoading(true)
    try {
      await apiClient.post(`/api/connectors/${id}/sync/`)
      onSync?.()
    } finally {
      setLoading(false)
    }
  }

  const statusBadge = connector.connected
    ? <Badge variant="success">Conectado</Badge>
    : connector.available
    ? <Badge variant="neutral">Disponible</Badge>
    : <Badge variant="warning">Proximamente</Badge>

  return (
    <Card
      className={`transition-all duration-[var(--motion-fast)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)] ${
        connector.connected
          ? 'border-emerald-200'
          : connector.available
          ? 'hover:border-[var(--border-strong)]'
          : 'opacity-70'
      }`}
    >
      <CardContent className="px-5 py-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{connector.icon}</span>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">{connector.name}</h3>
              <span className="text-xs text-[var(--text-muted)]">{connector.category}</span>
            </div>
          </div>
          {statusBadge}
        </div>

        <p className="mb-5 text-xs leading-relaxed text-[var(--text-secondary)]">{connector.description}</p>

        {connector.connected ? (
          <Button
            onClick={() => handleSync(connector.id)}
            loading={loading}
            variant="primary"
            className="w-full"
          >
            {loading ? 'Sincronizando...' : 'Sincronizar ahora'}
          </Button>
        ) : connector.available ? (
          <Button
            onClick={handleConnect}
            loading={loading}
            variant="accent"
            className="w-full"
          >
            {loading ? 'Conectando...' : 'Conectar'}
          </Button>
        ) : (
          <Button disabled variant="subtle" className="w-full">
            Proximamente
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

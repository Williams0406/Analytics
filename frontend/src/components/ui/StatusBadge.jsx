'use client'

import Badge from '@/components/ui/Badge'

export default function StatusBadge({ loading, error }) {
  if (loading) {
    return (
      <Badge variant="warning">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#d4a72c]" />
        Verificando
      </Badge>
    )
  }

  if (error) {
    return (
      <Badge variant="danger">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Desconectado
      </Badge>
    )
  }

  return (
    <Badge variant="success">
      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-sage)]" />
      Conectado
    </Badge>
  )
}

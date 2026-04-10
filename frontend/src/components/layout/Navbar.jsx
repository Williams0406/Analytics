'use client'

import { useEffect, useMemo, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Bell, ChevronRight, Command, Search, Sparkles } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import { getStoredUser } from '@/lib/auth'

const SECTION_LABELS = {
  dashboard: 'Dashboard',
  analytics: 'Analytics',
  connectors: 'Conectores',
  schema: 'Schema',
  ai: 'AI Insights',
  settings: 'Ajustes',
}

export default function Navbar({ title = 'Dashboard' }) {
  const pathname = usePathname()
  const [user, setUser] = useState(null)

  useEffect(() => {
    setUser(getStoredUser())
  }, [])

  const initials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
    : '?'

  const currentSection = useMemo(() => {
    if (pathname === '/dashboard') return 'Dashboard'
    const segments = pathname.split('/').filter(Boolean)
    const tail = segments[segments.length - 1]
    return SECTION_LABELS[tail] || title
  }, [pathname, title])

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[rgba(255,255,255,0.82)] backdrop-blur-xl">
      <div className="flex min-h-[76px] items-center justify-between gap-4 px-6">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">
            <span>Workspace</span>
            <ChevronRight size={12} />
            <span>{currentSection}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="truncate text-base font-semibold text-[var(--text-primary)]">{title}</h1>
            <Badge variant="neutral" className="hidden md:inline-flex">
              <Sparkles size={11} />
              Vista activa
            </Badge>
          </div>
        </div>

        <button
          type="button"
          className="hidden min-w-[320px] items-center gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3 text-left text-sm text-[var(--text-secondary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:bg-white xl:inline-flex"
        >
          <Search size={15} />
          <span className="flex-1">Buscar vistas, datasets o acciones...</span>
          <span className="inline-flex items-center gap-1 rounded-full border border-[var(--border)] bg-white px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
            <Command size={10} />
            K
          </span>
        </button>

        <div className="flex items-center gap-3">
          {user?.company ? (
            <Badge variant="info" className="hidden lg:inline-flex">
              {user.company}
            </Badge>
          ) : null}

          <button className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--border)] bg-white text-[var(--text-secondary)] transition-all duration-[var(--motion-fast)] hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]">
            <Bell size={15} />
          </button>

          <div className="flex items-center gap-2.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-2.5 py-2 shadow-[var(--shadow-sm)]">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-xs font-bold text-white shadow-[0_14px_30px_rgba(15,23,42,0.16)]">
              {initials}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-semibold leading-none text-[var(--text-primary)]">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="mt-0.5 text-xs text-[var(--text-secondary)]">{user?.company || 'Lumiq'}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

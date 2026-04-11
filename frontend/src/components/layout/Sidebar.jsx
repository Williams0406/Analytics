'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  BarChart3,
  Plug,
  Database,
  Sparkles,
  Settings,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'

import { logout } from '@/lib/auth'

const navItems = [
  { href: '/dashboard', label: 'Inicio', icon: LayoutDashboard },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/connectors', label: 'Conectores', icon: Plug },
  { href: '/dashboard/schema', label: 'Schema', icon: Database },
  { href: '/dashboard/ai', label: 'AI Insights', icon: Sparkles },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const storedValue = window.localStorage.getItem('lumiq.sidebar.collapsed')
    if (storedValue === '1') {
      setCollapsed(true)
    }
  }, [])

  const toggleCollapsed = () => {
    setCollapsed((previous) => {
      const next = !previous
      window.localStorage.setItem('lumiq.sidebar.collapsed', next ? '1' : '0')
      return next
    })
  }

  const handleLogout = async () => {
    await logout()
    router.replace('/login')
  }

  return (
    <aside
      className={`sticky top-0 h-screen min-h-screen bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] border-r border-[rgba(255,255,255,0.08)] flex flex-col transition-[width] duration-300 ${
        collapsed ? 'w-24' : 'w-72'
      }`}
    >
      <div className="px-4 py-4 border-b border-[rgba(255,255,255,0.08)]">
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} gap-3`}>
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl bg-white text-[var(--surface-dark)] flex items-center justify-center font-bold text-sm shadow-[0_16px_34px_rgba(255,255,255,0.12)]">
              LQ
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <span className="font-semibold text-white text-lg block leading-none">Lumiq</span>
                <p className="text-[11px] uppercase tracking-[0.26em] text-slate-400 mt-1">Decision Intelligence</p>
              </div>
            )}
          </div>

          {!collapsed && (
            <button
              type="button"
              onClick={toggleCollapsed}
              className="w-10 h-10 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] text-slate-300 hover:text-white hover:bg-[rgba(255,255,255,0.08)] transition"
              aria-label="Contraer sidebar"
            >
              <PanelLeftClose size={16} className="mx-auto" />
            </button>
          )}
        </div>

        {collapsed && (
          <button
            type="button"
            onClick={toggleCollapsed}
            className="mt-4 w-full h-10 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] text-slate-300 hover:text-white hover:bg-[rgba(255,255,255,0.08)] transition"
            aria-label="Expandir sidebar"
          >
            <PanelLeftOpen size={16} className="mx-auto" />
          </button>
        )}
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1.5">
        {navItems.map(({ href, label, icon: Icon, soon }) => {
          const isActive = pathname === href
          return (
            <div key={href} className="relative">
              <Link
                href={soon ? '#' : href}
                title={collapsed ? label : undefined}
                className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'} px-3 py-3 rounded-2xl text-sm transition-all ${
                  isActive
                    ? 'bg-white text-[var(--surface-dark)] font-semibold shadow-[0_18px_38px_rgba(255,255,255,0.12)]'
                    : soon
                    ? 'text-slate-600 cursor-not-allowed'
                    : 'text-slate-300 hover:text-white hover:bg-[rgba(255,255,255,0.06)]'
                }`}
              >
                <Icon size={16} />
                {!collapsed && <span>{label}</span>}
                {!collapsed && soon && (
                  <span className="ml-auto text-[11px] bg-[rgba(255,255,255,0.06)] text-slate-400 px-2 py-0.5 rounded-full">
                    Pronto
                  </span>
                )}
              </Link>
            </div>
          )
        })}
      </nav>

      <div className="px-3 py-4 border-t border-[rgba(255,255,255,0.08)]">
        <button
          onClick={handleLogout}
          title={collapsed ? 'Cerrar sesion' : undefined}
          className={`w-full flex items-center ${collapsed ? 'justify-center' : 'gap-3'} px-3 py-3 rounded-2xl text-sm text-slate-400 hover:text-red-200 hover:bg-[rgba(244,109,67,0.12)] transition`}
        >
          <LogOut size={16} />
          {!collapsed && <span>Cerrar sesion</span>}
        </button>
      </div>
    </aside>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import Sidebar from '@/components/layout/Sidebar'

export default function DashboardLayout({ children }) {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login')
    } else {
      setChecking(false)
    }
  }, [router])

  if (checking) {
    return (
      <div className="min-h-screen bg-[var(--app-bg)] flex items-center justify-center">
        <div className="rounded-2xl border border-[var(--border)] bg-white px-5 py-4 text-[var(--text-secondary)] text-sm shadow-[0_22px_60px_rgba(15,23,42,0.08)] animate-pulse">
          Verificando sesion...
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-[var(--app-bg)] text-[var(--text-primary)]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {children}
      </div>
    </div>
  )
}

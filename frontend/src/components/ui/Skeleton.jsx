'use client'

import { cn } from '@/lib/cn'

export default function Skeleton({ className = '' }) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-[var(--radius-md)] bg-[var(--surface-subtle)]',
        className
      )}
    >
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.6s_infinite] bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.7)_50%,transparent_100%)]" />
    </div>
  )
}

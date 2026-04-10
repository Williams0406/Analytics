'use client'

import { cn } from '@/lib/cn'

const VARIANTS = {
  neutral: 'border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)]',
  info: 'border border-[#d7dcff] bg-[var(--info-bg)] text-[var(--accent-indigo)]',
  success: 'border border-[#dcebe6] bg-[var(--success-bg)] text-[var(--accent-sage)]',
  warning: 'border border-[#f0e0b2] bg-[var(--warning-bg)] text-[#9a6700]',
  danger: 'border border-red-200 bg-[var(--danger-bg)] text-red-700',
  dark: 'border border-[rgba(255,255,255,0.08)] bg-[var(--surface-dark)] text-white',
}

export default function Badge({ className = '', variant = 'neutral', children, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        VARIANTS[variant] || VARIANTS.neutral,
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}

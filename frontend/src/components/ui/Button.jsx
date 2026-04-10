'use client'

import { cn } from '@/lib/cn'

const VARIANTS = {
  primary: 'bg-[var(--surface-dark)] text-white hover:bg-[var(--surface-dark-soft)]',
  secondary: 'border border-[var(--border)] bg-white text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-subtle)]',
  subtle: 'bg-[var(--surface-muted)] text-[var(--text-primary)] hover:bg-[var(--surface-subtle)]',
  ghost: 'text-[var(--text-secondary)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)]',
  danger: 'border border-red-200 bg-red-50 text-red-700 hover:bg-red-100',
  accent: 'bg-[var(--accent-indigo)] text-white hover:opacity-95',
}

const SIZES = {
  sm: 'h-9 rounded-[var(--radius-sm)] px-3 text-xs',
  md: 'h-11 rounded-[var(--radius-md)] px-4 text-sm',
  lg: 'h-12 rounded-[var(--radius-md)] px-5 text-sm',
  icon: 'h-10 w-10 rounded-[var(--radius-md)]',
}

export default function Button({
  className = '',
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  children,
  ...props
}) {
  const isDisabled = disabled || loading

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-all duration-[var(--motion-fast)] disabled:cursor-not-allowed disabled:opacity-50',
        VARIANTS[variant] || VARIANTS.primary,
        SIZES[size] || SIZES.md,
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {children}
    </button>
  )
}

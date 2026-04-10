'use client'

import { cn } from '@/lib/cn'

const VARIANTS = {
  default: 'border border-[var(--border)] bg-white shadow-[var(--shadow-md)]',
  muted: 'border border-[var(--border)] bg-[var(--surface-muted)]',
  elevated: 'border border-[var(--border)] bg-white shadow-[var(--shadow-lg)]',
  dark: 'border border-[rgba(255,255,255,0.08)] bg-[linear-gradient(180deg,#16202b_0%,#111a22_100%)] text-white shadow-[var(--shadow-lg)]',
}

export function Card({ className = '', variant = 'default', children, ...props }) {
  return (
    <section
      className={cn(
        'rounded-[var(--radius-xl)]',
        VARIANTS[variant] || VARIANTS.default,
        className
      )}
      {...props}
    >
      {children}
    </section>
  )
}

export function CardHeader({ className = '', children, ...props }) {
  return (
    <div className={cn('px-6 pt-6', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className = '', children, ...props }) {
  return (
    <h3 className={cn('text-base font-semibold text-[var(--text-primary)]', className)} {...props}>
      {children}
    </h3>
  )
}

export function CardDescription({ className = '', children, ...props }) {
  return (
    <p className={cn('mt-1 text-sm text-[var(--text-secondary)]', className)} {...props}>
      {children}
    </p>
  )
}

export function CardContent({ className = '', children, ...props }) {
  return (
    <div className={cn('px-6 py-5', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ className = '', children, ...props }) {
  return (
    <div className={cn('px-6 pb-6', className)} {...props}>
      {children}
    </div>
  )
}

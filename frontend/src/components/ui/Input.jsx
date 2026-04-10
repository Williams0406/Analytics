'use client'

import { cn } from '@/lib/cn'

function FieldShell({ label, hint, error, children }) {
  return (
    <label className="block">
      {label ? <span className="mb-1.5 block text-sm font-medium text-[var(--text-primary)]">{label}</span> : null}
      {children}
      {error ? (
        <span className="mt-1.5 block text-xs text-red-600">{error}</span>
      ) : hint ? (
        <span className="mt-1.5 block text-xs text-[var(--text-muted)]">{hint}</span>
      ) : null}
    </label>
  )
}

const baseClassName =
  'w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-white px-3.5 py-3 text-sm text-[var(--text-primary)] transition-all duration-[var(--motion-fast)] placeholder:text-[var(--text-muted)] focus:border-[var(--border-strong)]'

export function Input({ label, hint, error, className = '', ...props }) {
  return (
    <FieldShell label={label} hint={hint} error={error}>
      <input
        className={cn(
          baseClassName,
          error ? 'border-red-300 bg-red-50/40' : 'hover:border-[var(--border-strong)]',
          className
        )}
        {...props}
      />
    </FieldShell>
  )
}

export function TextArea({ label, hint, error, className = '', ...props }) {
  return (
    <FieldShell label={label} hint={hint} error={error}>
      <textarea
        className={cn(
          `${baseClassName} min-h-[132px] resize-none`,
          error ? 'border-red-300 bg-red-50/40' : 'hover:border-[var(--border-strong)]',
          className
        )}
        {...props}
      />
    </FieldShell>
  )
}

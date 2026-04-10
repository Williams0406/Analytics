'use client'

import { cn } from '@/lib/cn'

export default function SegmentedControl({
  options = [],
  value,
  onChange,
  className = '',
}) {
  return (
    <div className={cn('inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-white p-1', className)}>
      {options.map((option) => {
        const isActive = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange?.(option.value)}
            className={cn(
              'rounded-[12px] px-3 py-2 text-xs font-medium transition-all duration-[var(--motion-fast)]',
              isActive
                ? 'bg-[var(--surface-dark)] text-white'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

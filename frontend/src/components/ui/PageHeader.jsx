'use client'

import { cn } from '@/lib/cn'

export default function PageHeader({
  eyebrow,
  title,
  description,
  icon: Icon,
  actions = null,
  meta = null,
  className = '',
}) {
  return (
    <section className={cn('mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between', className)}>
      <div>
        {eyebrow ? (
          <p className="mb-2 text-[11px] uppercase tracking-[0.28em] text-[var(--text-muted)]">{eyebrow}</p>
        ) : null}
        <div className="flex items-center gap-2">
          {Icon ? <Icon size={18} className="text-[var(--accent-indigo)]" /> : null}
          <h1 className="text-2xl font-semibold text-[var(--text-primary)]">{title}</h1>
        </div>
        {description ? (
          <p className="mt-2 max-w-2xl text-sm text-[var(--text-secondary)]">{description}</p>
        ) : null}
      </div>

      <div className="flex flex-col items-stretch gap-3 sm:items-end">
        {meta}
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </section>
  )
}

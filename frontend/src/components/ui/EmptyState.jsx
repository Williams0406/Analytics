'use client'

import { Card, CardContent } from '@/components/ui/Card'
import { cn } from '@/lib/cn'

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action = null,
  className = '',
}) {
  return (
    <Card className={cn('border-dashed shadow-none', className)}>
      <CardContent className="flex flex-col items-center px-8 py-10 text-center">
        {Icon ? (
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--surface-muted)] text-[var(--text-muted)]">
            <Icon size={20} />
          </div>
        ) : null}
        <h3 className="text-base font-semibold text-[var(--text-primary)]">{title}</h3>
        {description ? (
          <p className="mt-2 max-w-lg text-sm leading-relaxed text-[var(--text-secondary)]">
            {description}
          </p>
        ) : null}
        {action ? <div className="mt-5">{action}</div> : null}
      </CardContent>
    </Card>
  )
}

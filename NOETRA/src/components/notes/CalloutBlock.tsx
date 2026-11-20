import { useMemo } from 'react'
import { Info, Lightbulb, TriangleAlert, Zap } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { InlineMarkdown } from './InlineMarkdown'
import { metaExtras } from '@/lib/notes/blocks'
import { cn } from '@/lib/utils'
import type { NoteCalloutTone } from '@/types/notes'

/**
 * Callout block.
 *
 * Tones reuse the existing NOETRA palette rather than introducing status
 * colours: weight and the accent tint carry the emphasis, so the block still
 * reads correctly at reduced contrast.
 */
const TONE_META: Record<
  NoteCalloutTone,
  { icon: LucideIcon; label: string; frame: string; iconClass: string }
> = {
  info: {
    icon: Info,
    label: 'Note',
    frame: 'border-border bg-muted/40',
    iconClass: 'text-muted-foreground',
  },
  tip: {
    icon: Lightbulb,
    label: 'Tip',
    frame: 'border-accent/25 bg-accent/[0.06]',
    iconClass: 'text-accent',
  },
  warning: {
    icon: TriangleAlert,
    label: 'Caution',
    frame: 'border-accent/40 bg-accent/[0.09]',
    iconClass: 'text-accent',
  },
  important: {
    icon: Zap,
    label: 'Important',
    frame: 'border-accent/50 bg-accent/[0.11]',
    iconClass: 'text-accent',
  },
}

export interface CalloutBlockProps {
  tone: NoteCalloutTone
  title?: string
  content: string
  meta?: Record<string, unknown>
  className?: string
}

export function CalloutBlock({ tone, title, content, meta, className }: CalloutBlockProps) {
  const { icon: Icon, label, frame, iconClass } = TONE_META[tone]
  const extras = useMemo(() => metaExtras(meta), [meta])

  return (
    <aside
      className={cn('my-4 flex gap-3 rounded-xl border px-4 py-3.5', frame, className)}
      aria-label={title ?? label}
    >
      <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', iconClass)} aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          {title ?? label}
        </p>
        <p className="mt-1 text-sm leading-relaxed text-foreground/90">
          <InlineMarkdown text={content} />
        </p>
        {extras.length > 0 && (
          <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 border-t border-border/60 pt-2">
            {extras.map((entry) => (
              <div key={entry.key} className="flex items-baseline gap-1.5">
                <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {entry.key}
                </dt>
                <dd className="text-[11px] text-foreground/75">{entry.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </aside>
  )
}

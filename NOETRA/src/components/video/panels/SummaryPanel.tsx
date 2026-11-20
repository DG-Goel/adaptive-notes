import { useState } from 'react'
import { FileQuestion, Lightbulb, ListChecks, RefreshCw, Sparkles, TextQuote } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { SectionHeader } from '@/components/common/SectionHeader'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { TimestampText } from '@/components/video/TimestampText'
import { cn } from '@/lib/utils'
import { useSummary } from '@/hooks/use-lecture-queries'
import type { SummaryDetail } from '@/types/notes'

const DETAIL_OPTIONS: { value: SummaryDetail; label: string; hint: string }[] = [
  { value: 'concise', label: 'Concise', hint: 'A couple of sentences' },
  { value: 'balanced', label: 'Balanced', hint: 'A short paragraph' },
  { value: 'detailed', label: 'Detailed', hint: 'A full walkthrough' },
]

export interface SummaryPanelProps {
  videoId: string
  className?: string
}

export function SummaryPanel({ videoId, className }: SummaryPanelProps) {
  const { data, isPending, isError, error, refetch } = useSummary(videoId)
  const [detail, setDetail] = useState<SummaryDetail>('balanced')

  if (isPending) {
    return (
      <div className={cn('rounded-2xl border border-border bg-card p-5', className)}>
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <EmptyState
        className={className}
        icon={<FileQuestion className="h-5 w-5" />}
        title="Summary unavailable"
        description={error instanceof Error ? error.message : 'The summary could not be loaded.'}
        action={
          <SecondaryButton size="sm" onClick={() => void refetch()}>
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </SecondaryButton>
        }
      />
    )
  }

  return (
    <div className={cn('space-y-5', className)}>
      <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" />
            <h2 className="font-serif text-lg font-medium tracking-tight text-foreground">
              Summary
            </h2>
            <Badge variant="outline" className="text-[10px]">
              Demo content
            </Badge>
          </div>

          <div
            role="tablist"
            aria-label="Summary detail level"
            className="inline-flex rounded-full border border-border bg-muted/40 p-0.5"
          >
            {DETAIL_OPTIONS.map((option) => {
              const active = detail === option.value
              return (
                <button
                  key={option.value}
                  type="button"
                  role="tab"
                  title={option.hint}
                  aria-selected={active}
                  onClick={() => setDetail(option.value)}
                  className={cn(
                    'rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
                    active
                      ? 'bg-accent text-accent-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {option.label}
                </button>
              )
            })}
          </div>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-foreground/85">
          <TimestampText text={data.variants[detail]} />
        </p>
      </section>

      <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <SectionHeader title="Executive summary" />
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{data.executive}</p>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-center gap-2">
            <ListChecks className="h-4 w-4 text-accent" />
            <h3 className="font-serif text-base font-medium text-foreground">Key takeaways</h3>
          </div>
          <ul className="mt-3 space-y-2.5">
            {data.takeaways.map((takeaway) => (
              <li key={takeaway} className="flex items-start gap-2.5">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent/60" />
                <span className="text-sm leading-relaxed text-foreground/85">{takeaway}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-accent" />
            <h3 className="font-serif text-base font-medium text-foreground">Key concepts</h3>
          </div>
          <dl className="mt-3 space-y-3">
            {data.concepts.map((concept) => (
              <div key={concept.term}>
                <dt className="text-sm font-medium text-foreground">{concept.term}</dt>
                <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">
                  {concept.definition}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      </div>

      <section className="rounded-2xl border border-accent/25 bg-accent/[0.05] p-5">
        <div className="flex items-center gap-2">
          <TextQuote className="h-4 w-4 text-accent" />
          <h3 className="font-serif text-base font-medium text-foreground">One-line recap</h3>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-foreground/85">{data.recap}</p>
      </section>
    </div>
  )
}

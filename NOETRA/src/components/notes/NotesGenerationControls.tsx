import { useState } from 'react'
import {
  Check,
  CircleDashed,
  Loader2,
  Sparkles,
  TriangleAlert,
  Wand2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { useStartNotesEnhancement, useStartNotesGeneration } from '@/hooks/use-lecture-queries'
import { cn } from '@/lib/utils'
import type {
  NoteDocument,
  NotesDetailLevel,
  NotesEnhancement,
  NotesProcessingStage,
  NotesProcessingStatus,
} from '@/types/notes'

/**
 * Notes generation and visual enhancement controls.
 *
 * The pipeline itself lives on the backend, so this surface only ever reports
 * what the API returned. Stages are listed in full, the current one is marked,
 * and a progress bar appears only when the service actually supplied a
 * fraction — no percentage is ever estimated on the client, and a run never
 * reports success unless the service did.
 */

const DETAIL_LEVELS: { value: NotesDetailLevel; label: string; hint: string }[] = [
  { value: 'concise', label: 'Concise', hint: 'Short sections, key points only' },
  { value: 'balanced', label: 'Balanced', hint: 'Adaptive depth with explanations' },
  { value: 'detailed', label: 'Detailed', hint: 'Full derivations and edge cases' },
]

const ENHANCEMENTS: { value: NotesEnhancement; label: string }[] = [
  { value: 'examples', label: 'Worked examples' },
  { value: 'equations', label: 'Equations' },
  { value: 'tables', label: 'Comparison tables' },
  { value: 'flowcharts', label: 'Flowcharts' },
  { value: 'diagrams', label: 'Diagrams' },
  { value: 'timestamps', label: 'Timestamp references' },
]

const STAGE_LABELS: Record<NotesProcessingStage, string> = {
  queued: 'Queued',
  extracting: 'Extracting transcript',
  generating: 'Generating notes',
  'identifying-visuals': 'Identifying visual opportunities',
  'rendering-visuals': 'Rendering visuals',
  completed: 'Completed',
  failed: 'Failed',
}

const STAGE_ORDER: NotesProcessingStage[] = [
  'queued',
  'extracting',
  'generating',
  'identifying-visuals',
  'rendering-visuals',
  'completed',
]

export interface NotesGenerationStatusProps {
  status?: NotesProcessingStatus
  isPending?: boolean
  isError?: boolean
  error?: unknown
  className?: string
}

/** Compact status read-out, shared by the generation dialog and the context panel. */
export function NotesGenerationStatus({
  status,
  isPending,
  isError,
  error,
  className,
}: NotesGenerationStatusProps) {
  if (isError) {
    return (
      <p className={cn('flex items-start gap-2 text-xs text-destructive', className)}>
        <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
        {error instanceof Error ? error.message : 'The generation status could not be read from the API.'}
      </p>
    )
  }

  if (isPending || !status) {
    return <p className={cn('text-xs text-muted-foreground', className)}>No generation job is running.</p>
  }

  const reported = typeof status.progress === 'number' && Number.isFinite(status.progress)
  const percent = reported ? Math.round(Math.max(0, Math.min(1, status.progress as number)) * 100) : null
  const currentIndex = STAGE_ORDER.indexOf(status.stage)

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant={status.stage === 'failed' ? 'destructive' : status.stage === 'completed' ? 'accent' : 'secondary'}
          className="text-[10px]"
        >
          {STAGE_LABELS[status.stage]}
        </Badge>
        {status.jobId && (
          <span className="font-mono text-[10px] text-muted-foreground">job {status.jobId}</span>
        )}
      </div>

      <ol className="space-y-1">
        {STAGE_ORDER.map((stage, index) => {
          const done = currentIndex >= 0 && index < currentIndex
          const active = stage === status.stage
          return (
            <li key={stage} className="flex items-center gap-2 text-[11px]">
              {done ? (
                <Check className="h-3 w-3 shrink-0 text-accent" aria-hidden />
              ) : active ? (
                <Loader2 className="h-3 w-3 shrink-0 animate-spin text-accent" aria-hidden />
              ) : (
                <CircleDashed className="h-3 w-3 shrink-0 text-muted-foreground/60" aria-hidden />
              )}
              <span className={cn(active ? 'font-medium text-foreground' : 'text-muted-foreground')}>
                {STAGE_LABELS[stage]}
              </span>
            </li>
          )
        })}
      </ol>

      {reported ? (
        <div className="space-y-1">
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <span
              className="block h-full rounded-full bg-accent transition-[width] duration-300"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="text-[10px] tabular-nums text-muted-foreground">
            {percent}% reported by the service
          </p>
        </div>
      ) : (
        <p className="text-[10px] leading-relaxed text-muted-foreground">
          The service has not reported a progress value, so none is shown.
        </p>
      )}

      {status.message && (
        <p className="text-[11px] leading-relaxed text-muted-foreground">{status.message}</p>
      )}
    </div>
  )
}

export interface NotesGenerationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  videoId: string
  document?: NoteDocument
  status?: NotesProcessingStatus
  statusPending?: boolean
  statusError?: unknown
  /** Called once a job was accepted, so the page can start polling. */
  onJobStarted: () => void
}

export function NotesGenerationDialog({
  open,
  onOpenChange,
  videoId,
  document,
  status,
  statusPending,
  statusError,
  onJobStarted,
}: NotesGenerationDialogProps) {
  const [detail, setDetail] = useState<NotesDetailLevel>('balanced')
  const [enhancements, setEnhancements] = useState<NotesEnhancement[]>([
    'equations',
    'tables',
    'flowcharts',
    'timestamps',
  ])

  const generate = useStartNotesGeneration()
  const enhance = useStartNotesEnhancement()
  const busy = generate.isPending || enhance.isPending

  const toggleEnhancement = (value: NotesEnhancement) => {
    setEnhancements((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    )
  }

  const runGeneration = () => {
    generate.mutate(
      { videoId, detail, enhancements },
      { onSuccess: () => onJobStarted() },
    )
  }

  const runEnhancement = () => {
    enhance.mutate(videoId, { onSuccess: () => onJobStarted() })
  }

  const requestError = generate.error ?? enhance.error

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[88vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">Generate notes</DialogTitle>
          <DialogDescription>
            Configure the notes pipeline and the second visual pass. Generation runs on the backend — this
            client never calls an AI provider directly.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          <fieldset className="space-y-2">
            <legend className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Detail level
            </legend>
            <div className="grid gap-2 sm:grid-cols-3">
              {DETAIL_LEVELS.map((level) => {
                const active = level.value === detail
                return (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => setDetail(level.value)}
                    aria-pressed={active}
                    className={cn(
                      'rounded-xl border px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                      active
                        ? 'border-accent/40 bg-accent/[0.07]'
                        : 'border-border bg-card hover:bg-muted/60',
                    )}
                  >
                    <span
                      className={cn(
                        'block text-sm font-medium',
                        active ? 'text-accent' : 'text-foreground',
                      )}
                    >
                      {level.label}
                    </span>
                    <span className="mt-0.5 block text-[11px] leading-snug text-muted-foreground">
                      {level.hint}
                    </span>
                  </button>
                )
              })}
            </div>
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Enhancements
            </legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {ENHANCEMENTS.map((enhancement) => (
                <label
                  key={enhancement.value}
                  className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2 text-[13px] transition-colors hover:bg-muted/60"
                >
                  <input
                    type="checkbox"
                    checked={enhancements.includes(enhancement.value)}
                    onChange={() => toggleEnhancement(enhancement.value)}
                    style={{ accentColor: 'hsl(var(--accent))' }}
                    className="h-4 w-4 rounded border-border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <span className="text-foreground/85">{enhancement.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="rounded-xl border border-border bg-muted/30 p-3">
            <p className="mb-2 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-accent" aria-hidden />
              Pipeline status
            </p>
            <NotesGenerationStatus status={status} isPending={statusPending} error={statusError} />
          </div>

          {requestError && (
            <p role="alert" className="flex items-start gap-2 text-xs text-destructive">
              <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              {requestError instanceof Error
                ? requestError.message
                : 'The generation request could not be sent.'}
            </p>
          )}

          <p className="text-[11px] leading-relaxed text-muted-foreground">
            Notes are only replaced when the backend reports a completed job. Nothing is written locally to
            stand in for a result.
          </p>
        </div>

        <DialogFooter className="gap-2 sm:justify-between">
          <SecondaryButton onClick={runEnhancement} disabled={busy}>
            {enhance.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Wand2 className="h-3.5 w-3.5" />
            )}
            Enhance visually
          </SecondaryButton>

          <div className="flex items-center gap-2">
            <SecondaryButton onClick={() => onOpenChange(false)} disabled={busy}>
              Close
            </SecondaryButton>
            <PrimaryButton onClick={runGeneration} loading={generate.isPending} disabled={enhance.isPending}>
              {generate.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {document ? 'Regenerate notes' : 'Generate notes'}
            </PrimaryButton>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

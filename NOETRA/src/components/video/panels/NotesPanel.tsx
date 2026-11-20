import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Check, Copy, ExternalLink, FileQuestion, Info, RefreshCw, Wand2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { NotesDocumentRenderer } from '@/components/notes/NotesDocumentRenderer'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import { useNoteDocument } from '@/hooks/use-lecture-queries'
import { noteDocumentToMarkdown } from '@/lib/notes/markdown'
import { formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'

/**
 * The "AI Notes" tab in the video workspace.
 *
 * It renders through the shared `NotesDocumentRenderer`, so the workspace tab
 * and the standalone Notes Studio display exactly the same structured document
 * through exactly one renderer implementation.
 */
export interface NotesPanelProps {
  videoId: string
  className?: string
}

export function NotesPanel({ videoId, className }: NotesPanelProps) {
  const { data, isPending, isError, error, refetch } = useNoteDocument(videoId)
  const { copied, copy } = useCopyToClipboard()

  const markdown = useMemo(() => (data ? noteDocumentToMarkdown(data) : ''), [data])

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
        title="Notes unavailable"
        description={error instanceof Error ? error.message : 'The notes could not be loaded.'}
        action={
          <SecondaryButton size="sm" onClick={() => void refetch()}>
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </SecondaryButton>
        }
      />
    )
  }

  const isDemo = data.status === 'demo'

  return (
    <section className={cn('space-y-4', className)}>
      <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-accent" />
              <h2 className="font-serif text-lg font-medium tracking-tight text-foreground">
                AI Notes
              </h2>
              <Badge variant={isDemo ? 'outline' : 'accent'} className="text-[10px]">
                {isDemo ? 'Demonstration document' : 'Generated'}
              </Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {data.title} · v{data.version} · updated {formatDate(data.updatedAt)}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Link to={`/notes/${videoId}`}>
              <PrimaryButton variant="outline" size="sm">
                <ExternalLink className="h-3.5 w-3.5" /> Open Notes Studio
              </PrimaryButton>
            </Link>

            <SecondaryButton
              size="sm"
              onClick={() => void copy(markdown)}
              aria-label="Copy notes as Markdown"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </SecondaryButton>
          </div>
        </div>

        {isDemo && (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-border bg-muted/40 px-3 py-2.5">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <p className="text-xs leading-relaxed text-muted-foreground">
              AI note generation is not connected yet. This is a written demonstration document that
              shows the intended structure — sections, callouts, tables, equations, flowcharts, and
              timestamp links. It was not extracted from the sample clip.
            </p>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-border bg-card p-5 shadow-soft sm:p-6">
        <NotesDocumentRenderer document={data} widthClass="max-w-none" />
      </div>
    </section>
  )
}

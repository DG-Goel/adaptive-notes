import { useMemo } from 'react'
import { FileQuestion, ImageOff, RefreshCw, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { NoteBlockRenderer } from '@/components/notes/NoteBlockRenderer'
import { TimestampChip } from '@/components/video/TimestampText'
import { useNoteDocument } from '@/hooks/use-lecture-queries'
import { ARTIFACT_KIND_META } from '@/lib/notes/artifact-kinds'
import { findBlockById, galleryArtifacts } from '@/lib/notes/visuals'
import { formatDate } from '@/lib/format'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'

/**
 * The "Visuals" tab in the video workspace.
 *
 * The gallery is not a separate artifact collection: it lists exactly the
 * artifacts the note document already renders inline, and renders each one
 * through the same block renderer. There is therefore one source of artifact
 * data and one renderer, with no duplicated preview markup.
 */
export interface VisualsPanelProps {
  videoId: string
  className?: string
}

export function VisualsPanel({ videoId, className }: VisualsPanelProps) {
  const { data, isPending, isError, error, refetch } = useNoteDocument(videoId)

  const artifacts = useMemo(() => galleryArtifacts(data), [data])

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
        title="Visuals unavailable"
        description={error instanceof Error ? error.message : 'The visuals could not be loaded.'}
        action={
          <SecondaryButton size="sm" onClick={() => void refetch()}>
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </SecondaryButton>
        }
      />
    )
  }

  if (artifacts.length === 0) {
    return (
      <EmptyState
        className={className}
        icon={<Sparkles className="h-5 w-5" />}
        title="No visuals yet"
        description="Tables, flowcharts, diagrams, and equations from the notes appear here once the visual-enhancement pass has produced them."
      />
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-start gap-2 rounded-xl border border-border bg-muted/40 px-3 py-2.5">
        <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <p className="text-xs leading-relaxed text-muted-foreground">
          These {artifacts.length} artifacts are the same ones rendered inline in the notes — the
          gallery references the document's artifact data rather than keeping its own copy.
          {data.isDemonstration
            ? ' This build ships a written demonstration document, so nothing here was produced by a generation pipeline.'
            : ` Document updated ${formatDate(data.updatedAt)}.`}
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {artifacts.map((artifact) => {
          const { icon: Icon, label } = ARTIFACT_KIND_META[artifact.kind]
          const block = artifact.blockId ? findBlockById(data, artifact.blockId) : undefined
          const reserved = artifact.status === 'reserved'

          return (
            <article
              key={artifact.id}
              className="flex flex-col rounded-2xl border border-border bg-card p-4 shadow-soft"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                    <Icon className="h-4 w-4" aria-hidden />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">{artifact.title}</p>
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      {label}
                      {artifact.sectionId ? ` · ${artifact.sectionId}` : ''}
                    </p>
                  </div>
                </div>
                <Badge variant={reserved ? 'outline' : 'secondary'} className="shrink-0 text-[10px]">
                  {reserved ? 'Reserved' : artifact.blockId ? 'Inline placement' : 'No placement'}
                </Badge>
              </div>

              {artifact.description && (
                <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">
                  {artifact.description}
                </p>
              )}

              <div className="mt-3 min-w-0">
                {block ? (
                  <NoteBlockRenderer block={block} />
                ) : (
                  <p className="flex items-center gap-2 rounded-xl border border-dashed border-border bg-muted/30 px-3 py-3 text-[11px] text-muted-foreground">
                    <ImageOff className="h-3.5 w-3.5 shrink-0" aria-hidden />
                    This artifact carries placement metadata but no inline block, so there is nothing
                    to render for it yet.
                  </p>
                )}
              </div>

              {typeof artifact.timestamp === 'number' && (
                <div className="mt-auto flex items-center gap-2 border-t border-border pt-3">
                  <span className="text-[11px] text-muted-foreground">In lecture</span>
                  <TimestampChip
                    seconds={artifact.timestamp}
                    label={timestampLabel(artifact.timestamp)}
                  />
                </div>
              )}
            </article>
          )
        })}
      </div>
    </div>
  )
}

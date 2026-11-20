import { FileQuestion } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { NoteBlockRenderer } from './NoteBlockRenderer'
import { TimestampChip } from '@/components/video/TimestampText'
import { ARTIFACT_KIND_META } from '@/lib/notes/artifact-kinds'
import { metaExtras } from '@/lib/notes/blocks'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { NoteBlock, VisualArtifact } from '@/types/notes'

/**
 * Artifacts the visual pass returned without usable placement metadata.
 *
 * They are never inserted at a guessed position. Anything that carries its own
 * block payload is rendered read-only so the reader can still use it; anything
 * else is listed with the metadata that arrived with it.
 */

function embeddedBlock(artifact: VisualArtifact): NoteBlock | null {
  const raw = (artifact.meta ?? {}).block
  if (!raw || typeof raw !== 'object') return null
  const candidate = raw as { id?: unknown; type?: unknown }
  return typeof candidate.id === 'string' && typeof candidate.type === 'string'
    ? (raw as NoteBlock)
    : null
}

export interface NotesUnplacedArtifactsProps {
  artifacts: VisualArtifact[]
  className?: string
}

export function NotesUnplacedArtifacts({ artifacts, className }: NotesUnplacedArtifactsProps) {
  if (artifacts.length === 0) return null

  return (
    <section
      id="note-unplaced-artifacts"
      aria-labelledby="note-unplaced-artifacts-title"
      className={cn(
        'scroll-mt-32 rounded-2xl border border-dashed border-border bg-muted/25 p-5',
        className,
      )}
    >
      <h2
        id="note-unplaced-artifacts-title"
        className="font-serif text-lg font-medium tracking-tight text-foreground"
      >
        Unplaced visual artifacts
      </h2>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
        The visual pass returned {artifacts.length === 1 ? 'one artifact' : `${artifacts.length} artifacts`} without
        usable placement metadata. They are listed here rather than inserted at an estimated position.
      </p>

      <ul className="mt-4 space-y-4">
        {artifacts.map((artifact) => {
          const { icon: Icon, label } = ARTIFACT_KIND_META[artifact.kind]
          const block = embeddedBlock(artifact)
          const extras = metaExtras(artifact.meta)

          return (
            <li key={artifact.id}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{artifact.title}</p>
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
                </div>
                <Badge variant="outline" className="ml-auto text-[10px]">
                  No placement metadata
                </Badge>
                {typeof artifact.timestamp === 'number' && (
                  <TimestampChip
                    seconds={artifact.timestamp}
                    label={timestampLabel(artifact.timestamp)}
                  />
                )}
              </div>

              {artifact.description && (
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                  {artifact.description}
                </p>
              )}

              {block ? (
                <div className="mt-3">
                  <NoteBlockRenderer block={block} />
                </div>
              ) : (
                <p className="mt-3 flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-[11px] text-muted-foreground">
                  <FileQuestion className="h-3.5 w-3.5 shrink-0" aria-hidden />
                  No artifact payload was included, so there is nothing to render for this entry.
                </p>
              )}

              {extras.length > 0 && (
                <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
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
            </li>
          )
        })}
      </ul>
    </section>
  )
}

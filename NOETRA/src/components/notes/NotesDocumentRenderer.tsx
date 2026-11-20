import { useMemo } from 'react'
import 'katex/dist/katex.min.css'
import { Badge } from '@/components/ui/badge'
import { NoteSectionRenderer } from './NoteSectionRenderer'
import { NotesUnplacedArtifacts } from './NotesUnplacedArtifacts'
import { NotesPlaybackProvider } from '@/context/NotesPlaybackProvider'
import { formatDate } from '@/lib/format'
import { metaExtras } from '@/lib/notes/blocks'
import { mergeVisualArtifacts } from '@/lib/notes/visuals'
import { cn } from '@/lib/utils'
import type { EditableNoteBlock, NoteDocument, VisualArtifact } from '@/types/notes'

/**
 * The reusable notes document renderer.
 *
 * Used by the standalone Notes Studio and by the "AI Notes" tab in the video
 * workspace, so a document only ever has one rendering implementation. Visual
 * artifacts supplied separately by the visual pass are merged here through the
 * explicit-placement adapter — never by estimating an insertion point.
 *
 * Wrapping in `NotesPlaybackProvider` is what makes timestamp chips seek the
 * shared player when one is mounted and deep-link to the lecture when not.
 */
export interface NotesDocumentRendererProps {
  document: NoteDocument
  /** Artifacts from the visual pass, merged before rendering. */
  artifacts?: VisualArtifact[]
  /** Search target: highlighted and (by the caller) scrolled into view. */
  highlightedBlockId?: string
  /** Sections the reader has collapsed. */
  collapsedSections?: ReadonlySet<string>
  onToggleCollapse?: (sectionId: string) => void
  /** Present only in editing mode; artifact blocks stay read-only. */
  onEditBlock?: (block: EditableNoteBlock) => void
  editing?: boolean
  /** The studio renders its own toolbar header; the workspace tab does not. */
  showHeader?: boolean
  /** Reading width, controlled by the reading-mode switch. */
  widthClass?: string
  className?: string
}

export function NotesDocumentRenderer({
  document,
  artifacts,
  highlightedBlockId,
  collapsedSections,
  onToggleCollapse,
  onEditBlock,
  editing = false,
  showHeader = false,
  widthClass = 'max-w-3xl',
  className,
}: NotesDocumentRendererProps) {
  const resolved = useMemo(() => {
    if (!artifacts || artifacts.length === 0) return document
    return mergeVisualArtifacts(document, artifacts).document
  }, [document, artifacts])

  const documentMeta = useMemo(() => metaExtras(resolved.meta), [resolved.meta])
  const unplaced = resolved.unplacedArtifacts ?? []

  return (
    <NotesPlaybackProvider videoId={resolved.videoId}>
      <article
        aria-labelledby={showHeader ? 'notes-document-title' : undefined}
        className={cn('mx-auto w-full', widthClass, className)}
      >
        {showHeader && (
          <header className="mb-8 border-b border-border pb-5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={resolved.status === 'demo' ? 'outline' : 'accent'} className="text-[10px]">
                {resolved.status === 'demo'
                  ? 'Demonstration document'
                  : resolved.status === 'stale'
                    ? 'Out of date'
                    : 'Generated'}
              </Badge>
              <Badge variant="secondary" className="text-[10px]">
                v{resolved.version}
              </Badge>
              <span className="text-[11px] text-muted-foreground">
                Updated {formatDate(resolved.updatedAt)}
              </span>
            </div>
            <h1
              id="notes-document-title"
              className="mt-3 font-serif text-3xl font-medium tracking-tight text-foreground sm:text-4xl"
            >
              {resolved.title}
            </h1>
            {resolved.subtitle && (
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {resolved.subtitle}
              </p>
            )}
          </header>
        )}

        <div className="space-y-10">
          {resolved.sections.map((section) => (
            <NoteSectionRenderer
              key={section.id}
              section={section}
              videoId={resolved.videoId}
              collapsed={collapsedSections?.has(section.id) ?? false}
              onToggleCollapse={onToggleCollapse}
              highlightedBlockId={highlightedBlockId}
              onEditBlock={onEditBlock}
              editing={editing}
            />
          ))}
        </div>

        {unplaced.length > 0 && <NotesUnplacedArtifacts artifacts={unplaced} className="mt-10" />}

        {documentMeta.length > 0 && (
          <footer className="mt-10 border-t border-border pt-4">
            <details className="text-[11px] text-muted-foreground">
              <summary className="cursor-pointer select-none rounded-md py-1 font-medium text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                Document metadata
              </summary>
              <dl className="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2">
                {documentMeta.map((entry) => (
                  <div key={entry.key} className="flex items-baseline gap-2">
                    <dt className="uppercase tracking-wide text-muted-foreground">{entry.key}</dt>
                    <dd className="min-w-0 break-words text-foreground/75">{entry.value}</dd>
                  </div>
                ))}
              </dl>
            </details>
          </footer>
        )}
      </article>
    </NotesPlaybackProvider>
  )
}

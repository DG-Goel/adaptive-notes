import { useMemo } from 'react'
import { ImageOff, Network, TriangleAlert } from 'lucide-react'
import { FlowchartBlock } from './FlowchartBlock'
import { metaExtras } from '@/lib/notes/blocks'
import { cn } from '@/lib/utils'
import type { NoteDiagramBlock } from '@/types/notes'

/**
 * Diagram artifact.
 *
 * Only formats this build can genuinely display are rendered:
 * - `flow` reuses the interactive React Flow flowchart renderer;
 * - `image` shows the referenced image;
 * - `mermaid` shows the source verbatim, because no Mermaid renderer is
 *   installed — the alternative would be fabricating a picture of it;
 * - anything else degrades to a labelled unsupported state that keeps the
 *   original payload metadata visible.
 */
export interface DiagramBlockProps {
  block: NoteDiagramBlock
  /** Renders inside a smaller frame, used by the visuals gallery. */
  compact?: boolean
  className?: string
}

export function DiagramBlock({ block, compact = false, className }: DiagramBlockProps) {
  const extras = useMemo(() => metaExtras(block.meta), [block.meta])

  if (block.format === 'flow' && block.nodes && block.nodes.length > 0) {
    return (
      <FlowchartBlock
        nodes={block.nodes}
        edges={block.edges ?? []}
        direction="LR"
        caption={block.caption ?? 'Diagram'}
        meta={block.meta}
        compact={compact}
        className={className}
      />
    )
  }

  if (block.format === 'image') {
    return (
      <figure
        className={cn('my-4 overflow-hidden rounded-xl border border-border bg-card shadow-soft', className)}
      >
        <figcaption className="flex items-center gap-2 border-b border-border px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Network className="h-3.5 w-3.5 text-accent" aria-hidden />
          {block.caption ?? 'Diagram'}
        </figcaption>
        {block.src ? (
          <img
            src={block.src}
            alt={block.caption ?? 'Diagram'}
            loading="lazy"
            className="mx-auto block max-h-[520px] w-full object-contain p-3"
          />
        ) : (
          <div className="flex items-center gap-2 px-4 py-6 text-xs text-muted-foreground">
            <ImageOff className="h-4 w-4" aria-hidden />
            This diagram artifact has no image source.
          </div>
        )}
      </figure>
    )
  }

  if (block.format === 'mermaid' && block.source) {
    return (
      <figure
        className={cn('my-4 overflow-hidden rounded-xl border border-border bg-card shadow-soft', className)}
      >
        <figcaption className="flex items-center gap-2 border-b border-border px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Network className="h-3.5 w-3.5 text-accent" aria-hidden />
          {block.caption ?? 'Mermaid diagram'}
        </figcaption>
        <pre className="note-code overflow-x-auto bg-sidebar px-4 py-3.5 font-mono text-[12.5px] leading-relaxed text-sidebar-foreground">
          <code>{block.source}</code>
        </pre>
        <figcaption className="border-t border-border px-4 py-2 text-[11px] leading-relaxed text-muted-foreground">
          Mermaid source. A Mermaid renderer is not installed in this build, so the diagram source
          is shown exactly as the note provided it.
        </figcaption>
      </figure>
    )
  }

  // Unknown or incomplete diagram payload: keep the artifact visible and say so.
  return (
    <div
      role="note"
      className={cn(
        'my-4 rounded-xl border border-dashed border-border bg-muted/30 px-4 py-3.5',
        className,
      )}
    >
      <p className="flex items-center gap-2 text-sm font-medium text-foreground">
        <TriangleAlert className="h-4 w-4 text-accent" aria-hidden />
        Diagram format not supported
      </p>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
        {block.caption ? `${block.caption} — ` : ''}
        This artifact was delivered as <span className="font-mono">{block.format}</span>, which this
        build cannot display. The original payload is preserved below rather than being rendered as
        a guess.
      </p>
      <pre className="note-code mt-2 overflow-x-auto rounded-lg border border-white/10 bg-sidebar px-3 py-2 font-mono text-[11.5px] text-sidebar-foreground">
        <code>{JSON.stringify(block.payload ?? { format: block.format }, null, 2)}</code>
      </pre>
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
    </div>
  )
}

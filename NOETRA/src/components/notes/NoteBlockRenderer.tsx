import { Suspense, lazy, memo } from 'react'
import { Clock, ImageOff, Loader2, Quote, TriangleAlert } from 'lucide-react'
import { CalloutBlock } from './CalloutBlock'
import { CodeBlock } from './CodeBlock'
import { InlineMarkdown } from './InlineMarkdown'
import { MarkdownBlock } from './MarkdownBlock'
import { MathBlock } from './MathBlock'
import { NoteRenderBoundary } from './NoteRenderBoundary'
import { TableBlock } from './TableBlock'
import { TimestampChip } from '@/components/video/TimestampText'
import { blockAnchorId, isArtifactBlock, metaExtras } from '@/lib/notes/blocks'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { NoteBlock, NoteListItem, NoteListBlock } from '@/types/notes'

/**
 * Renders one structured note block.
 *
 * Document order is owned by the caller: this component only turns a block into
 * markup and never reorders or drops anything. Third-party pipelines (KaTeX,
 * highlight.js, React Flow, tables) are individually wrapped in an error
 * boundary so one broken artifact cannot blank the document.
 */

/** Section titles occupy h2–h4, so a block heading starts one level below. */
function headingTag(level: 1 | 2 | 3 | 4): 'h3' | 'h4' | 'h5' | 'h6' {
  return `h${level + 2}` as 'h3' | 'h4' | 'h5' | 'h6'
}

const HEADING_CLASSES: Record<'h3' | 'h4' | 'h5' | 'h6', string> = {
  h3: 'mt-6 mb-2 font-serif text-xl font-medium tracking-tight text-foreground',
  h4: 'mt-5 mb-2 font-serif text-lg font-medium text-foreground',
  h5: 'mt-4 mb-1.5 text-sm font-semibold uppercase tracking-wide text-muted-foreground',
  h6: 'mt-3 mb-1.5 text-sm font-semibold text-foreground',
}

/**
 * The flow/diagram renderers pull in React Flow, which is the heaviest
 * artifact code in the notes. They are code-split out of the initial bundle
 * and fetched only when a flowchart or diagram is actually on screen.
 */
const FlowchartBlock = lazy(() =>
  import('./FlowchartBlock').then((module) => ({ default: module.FlowchartBlock })),
)
const DiagramBlock = lazy(() =>
  import('./DiagramBlock').then((module) => ({ default: module.DiagramBlock })),
)

/** Placeholder shown while a code-split artifact renderer loads. */
function ArtifactLoading({ label }: { label: string }) {
  return (
    <div
      aria-hidden
      className="my-4 flex h-40 items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-muted/25 text-[11px] text-muted-foreground"
    >
      <Loader2 className="h-3.5 w-3.5 animate-spin" />
      Loading {label}…
    </div>
  )
}

function ListItems({ block, depth = 0 }: { block: NoteListBlock; depth?: number }) {
  const Tag = block.ordered ? 'ol' : 'ul'
  return (
    <Tag
      className={cn(
        'space-y-1.5',
        depth === 0 ? 'my-3' : 'mt-1.5',
        block.ordered ? 'list-decimal pl-5' : 'pl-1',
      )}
    >
      {block.items.map((item: NoteListItem) => (
        <li
          key={item.id}
          className={cn(
            'text-sm leading-relaxed text-foreground/85 marker:text-accent',
            !block.ordered &&
              "flex gap-2.5 before:mt-[0.45rem] before:h-1.5 before:w-1.5 before:shrink-0 before:rounded-full before:bg-accent/60 before:content-['']",
          )}
        >
          <span className="min-w-0">
            <InlineMarkdown text={item.content} />
            {item.items && item.items.length > 0 && (
              <ListItems block={{ ...block, items: item.items }} depth={depth + 1} />
            )}
          </span>
        </li>
      ))}
    </Tag>
  )
}

/** Timestamp plus any backend metadata that no artifact component already shows. */
function BlockFooter({ block }: { block: NoteBlock }) {
  const extras = isArtifactBlock(block) ? [] : metaExtras(block.meta)
  if (block.startSeconds === undefined && extras.length === 0) return null

  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
      {block.startSeconds !== undefined && (
        <span className="inline-flex items-center gap-1.5">
          <Clock className="h-3 w-3" aria-hidden />
          <TimestampChip seconds={block.startSeconds} label={timestampLabel(block.startSeconds)} />
        </span>
      )}
      {extras.map((entry) => (
        <span key={entry.key} className="inline-flex items-baseline gap-1.5">
          <span className="uppercase tracking-wide">{entry.key}</span>
          <span className="text-foreground/70">{entry.value}</span>
        </span>
      ))}
    </div>
  )
}

function UnsupportedBlock({ block }: { block: Extract<NoteBlock, { type: 'unknown' }> }) {
  return (
    <div
      role="note"
      className="my-4 rounded-xl border border-dashed border-border bg-muted/30 px-4 py-3.5"
    >
      <p className="flex items-center gap-2 text-sm font-medium text-foreground">
        <TriangleAlert className="h-4 w-4 text-accent" aria-hidden />
        Unsupported block type
      </p>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
        The backend sent a <span className="font-mono">{block.originalType}</span> block that this
        build does not render yet. It is kept in the document with its metadata rather than being
        silently removed.
      </p>
      {metaExtras(block.meta).length > 0 && (
        <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {metaExtras(block.meta).map((entry) => (
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

function ImageBlock({ block }: { block: Extract<NoteBlock, { type: 'image' }> }) {
  return (
    <figure className="my-4 overflow-hidden rounded-xl border border-border bg-card shadow-soft">
      {block.src ? (
        <img
          src={block.src}
          alt={block.alt}
          loading="lazy"
          className="mx-auto block max-h-[520px] w-full object-contain p-3"
        />
      ) : (
        <div className="flex items-center gap-2 px-4 py-6 text-xs text-muted-foreground">
          <ImageOff className="h-4 w-4" aria-hidden />
          This image artifact has no source.
        </div>
      )}
      {block.caption && (
        <figcaption className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          {block.caption}
        </figcaption>
      )}
    </figure>
  )
}

function renderContent(block: NoteBlock) {
  switch (block.type) {
    case 'markdown':
      return <MarkdownBlock content={block.content} />
    case 'heading': {
      const Tag = headingTag(block.level)
      return (
        <Tag className={HEADING_CLASSES[Tag]}>
          <InlineMarkdown text={block.content} />
        </Tag>
      )
    }
    case 'paragraph':
      return (
        <p className="my-3 text-sm leading-relaxed text-foreground/85">
          <InlineMarkdown text={block.content} />
        </p>
      )
    case 'list':
      return <ListItems block={block} />
    case 'code':
      return (
        <CodeBlock code={block.content} language={block.language} title={block.title} meta={block.meta} />
      )
    case 'math':
      return (
        <NoteRenderBoundary label="Equation">
          <MathBlock
            latex={block.latex}
            displayMode={block.displayMode}
            description={block.description}
            meta={block.meta}
          />
        </NoteRenderBoundary>
      )
    case 'table':
      return (
        <NoteRenderBoundary label="Table">
          <TableBlock block={block} />
        </NoteRenderBoundary>
      )
    case 'flowchart':
      return (
        <NoteRenderBoundary label="Flowchart">
          <Suspense fallback={<ArtifactLoading label="flowchart" />}>
            <FlowchartBlock
              nodes={block.nodes}
              edges={block.edges}
              direction={block.direction}
              caption={block.caption}
              meta={block.meta}
            />
          </Suspense>
        </NoteRenderBoundary>
      )
    case 'diagram':
      return (
        <NoteRenderBoundary label="Diagram">
          <Suspense fallback={<ArtifactLoading label="diagram" />}>
            <DiagramBlock block={block} />
          </Suspense>
        </NoteRenderBoundary>
      )
    case 'image':
      return <ImageBlock block={block} />
    case 'callout':
      return (
        <CalloutBlock
          tone={block.tone}
          title={block.title}
          content={block.content}
          meta={block.meta}
        />
      )
    case 'quote':
      return (
        <blockquote className="my-4 rounded-r-xl border-l-2 border-accent/50 bg-accent/[0.05] py-2.5 pr-3 pl-4">
          <p className="flex gap-2 text-sm leading-relaxed text-foreground/85 italic">
            <Quote className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent/70" aria-hidden />
            <span>
              <InlineMarkdown text={block.content} />
            </span>
          </p>
          {block.attribution && (
            <footer className="mt-1.5 pl-5 text-[11px] text-muted-foreground">
              — {block.attribution}
            </footer>
          )}
        </blockquote>
      )
    case 'unknown':
      return <UnsupportedBlock block={block} />
    default:
      return null
  }
}

export interface NoteBlockRendererProps {
  block: NoteBlock
  /** Set by search to mark the block the reader is currently on. */
  highlighted?: boolean
  className?: string
}

export const NoteBlockRenderer = memo(function NoteBlockRenderer({
  block,
  highlighted = false,
  className,
}: NoteBlockRendererProps) {
  return (
    <div
      id={blockAnchorId(block.id)}
      data-block-id={block.id}
      data-block-type={block.type}
      className={cn(
        'scroll-mt-32 rounded-xl transition-colors',
        highlighted && 'bg-accent/[0.06] ring-1 ring-accent/40 ring-offset-4 ring-offset-background',
        className,
      )}
    >
      {renderContent(block)}
      <BlockFooter block={block} />
    </div>
  )
})

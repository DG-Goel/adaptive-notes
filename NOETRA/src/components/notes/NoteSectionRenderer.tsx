import { BrainCircuit, Check, ChevronDown, Copy, Layers, Map, Pencil, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { NoteBlockRenderer } from './NoteBlockRenderer'
import { TimestampChip } from '@/components/video/TimestampText'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import { useTutorConversation } from '@/context/tutor-conversation-context'
import { isArtifactBlock, isEditableBlock, sectionAnchorId } from '@/lib/notes/blocks'
import { sectionClipboardText } from '@/lib/notes/markdown'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { EditableNoteBlock, NoteBlock, NoteSection } from '@/types/notes'

/**
 * One document section: heading, inline blocks in document order, and the
 * section utilities (collapse, copy).
 *
 * The heading level is derived from the section's own depth so the document
 * keeps a real, skippable-free outline for screen readers.
 */

const HEADING_CLASSES: Record<NoteSection['level'], string> = {
  1: 'font-serif text-2xl font-medium tracking-tight text-foreground sm:text-[1.75rem]',
  2: 'font-serif text-xl font-medium tracking-tight text-foreground',
  3: 'font-serif text-lg font-medium text-foreground',
}

export interface NoteSectionRendererProps {
  section: NoteSection
  videoId?: string
  collapsed?: boolean
  onToggleCollapse?: (sectionId: string) => void
  /** Block the reader is currently on, set by search. */
  highlightedBlockId?: string
  /** Present only in editing mode. Read-only artifacts stay untouched. */
  onEditBlock?: (block: EditableNoteBlock) => void
  editing?: boolean
  className?: string
}

export function NoteSectionRenderer({
  section,
  videoId,
  collapsed = false,
  onToggleCollapse,
  highlightedBlockId,
  onEditBlock,
  editing = false,
  className,
}: NoteSectionRendererProps) {
  const { copied, copy } = useCopyToClipboard()
  const navigate = useNavigate()
  const { newConversation, setDraft } = useTutorConversation()
  const titleId = `${sectionAnchorId(section.id)}-title`
  const headingClass = cn('min-w-0', HEADING_CLASSES[section.level])
  const artifactCount = section.blocks.filter(isArtifactBlock).length
  const collapsible = Boolean(onToggleCollapse)

  const askAboutSection = (prompt: string) => {
    if (!videoId) return
    const context = { type: 'notes' as const, videoId, sectionId: section.id }
    const id = newConversation(context, `About: ${section.title}`)
    setDraft(prompt)
    // The conversation provider holds the draft; navigate to the full Tutor.
    void id
    navigate('/tutor')
  }

  return (
    <section
      id={sectionAnchorId(section.id)}
      data-section-id={section.id}
      aria-labelledby={titleId}
      className={cn('scroll-mt-32', className)}
    >
      <div className="group/section flex flex-wrap items-center gap-x-3 gap-y-2">
        {collapsible && (
          <button
            type="button"
            onClick={() => onToggleCollapse?.(section.id)}
            aria-expanded={!collapsed}
            aria-controls={`${sectionAnchorId(section.id)}-body`}
            aria-label={collapsed ? `Expand ${section.title}` : `Collapse ${section.title}`}
            className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ChevronDown className={cn('h-4 w-4 transition-transform', collapsed && '-rotate-90')} />
          </button>
        )}

        {section.level === 1 && (
          <h2 id={titleId} className={headingClass}>
            {section.title}
          </h2>
        )}
        {section.level === 2 && (
          <h3 id={titleId} className={headingClass}>
            {section.title}
          </h3>
        )}
        {section.level === 3 && (
          <h4 id={titleId} className={headingClass}>
            {section.title}
          </h4>
        )}

        {section.startSeconds !== undefined && (
          <TimestampChip
            seconds={section.startSeconds}
            label={timestampLabel(section.startSeconds)}
          />
        )}

        <span className="hidden items-center gap-2 text-[11px] text-muted-foreground sm:flex">
          <Layers className="h-3 w-3" aria-hidden />
          {section.blocks.length} blocks
          {artifactCount > 0 && ` · ${artifactCount} visuals`}
        </span>

        <button
          type="button"
          onClick={() => void copy(sectionClipboardText(section))}
          aria-label={`Copy “${section.title}” as Markdown`}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover/section:opacity-100"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>

        {videoId && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Ask AI about this section"
                className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover/section:opacity-100"
              >
                <Sparkles className="h-3 w-3" />
                Ask AI
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onSelect={() => askAboutSection('Summarize this section.')}>
                Summarize this section
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => askAboutSection('Explain this section simply.')}>
                Explain this simply
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => askAboutSection('Give a practical example from this section.')}>
                Give an example
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => askAboutSection('Simplify the key concept in this section.')}>
                Simplify this concept
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => navigate(`/quiz/${videoId}`)}>
                <BrainCircuit className="mr-2 h-3.5 w-3.5" />
                Practice with quiz
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => navigate(`/knowledge/${videoId}`)}>
                <Map className="mr-2 h-3.5 w-3.5" />
                Explore in knowledge map
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      <div
        id={`${sectionAnchorId(section.id)}-body`}
        hidden={collapsed}
        className="mt-3 space-y-1 border-l border-border/70 pl-4 sm:pl-5"
      >
        {section.blocks.map((block: NoteBlock) => (
          <div key={block.id} className="group/block relative">
            <NoteBlockRenderer
              block={block}
              highlighted={highlightedBlockId === block.id}
              className={editing && isArtifactBlock(block) ? 'opacity-95' : undefined}
            />
            {editing && onEditBlock && isEditableBlock(block) && (
              <button
                type="button"
                onClick={() => onEditBlock(block)}
                aria-label={`Edit block ${block.type}`}
                className="absolute -top-1 right-0 inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2 py-1 text-[11px] font-medium text-muted-foreground opacity-0 shadow-soft transition-opacity hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover/block:opacity-100"
              >
                <Pencil className="h-3 w-3" />
                Edit
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

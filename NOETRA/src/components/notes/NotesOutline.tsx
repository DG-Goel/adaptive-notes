import { useMemo } from 'react'
import { ChevronDown, ChevronRight, ListTree } from 'lucide-react'
import { TimestampChip } from '@/components/video/TimestampText'
import { buildOutlineTree } from '@/lib/notes/outline'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { OutlineEntry, OutlineNode } from '@/lib/notes/outline'

/**
 * Hierarchical table of contents.
 *
 * Nesting comes from the section levels in the document model, so the outline
 * always mirrors the notes instead of being maintained separately. Parents are
 * collapsible, the section the reader is on is marked, and each row can be
 * clicked (or timestamped) to navigate.
 */

export interface NotesOutlineProps {
  entries: OutlineEntry[]
  activeSectionId?: string
  collapsedGroups: ReadonlySet<string>
  onToggleGroup: (sectionId: string) => void
  onNavigate: (sectionId: string) => void
  className?: string
}

export function NotesOutline({
  entries,
  activeSectionId,
  collapsedGroups,
  onToggleGroup,
  onNavigate,
  className,
}: NotesOutlineProps) {
  const tree = useMemo(() => buildOutlineTree(entries), [entries])
  const activeIndex = entries.findIndex((entry) => entry.id === activeSectionId)
  const progress = entries.length > 0 ? ((activeIndex + 1) / entries.length) * 100 : 0

  const renderNode = (node: OutlineNode, depth: number) => {
    const { entry } = node
    const collapsed = collapsedGroups.has(entry.id)
    const active = entry.id === activeSectionId
    const hasChildren = node.children.length > 0

    return (
      <li key={entry.id}>
        <div
          className={cn(
            'group flex items-center gap-1 rounded-lg pr-1 transition-colors',
            active ? 'bg-accent/[0.08]' : 'hover:bg-muted/70',
          )}
          style={{ paddingLeft: `${depth * 0.75}rem` }}
        >
          {hasChildren ? (
            <button
              type="button"
              onClick={() => onToggleGroup(entry.id)}
              aria-expanded={!collapsed}
              aria-label={collapsed ? `Expand ${entry.title}` : `Collapse ${entry.title}`}
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {collapsed ? (
                <ChevronRight className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </button>
          ) : (
            <span className="h-6 w-6 shrink-0" aria-hidden />
          )}

          <button
            type="button"
            onClick={() => onNavigate(entry.id)}
            aria-current={active ? 'true' : undefined}
            className={cn(
              'min-w-0 flex-1 rounded-md py-1.5 text-left text-[13px] leading-snug transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              active ? 'font-medium text-accent' : 'text-foreground/80 hover:text-foreground',
            )}
          >
            <span className="line-clamp-2">{entry.title}</span>
            <span className="mt-0.5 block text-[10px] uppercase tracking-wide text-muted-foreground">
              {entry.blockCount} blocks
              {entry.artifactCount > 0 ? ` · ${entry.artifactCount} visuals` : ''}
            </span>
          </button>

          {typeof entry.startSeconds === 'number' && (
            <TimestampChip
              seconds={entry.startSeconds}
              label={timestampLabel(entry.startSeconds)}
              className="shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
            />
          )}
        </div>

        {hasChildren && !collapsed && (
          <ul className="mt-0.5 space-y-0.5">{node.children.map((child) => renderNode(child, depth + 1))}</ul>
        )}
      </li>
    )
  }

  return (
    <nav aria-label="Document outline" className={cn('flex min-h-0 flex-col', className)}>
      <div className="flex items-center gap-2 px-1 pb-2">
        <ListTree className="h-3.5 w-3.5 text-accent" aria-hidden />
        <h2 className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Outline
        </h2>
      </div>

      <div
        className="mx-1 mb-2 h-0.5 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-label="Reading progress by section"
        aria-valuemin={0}
        aria-valuemax={entries.length}
        aria-valuenow={activeIndex + 1}
      >
        <span
          className="block h-full rounded-full bg-accent/70 transition-[width] duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {entries.length === 0 ? (
        <p className="px-1 text-xs text-muted-foreground">This document has no sections.</p>
      ) : (
        <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto pb-2 pr-0.5">
          {tree.map((node) => renderNode(node, 0))}
        </ul>
      )}
    </nav>
  )
}

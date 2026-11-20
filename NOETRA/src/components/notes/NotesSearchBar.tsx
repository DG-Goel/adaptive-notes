import { ChevronDown, ChevronUp, X } from 'lucide-react'
import { SearchField } from '@/components/common/SearchField'
import { cn } from '@/lib/utils'

/**
 * Document search controls.
 *
 * Match counting is delegated to the caller (which runs `searchNoteDocument`),
 * so the counter always reflects the same results the document highlights.
 */
export interface NotesSearchBarProps {
  query: string
  onQueryChange: (query: string) => void
  matchCount: number
  /** Zero-based index of the match the reader is on. */
  activeIndex: number
  onPrevious: () => void
  onNext: () => void
  className?: string
}

export function NotesSearchBar({
  query,
  onQueryChange,
  matchCount,
  activeIndex,
  onPrevious,
  onNext,
  className,
}: NotesSearchBarProps) {
  const hasQuery = query.trim().length > 0
  const position = matchCount === 0 ? 0 : activeIndex + 1
  const status = !hasQuery
    ? 'Search inside these notes'
    : matchCount === 0
      ? 'No matches'
      : `Match ${position} of ${matchCount}`

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <SearchField
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key !== 'Enter' || matchCount === 0) return
          event.preventDefault()
          if (event.shiftKey) onPrevious()
          else onNext()
        }}
        placeholder="Search notes…"
        aria-label="Search inside the notes"
        className="h-9 text-sm"
      />

      <span
        aria-live="polite"
        className="hidden shrink-0 text-[11px] tabular-nums text-muted-foreground sm:inline"
      >
        {status}
      </span>

      <div className="flex shrink-0 items-center gap-0.5">
        <button
          type="button"
          onClick={onPrevious}
          disabled={matchCount === 0}
          aria-label="Previous match"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronUp className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={matchCount === 0}
          aria-label="Next match"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronDown className="h-4 w-4" />
        </button>
        {hasQuery && (
          <button
            type="button"
            onClick={() => onQueryChange('')}
            aria-label="Clear search"
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

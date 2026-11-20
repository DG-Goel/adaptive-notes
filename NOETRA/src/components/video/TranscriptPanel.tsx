import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Check, Copy, FileQuestion, MicVocal, RefreshCw, ScrollText } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { SearchField } from '@/components/common/SearchField'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { formatTime } from '@/lib/format'
import { useVideoPlayer, useVideoTime } from '@/context/video-player-context'
import { useTranscript } from '@/hooks/use-lecture-queries'
import type { TranscriptSegment } from '@/types/transcript'

/** Wrap every occurrence of `query` in a highlight mark. */
function highlightMatches(text: string, query: string): ReactNode {
  const needle = query.trim().toLowerCase()
  if (!needle) return text
  const haystack = text.toLowerCase()
  const parts: ReactNode[] = []
  let cursor = 0
  let found = haystack.indexOf(needle)
  while (found !== -1) {
    if (found > cursor) parts.push(text.slice(cursor, found))
    parts.push(
      <mark
        key={`${found}-${parts.length}`}
        className="rounded bg-accent/20 px-[2px] text-foreground"
      >
        {text.slice(found, found + needle.length)}
      </mark>,
    )
    cursor = found + needle.length
    found = haystack.indexOf(needle, cursor)
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return parts
}

interface TranscriptRowProps {
  segment: TranscriptSegment
  isActive: boolean
  query: string
  onSeek(time: number): void
  registerRef(id: string, node: HTMLButtonElement | null): void
}

/**
 * Memoised so the ~10 Hz playback position updates only re-render the row
 * whose active state actually changed.
 */
const TranscriptRow = memo(function TranscriptRow({
  segment,
  isActive,
  query,
  onSeek,
  registerRef,
}: TranscriptRowProps) {
  const reduceMotion = useReducedMotion()
  return (
    <li>
      <button
        type="button"
        ref={(node) => registerRef(segment.id, node)}
        onClick={() => onSeek(segment.startTime)}
        aria-current={isActive ? 'true' : undefined}
        className={cn(
          'relative flex w-full gap-3 rounded-xl px-3 py-2.5 text-left transition-colors',
          isActive ? 'bg-accent/[0.07]' : 'hover:bg-muted/60',
        )}
      >
        {isActive && (
          <motion.span
            layoutId={reduceMotion ? undefined : 'active-transcript-marker'}
            className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent"
            transition={{ duration: 0.2 }}
          />
        )}
        <span
          className={cn(
            'mt-0.5 shrink-0 font-mono text-[11px] tabular-nums transition-colors',
            isActive ? 'text-accent' : 'text-muted-foreground',
          )}
        >
          {formatTime(segment.startTime)}
        </span>
        <span className="min-w-0 flex-1">
          {segment.speaker && (
            <span className="mb-0.5 flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              <MicVocal className="h-3 w-3" />
              {segment.speaker}
            </span>
          )}
          <span
            className={cn(
              'block text-sm leading-relaxed',
              isActive ? 'text-foreground' : 'text-foreground/80',
            )}
          >
            {highlightMatches(segment.text, query)}
          </span>
        </span>
      </button>
    </li>
  )
})

interface TranscriptListProps {
  segments: TranscriptSegment[]
  query: string
  autoScroll: boolean
}

function TranscriptList({ segments, query, autoScroll }: TranscriptListProps) {
  const { seekTo } = useVideoPlayer()
  const currentTime = useVideoTime()
  const reduceMotion = useReducedMotion()
  const containerRef = useRef<HTMLDivElement>(null)
  const rowRefs = useRef(new Map<string, HTMLButtonElement>())

  const registerRef = useCallback((id: string, node: HTMLButtonElement | null) => {
    if (node) rowRefs.current.set(id, node)
    else rowRefs.current.delete(id)
  }, [])

  const activeId = useMemo(() => {
    const match = segments.find(
      (segment) => currentTime >= segment.startTime && currentTime < segment.endTime,
    )
    return match?.id ?? null
  }, [segments, currentTime])

  useEffect(() => {
    if (!autoScroll || !activeId) return
    const container = containerRef.current
    const node = rowRefs.current.get(activeId)
    if (!container || !node) return
    const top = node.offsetTop - container.clientHeight / 2 + node.clientHeight / 2
    container.scrollTo({ top: Math.max(top, 0), behavior: reduceMotion ? 'auto' : 'smooth' })
  }, [autoScroll, activeId, reduceMotion])

  return (
    <div
      ref={containerRef}
      className="relative max-h-[58vh] overflow-y-auto pr-1 [scrollbar-gutter:stable]"
    >
      <ol className="space-y-0.5">
        {segments.map((segment) => (
          <TranscriptRow
            key={segment.id}
            segment={segment}
            isActive={segment.id === activeId}
            query={query}
            onSeek={seekTo}
            registerRef={registerRef}
          />
        ))}
      </ol>
    </div>
  )
}

export interface TranscriptPanelProps {
  videoId: string
  className?: string
}

/**
 * Synchronised lecture transcript.
 *
 * Search, auto-scroll, copy, and click-to-seek all operate on the shared
 * playback controller, so the transcript never owns playback state itself.
 */
export function TranscriptPanel({ videoId, className }: TranscriptPanelProps) {
  const { data, isPending, isError, error, refetch } = useTranscript(videoId)
  const { isIllustrative } = useVideoPlayer()
  const [query, setQuery] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const [copied, setCopied] = useState(false)

  const segments = useMemo(() => data?.segments ?? [], [data])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return segments
    return segments.filter((segment) => segment.text.toLowerCase().includes(needle))
  }, [segments, query])

  const handleCopy = useCallback(async () => {
    if (segments.length === 0) return
    const text = segments
      .map((segment) => `[${formatTime(segment.startTime)}] ${segment.text}`)
      .join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }, [segments])

  if (isPending) {
    return (
      <div className={cn('rounded-2xl border border-border bg-card p-5', className)}>
        <LoadingSkeleton variant="list" />
      </div>
    )
  }

  if (isError) {
    return (
      <EmptyState
        className={className}
        icon={<FileQuestion className="h-5 w-5" />}
        title="Transcript unavailable"
        description={error instanceof Error ? error.message : 'The transcript could not be loaded.'}
        action={
          <SecondaryButton size="sm" onClick={() => void refetch()}>
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </SecondaryButton>
        }
      />
    )
  }

  if (segments.length === 0) {
    return (
      <EmptyState
        className={className}
        icon={<ScrollText className="h-5 w-5" />}
        title="No transcript yet"
        description="A transcript will appear here once the lecture has been processed."
      />
    )
  }

  return (
    <section
      className={cn('rounded-2xl border border-border bg-card p-4 shadow-soft', className)}
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <ScrollText className="h-4 w-4 text-accent" />
          <h2 className="font-serif text-lg font-medium tracking-tight text-foreground">
            Transcript
          </h2>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            {data?.language?.toUpperCase() ?? 'EN'}
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                aria-pressed={autoScroll}
                onClick={() => setAutoScroll((value) => !value)}
                className={cn(
                  'inline-flex h-9 items-center gap-1.5 rounded-lg px-2.5 text-xs font-medium transition-colors',
                  autoScroll
                    ? 'bg-accent/10 text-accent'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                )}
              >
                Auto-scroll
              </button>
            </TooltipTrigger>
            <TooltipContent>Follow the playback position automatically</TooltipContent>
          </Tooltip>

          <SecondaryButton size="sm" onClick={() => void handleCopy()}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </SecondaryButton>
        </div>
      </div>

      {isIllustrative && (
        <p className="mt-3 rounded-lg bg-amber-500/[0.08] px-2.5 py-1.5 text-[11px] leading-relaxed text-amber-600">
          Illustrative transcript — these timestamps describe the lecture, not the shorter sample
          clip in the player, so seeking jumps to the nearest available position in the clip.
        </p>
      )}

      <div className="mt-3 flex items-center gap-3">
        <SearchField
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search the transcript…"
          aria-label="Search the transcript"
        />
        {query.trim() && (
          <span className="shrink-0 text-xs text-muted-foreground">
            {filtered.length} match{filtered.length === 1 ? '' : 'es'}
          </span>
        )}
      </div>

      <div className="mt-3">
        {filtered.length === 0 ? (
          <EmptyState
            icon={<FileQuestion className="h-5 w-5" />}
            title="No matching lines"
            description={`Nothing in the transcript mentions “${query.trim()}”.`}
            action={
              <SecondaryButton size="sm" onClick={() => setQuery('')}>
                Clear search
              </SecondaryButton>
            }
          />
        ) : (
          <TranscriptList segments={filtered} query={query} autoScroll={autoScroll} />
        )}
      </div>
    </section>
  )
}

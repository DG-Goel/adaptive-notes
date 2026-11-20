import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  ChevronDown,
  Film,
  GraduationCap,
  ListOrdered,
  MessageSquare,
  PlayCircle,
  Sparkles,
  Tags,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { VideoPlayer } from '@/components/video/VideoPlayer'
import { NotesGenerationStatus } from './NotesGenerationControls'
import { useVideoPlayer } from '@/context/video-player-context'
import { formatTime } from '@/lib/format'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { NoteDocument, NotesProcessingStatus } from '@/types/notes'
import type { VideoLecture } from '@/types/video'

/**
 * The Notes Studio's right-hand learning context.
 *
 * It holds the video reference, the chapter/timestamp navigation, the concepts
 * the document depends on, a route into the AI tutor, and the live generation
 * status. The video reference renders the *shared* player component inside the
 * studio's `VideoPlayerProvider`, so timestamp chips in the notes seek a real
 * player rather than a second, parallel implementation.
 */

interface CollapsibleGroupProps {
  title: string
  icon: ReactNode
  defaultOpen?: boolean
  action?: ReactNode
  children: ReactNode
}

function CollapsibleGroup({ title, icon, defaultOpen = true, action, children }: CollapsibleGroupProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="rounded-2xl border border-border bg-card shadow-soft">
      <div className="flex items-center gap-2 px-4 py-3">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          className="flex min-w-0 flex-1 items-center gap-2 rounded-md text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <span className="text-accent" aria-hidden>
            {icon}
          </span>
          <h2 className="min-w-0 flex-1 truncate text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {title}
          </h2>
          <ChevronDown
            className={cn('h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform', !open && '-rotate-90')}
            aria-hidden
          />
        </button>
        {action}
      </div>
      {open && <div className="border-t border-border px-4 py-3">{children}</div>}
    </section>
  )
}

export interface NotesContextPanelProps {
  lecture: VideoLecture
  document?: NoteDocument
  activeSectionId?: string
  onNavigateSection: (sectionId: string) => void
  status?: NotesProcessingStatus
  statusPending?: boolean
  statusError?: unknown
  className?: string
}

export function NotesContextPanel({
  lecture,
  document,
  activeSectionId,
  onNavigateSection,
  status,
  statusPending,
  statusError,
  className,
}: NotesContextPanelProps) {
  const { activeChapter, chapters, seekTo, isReady, duration } = useVideoPlayer()

  const sectionEntries = useMemo(
    () =>
      (document?.sections ?? []).map((section) => ({
        id: section.id,
        title: section.title,
        level: section.level,
        startSeconds: section.startSeconds,
      })),
    [document],
  )

  const activeSectionStart = sectionEntries.find((entry) => entry.id === activeSectionId)?.startSeconds
  const openAt = activeChapter?.startTime ?? activeSectionStart ?? sectionEntries[0]?.startSeconds ?? 0

  return (
    <aside className={cn('flex flex-col gap-3', className)} aria-label="Learning context">
      <CollapsibleGroup title="Video reference" icon={<Film className="h-3.5 w-3.5" />}>
        <div className="space-y-3">
          <VideoPlayer lecture={lecture} />

          <div className="space-y-1.5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Current chapter</p>
            <p className="text-[13px] font-medium text-foreground">
              {activeChapter ? activeChapter.title : 'Not started yet'}
            </p>
            <p className="font-mono text-[11px] tabular-nums text-muted-foreground">
              {isReady ? `${formatTime(duration)} available` : 'Loading media…'}
            </p>
          </div>

          <Link
            to={`/learn/${lecture.id}?t=${Math.max(0, Math.floor(openAt))}`}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-[13px] font-medium text-accent-foreground shadow-sm transition-colors hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <PlayCircle className="h-4 w-4" />
            Open at {timestampLabel(openAt)}
          </Link>

          <p className="text-[11px] leading-relaxed text-muted-foreground">
            The reference player is the same player used by the lecture workspace. Note timestamps seek it
            directly, and “Open at timestamp” deep-links into the full workspace.
          </p>
        </div>
      </CollapsibleGroup>

      <CollapsibleGroup title="Chapters" icon={<ListOrdered className="h-3.5 w-3.5" />} defaultOpen={false}>
        {chapters.length === 0 ? (
          <p className="text-xs text-muted-foreground">This lecture has no chapter markers.</p>
        ) : (
          <ul className="space-y-0.5">
            {chapters.map((chapter) => {
              const active = activeChapter?.id === chapter.id
              return (
                <li key={chapter.id}>
                  <div
                    className={cn(
                      'group flex items-center gap-2 rounded-lg px-1 py-1',
                      active ? 'bg-accent/[0.08]' : 'hover:bg-muted/70',
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => seekTo(chapter.startTime)}
                      disabled={!isReady}
                      className={cn(
                        'min-w-0 flex-1 rounded-md text-left text-[12.5px] leading-snug focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60',
                        active ? 'font-medium text-accent' : 'text-foreground/80',
                      )}
                    >
                      <span className="line-clamp-2">{chapter.title}</span>
                      <span className="mt-0.5 block font-mono text-[10px] tabular-nums text-muted-foreground">
                        {timestampLabel(chapter.startTime)}
                      </span>
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </CollapsibleGroup>

      <CollapsibleGroup title="Sections" icon={<GraduationCap className="h-3.5 w-3.5" />} defaultOpen={false}>
        {sectionEntries.length === 0 ? (
          <p className="text-xs text-muted-foreground">No sections in this document.</p>
        ) : (
          <ul className="space-y-0.5">
            {sectionEntries.map((entry) => (
              <li key={entry.id}>
                <button
                  type="button"
                  onClick={() => onNavigateSection(entry.id)}
                  aria-current={entry.id === activeSectionId ? 'true' : undefined}
                  className={cn(
                    'w-full rounded-md py-1 text-left text-[12.5px] leading-snug transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    entry.id === activeSectionId
                      ? 'font-medium text-accent'
                      : 'text-foreground/80 hover:text-foreground',
                  )}
                  style={{ paddingLeft: `${(entry.level - 1) * 0.6}rem` }}
                >
                  <span className="line-clamp-2">{entry.title}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleGroup>

      <CollapsibleGroup title="Related concepts" icon={<Tags className="h-3.5 w-3.5" />} defaultOpen={false}>
        {lecture.keyConcepts.length === 0 ? (
          <p className="text-xs text-muted-foreground">No key concepts were recorded for this lecture.</p>
        ) : (
          <ul className="flex flex-wrap gap-1.5">
            {lecture.keyConcepts.map((concept) => (
              <li key={concept}>
                <Badge variant="secondary" className="text-[10px] font-normal">
                  {concept}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleGroup>

      <CollapsibleGroup
        title="AI tutor"
        icon={<MessageSquare className="h-3.5 w-3.5" />}
        defaultOpen={false}
      >
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          Ask about anything in these notes. The tutor opens in its own workspace and stays grounded in this
          lecture.
        </p>
        <Link
          to="/tutor"
          className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-border px-3 py-2 text-[13px] font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Open AI tutor
        </Link>
      </CollapsibleGroup>

      <CollapsibleGroup title="Generation status" icon={<Sparkles className="h-3.5 w-3.5" />}>
        <NotesGenerationStatus status={status} isPending={statusPending} error={statusError} />
      </CollapsibleGroup>
    </aside>
  )
}

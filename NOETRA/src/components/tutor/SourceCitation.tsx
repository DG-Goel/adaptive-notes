import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, FileText, Film, ScrollText } from 'lucide-react'
import { useVideoPlayerOptional } from '@/context/video-player-context'
import { formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { TutorCitation, TutorCitationType } from '@/types/tutor'

const TYPE_ICON: Record<TutorCitationType, typeof Film> = {
  video: Film,
  transcript: ScrollText,
  notes: BookOpen,
  document: FileText,
}

export interface SourceCitationProps {
  citation: TutorCitation
  className?: string
}

/**
 * A single source citation chip.
 *
 * Timestamp citations seek the mounted video player when one is available,
 * otherwise deep-link to `/learn/:videoId?t=<seconds>`. Citations without a
 * usable timestamp are shown as informational chips with an excerpt preview.
 *
 * Citations are never invented: this component only renders metadata that was
 * actually returned by the backend (or present in the mock fixtures).
 */
export function SourceCitation({ citation, className }: SourceCitationProps) {
  const [open, setOpen] = useState(false)
  const player = useVideoPlayerOptional()
  const navigate = useNavigate()

  const seconds = citation.timestamp ?? citation.startSeconds
  const label = citation.label ?? citation.title ?? 'Source'
  const Icon = TYPE_ICON[citation.type]

  const hasTimestamp = typeof seconds === 'number' && Number.isFinite(seconds)
  const hasVideoId = Boolean(citation.videoId)
  const actionable = hasTimestamp && (Boolean(player?.seekTo) || hasVideoId)

  const handleClick = () => {
    if (!hasTimestamp) return
    if (player?.seekTo) {
      player.seekTo(seconds!)
      return
    }
    if (citation.videoId) {
      navigate(`/learn/${citation.videoId}?t=${Math.max(0, Math.floor(seconds!))}`)
    }
  }

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={handleClick}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        disabled={!actionable}
        title={
          actionable
            ? `Open ${label}${hasTimestamp ? ` at ${formatTime(seconds!)}` : ''}`
            : `${label} — no timestamp available`
        }
        className={cn(
          'inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-muted-foreground transition-colors',
          actionable && 'hover:border-accent/40 hover:text-accent',
          !actionable && 'cursor-default opacity-70',
          className,
        )}
      >
        <Icon className="h-3 w-3" />
        <span className="max-w-[10rem] truncate">{label}</span>
        {hasTimestamp && (
          <span className="font-mono tabular-nums">{formatTime(seconds!)}</span>
        )}
      </button>

      {open && citation.excerpt && (
        <div className="absolute bottom-full left-0 z-20 mb-2 w-72 rounded-lg border border-border bg-popover p-3 text-xs text-popover-foreground shadow-lg">
          <p className="mb-1 font-semibold text-foreground">{label}</p>
          <p className="line-clamp-4 text-muted-foreground">{citation.excerpt}</p>
        </div>
      )}
    </span>
  )
}

export interface SourceCitationListProps {
  citations: TutorCitation[]
  className?: string
}

export function SourceCitationList({ citations, className }: SourceCitationListProps) {
  if (!citations.length) return null
  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)}>
      {citations.map((citation) => (
        <SourceCitation key={citation.id} citation={citation} />
      ))}
    </div>
  )
}

import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { parseTimestamp } from '@/lib/timestamps'
import { useNotesPlaybackTarget } from '@/context/notes-playback-context'
import { useVideoPlayerOptional } from '@/context/video-player-context'

const TIMESTAMP_PATTERN = /\[(?:\d{1,2}:)?\d{1,2}:\d{2}\]/g

const CHIP_CLASSES =
  'mx-0.5 inline-flex items-center rounded-md border border-accent/25 bg-accent/[0.07] px-1.5 py-px font-mono text-[0.85em] tabular-nums text-accent transition-colors'

export interface TimestampChipProps {
  seconds: number
  label: string
  className?: string
}

/**
 * A clickable `[mm:ss]` marker.
 *
 * Inside the video workspace it seeks the shared player. On a standalone notes
 * route — where no player is mounted — it deep-links to `/learn/:videoId?t=…`
 * so the lecture opens at the right moment instead of silently doing nothing.
 */
export function TimestampChip({ seconds, label, className }: TimestampChipProps) {
  const target = useNotesPlaybackTarget()
  const player = useVideoPlayerOptional()
  const navigate = useNavigate()

  const seekTo = target?.seekTo ?? player?.seekTo
  const videoId = target?.videoId
  const actionable = Boolean(seekTo) || Boolean(videoId)

  if (!actionable) {
    return <span className={cn(CHIP_CLASSES, 'border-border text-muted-foreground', className)}>{label}</span>
  }

  const openLecture = Boolean(seekTo)

  return (
    <button
      type="button"
      onClick={() => {
        if (seekTo) {
          seekTo(seconds)
          return
        }
        if (videoId) navigate(`/learn/${videoId}?t=${Math.max(0, Math.floor(seconds))}`)
      }}
      title={openLecture ? `Jump to ${label}` : `Open the lecture at ${label}`}
      className={cn(CHIP_CLASSES, 'hover:bg-accent/15', className)}
    >
      {label}
    </button>
  )
}

export interface TimestampTextProps {
  text: string
  className?: string
}

/** Render prose with any `[mm:ss]` markers turned into seekable chips. */
export function TimestampText({ text, className }: TimestampTextProps) {
  const pattern = new RegExp(TIMESTAMP_PATTERN.source, 'g')
  const parts: ReactNode[] = []
  let cursor = 0
  let match = pattern.exec(text)

  while (match) {
    if (match.index > cursor) parts.push(text.slice(cursor, match.index))
    const token = match[0]
    const seconds = parseTimestamp(token)
    if (seconds === null) {
      parts.push(token)
    } else {
      parts.push(<TimestampChip key={match.index} seconds={seconds} label={token.slice(1, -1)} />)
    }
    cursor = match.index + token.length
    match = pattern.exec(text)
  }

  if (cursor < text.length) parts.push(text.slice(cursor))

  return <span className={className}>{parts.length > 0 ? parts : text}</span>
}

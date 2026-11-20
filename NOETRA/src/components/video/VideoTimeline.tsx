import { useMemo, useRef, useState } from 'react'
import type { PointerEvent as ReactPointerEvent } from 'react'
import { cn } from '@/lib/utils'
import { formatTime } from '@/lib/format'
import { findChapterIndex } from '@/lib/chapters'
import { useVideoPlayer, useVideoTime } from '@/context/video-player-context'

export interface VideoTimelineProps {
  className?: string
}

const clampFraction = (value: number) => Math.min(Math.max(value, 0), 1)

/**
 * Custom playback timeline.
 *
 * Renders buffered progress, playhead position, chapter markers, and a hover
 * timestamp preview. A transparent native range input sits on top so the
 * control is draggable and keyboard-accessible for free.
 */
export function VideoTimeline({ className }: VideoTimelineProps) {
  const { duration, chapters, isIllustrative, seekTo, getBufferedFraction } = useVideoPlayer()
  const currentTime = useVideoTime()
  const trackRef = useRef<HTMLDivElement>(null)
  const [hoverFraction, setHoverFraction] = useState<number | null>(null)

  const seekableDuration = duration > 0 ? duration : 0
  const max = seekableDuration > 0 ? seekableDuration : 1
  const progress = seekableDuration > 0 ? clampFraction(currentTime / seekableDuration) : 0
  const buffered = clampFraction(getBufferedFraction())

  const markers = useMemo(() => {
    // An illustrative clip is shorter than the lecture, so chapter positions
    // would collapse onto the end of the track — omit them entirely.
    if (seekableDuration <= 0 || isIllustrative) return []
    return chapters
      .filter((chapter) => chapter.startTime > 0)
      .map((chapter) => ({
        id: chapter.id,
        title: chapter.title,
        offset: clampFraction(chapter.startTime / seekableDuration),
      }))
  }, [chapters, seekableDuration, isIllustrative])

  const hoverTime = hoverFraction === null ? null : hoverFraction * seekableDuration
  const hoverChapter =
    hoverTime === null || isIllustrative ? null : chapters[findChapterIndex(hoverTime, chapters)] ?? null

  const updateHover = (event: ReactPointerEvent<HTMLDivElement>) => {
    const rect = trackRef.current?.getBoundingClientRect()
    if (!rect || rect.width === 0) return
    setHoverFraction(clampFraction((event.clientX - rect.left) / rect.width))
  }

  return (
    <div
      className={cn('group/timeline relative', className)}
      onPointerMove={updateHover}
      onPointerLeave={() => setHoverFraction(null)}
    >
      {hoverTime !== null && !Number.isNaN(hoverTime) && (
        <div
          className="pointer-events-none absolute bottom-full z-20 mb-3 -translate-x-1/2 rounded-lg border border-border bg-card px-2.5 py-1.5 text-center shadow-elevated"
          style={{ left: `${(hoverFraction ?? 0) * 100}%` }}
        >
          <p className="font-mono text-xs font-medium tabular-nums text-foreground">
            {formatTime(hoverTime)}
          </p>
          {hoverChapter && (
            <p className="mt-0.5 max-w-[180px] truncate text-[10px] text-muted-foreground">
              {hoverChapter.title}
            </p>
          )}
        </div>
      )}

      <div
        ref={trackRef}
        className="relative h-1.5 w-full rounded-full bg-muted-foreground/20 transition-[height] duration-150 group-hover/timeline:h-2.5"
      >
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-muted-foreground/30"
          style={{ width: `${buffered * 100}%` }}
        />

        <div
          className="absolute inset-y-0 left-0 rounded-full bg-accent"
          style={{ width: `${progress * 100}%` }}
        />

        {markers.map((marker) => (
          <span
            key={marker.id}
            title={marker.title}
            className="absolute inset-y-0 w-px bg-background/80"
            style={{ left: `${marker.offset * 100}%` }}
          />
        ))}

        {hoverFraction !== null && (
          <span
            className="absolute inset-y-0 w-px bg-foreground/40"
            style={{ left: `${hoverFraction * 100}%` }}
          />
        )}

        <span
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent bg-background opacity-0 transition-opacity duration-150 group-hover/timeline:opacity-100"
          style={{ left: `${progress * 100}%` }}
        />

        <input
          type="range"
          min={0}
          max={max}
          step={0.1}
          value={Math.min(currentTime, max)}
          disabled={seekableDuration === 0}
          onChange={(event) => seekTo(Number(event.target.value))}
          aria-label="Seek through the lecture"
          aria-valuetext={`${formatTime(currentTime)} of ${formatTime(seekableDuration)}`}
          className="absolute inset-x-0 -inset-y-2 h-[calc(100%+16px)] w-full cursor-pointer appearance-none bg-transparent opacity-0 disabled:cursor-not-allowed"
        />
      </div>
    </div>
  )
}

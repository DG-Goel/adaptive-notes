import { useMemo, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { ChevronDown, ListVideo } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatTime } from '@/lib/format'
import { getChapterProgress } from '@/lib/chapters'
import { useVideoPlayer, useVideoTime } from '@/context/video-player-context'

export interface ChapterNavigationProps {
  defaultOpen?: boolean
  className?: string
}

/**
 * Chapter navigation.
 *
 * A compact proportional timeline gives a quick overview of the whole lecture,
 * and the expanded list offers per-chapter progress. Both seek on click and
 * read the shared controller, so they never restart the player.
 */
export function ChapterNavigation({ defaultOpen = true, className }: ChapterNavigationProps) {
  const { chapters, activeChapter, duration, isIllustrative, seekTo } = useVideoPlayer()
  const currentTime = useVideoTime()
  const reduceMotion = useReducedMotion()
  const [open, setOpen] = useState(defaultOpen)

  const segments = useMemo(
    () =>
      chapters.map((chapter, index) => {
        const next = chapters[index + 1]
        const end = chapter.endTime ?? next?.startTime ?? duration
        return { chapter, span: Math.max(end - chapter.startTime, 1) }
      }),
    [chapters, duration],
  )

  if (chapters.length === 0) return null

  return (
    <section className={cn('rounded-2xl border border-border bg-card p-4 shadow-soft', className)}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ListVideo className="h-4 w-4 text-accent" />
          <h2 className="font-serif text-lg font-medium tracking-tight text-foreground">Chapters</h2>
          <span className="text-xs text-muted-foreground">{chapters.length}</span>
          {isIllustrative && (
            <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-600">
              Illustrative
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {open ? 'Hide list' : 'Show list'}
          <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
        </button>
      </div>

      {isIllustrative && (
        <p className="mt-2 rounded-lg bg-amber-500/[0.08] px-2.5 py-1.5 text-[11px] leading-relaxed text-amber-600">
          These chapters describe the lecture “Understanding Transformers”. The sample clip in the
          player is shorter and unrelated, so it is a playback demonstration only.
        </p>
      )}

      {/* Compact proportional timeline */}
      <div className="mt-3 flex gap-1">
        {segments.map(({ chapter, span }, index) => {
          const next = chapters[index + 1]
          const progress = getChapterProgress(
            currentTime,
            chapter,
            next?.startTime ?? chapter.endTime ?? duration,
          )
          const isActive = activeChapter?.id === chapter.id
          return (
            <button
              key={chapter.id}
              type="button"
              onClick={() => seekTo(chapter.startTime)}
              title={`${index + 1}. ${chapter.title} — ${formatTime(chapter.startTime)}`}
              aria-label={`Jump to chapter ${index + 1}: ${chapter.title}`}
              aria-current={isActive ? 'true' : undefined}
              className={cn(
                'group/segment h-1.5 overflow-hidden rounded-full bg-muted transition-all duration-200 hover:h-2.5',
                isActive && 'h-2.5',
              )}
              style={{ flexGrow: span, flexBasis: 0 }}
            >
              <span
                className={cn(
                  'block h-full rounded-full transition-[width] duration-200',
                  isActive ? 'bg-accent' : 'bg-muted-foreground/35 group-hover/segment:bg-muted-foreground/50',
                )}
                style={{ width: `${progress * 100}%` }}
              />
            </button>
          )
        })}
      </div>

      {open && (
        <ol className="mt-3 space-y-1">
          {segments.map(({ chapter }, index) => {
            const next = chapters[index + 1]
            const end = next?.startTime ?? chapter.endTime ?? duration
            const progress = getChapterProgress(currentTime, chapter, end)
            const isActive = activeChapter?.id === chapter.id
            return (
              <li key={chapter.id} className="relative">
                <button
                  type="button"
                  onClick={() => seekTo(chapter.startTime)}
                  aria-current={isActive ? 'true' : undefined}
                  className={cn(
                    'group/row flex w-full items-start gap-3 rounded-xl p-3 text-left transition-colors',
                    isActive ? 'bg-accent/[0.06]' : 'hover:bg-muted/60',
                  )}
                >
                  {isActive && (
                    <motion.span
                      layoutId={reduceMotion ? undefined : 'active-chapter-bar'}
                      className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent"
                      initial={reduceMotion ? false : { opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.2 }}
                    />
                  )}

                  <span
                    className={cn(
                      'mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-semibold tabular-nums transition-colors',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'bg-muted text-muted-foreground group-hover/row:text-foreground',
                    )}
                  >
                    {index + 1}
                  </span>

                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span
                        className={cn(
                          'truncate text-sm font-medium',
                          isActive ? 'text-foreground' : 'text-foreground/85',
                        )}
                      >
                        {chapter.title}
                      </span>
                      <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">
                        {formatTime(chapter.startTime)}
                      </span>
                    </span>

                    {chapter.summary && (
                      <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                        {chapter.summary}
                      </span>
                    )}

                    <span className="mt-2 block h-1 w-full overflow-hidden rounded-full bg-muted">
                      <span
                        className={cn(
                          'block h-full rounded-full transition-[width] duration-200',
                          isActive ? 'bg-accent' : 'bg-muted-foreground/35',
                        )}
                        style={{ width: `${progress * 100}%` }}
                      />
                    </span>

                    <span className="mt-1 block font-mono text-[10px] text-muted-foreground/70">
                      {formatTime(end - chapter.startTime)} long
                    </span>
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}

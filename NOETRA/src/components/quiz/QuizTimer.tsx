import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface QuizTimerProps {
  startTime: Date
  timeLimit?: number // seconds
  onTimeUp?: () => void
  className?: string
}

/**
 * Quiz elapsed time or countdown timer.
 *
 * Shows elapsed time by default. If timeLimit is provided, counts down
 * and calls onTimeUp when time expires.
 */
export function QuizTimer({ startTime, timeLimit, onTimeUp, className }: QuizTimerProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const elapsedSeconds = Math.floor((now - startTime.getTime()) / 1000)
      setElapsed(elapsedSeconds)

      if (timeLimit && elapsedSeconds >= timeLimit) {
        clearInterval(interval)
        onTimeUp?.()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime, timeLimit, onTimeUp])

  const displaySeconds = timeLimit ? Math.max(0, timeLimit - elapsed) : elapsed
  const minutes = Math.floor(displaySeconds / 60)
  const seconds = displaySeconds % 60

  const isWarning = timeLimit && elapsed >= timeLimit * 0.8
  const isCritical = timeLimit && elapsed >= timeLimit * 0.95

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium tabular-nums',
        isCritical
          ? 'border-red-500 bg-red-50 text-red-700'
          : isWarning
            ? 'border-amber-500 bg-amber-50 text-amber-700'
            : 'border-border bg-background text-foreground',
        className,
      )}
    >
      <Clock className="h-3.5 w-3.5" />
      <span>
        {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
      </span>
      {timeLimit && <span className="text-muted-foreground">/ {Math.floor(timeLimit / 60)}:00</span>}
    </div>
  )
}

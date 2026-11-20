import { useState } from 'react'
import { Calendar, Clock, Eye, RotateCcw, Search, Trophy } from 'lucide-react'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { QuizAttemptSummary } from '@/types/quiz'

export interface QuizHistoryProps {
  attempts: QuizAttemptSummary[]
  onViewResults?: (attemptId: string) => void
  onRetake?: (quizId: string) => void
  className?: string
}

/**
 * Quiz attempt history list.
 *
 * Shows past quiz attempts with scores, times, and actions.
 * Supports filtering and sorting.
 */
export function QuizHistory({
  attempts,
  onViewResults,
  onRetake,
  className,
}: QuizHistoryProps) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'score'>('date')

  const filtered = attempts.filter((attempt) =>
    attempt.videoTitle?.toLowerCase().includes(search.toLowerCase()),
  )

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'date') {
      return new Date(b.attemptedAt).getTime() - new Date(a.attemptedAt).getTime()
    }
    return (b.percentage ?? 0) - (a.percentage ?? 0)
  })

  const getScoreColor = (percentage?: number) => {
    if (!percentage) return 'text-muted-foreground'
    if (percentage >= 90) return 'text-green-600'
    if (percentage >= 70) return 'text-blue-600'
    if (percentage >= 50) return 'text-amber-600'
    return 'text-red-600'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(date)
  }

  const formatTime = (seconds?: number) => {
    if (!seconds) return '—'
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}:${String(secs).padStart(2, '0')}`
  }

  if (attempts.length === 0) {
    return (
      <div className={cn('rounded-2xl border border-dashed border-border bg-muted/30 p-12 text-center', className)}>
        <Trophy className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 font-serif text-lg font-medium text-foreground">No quiz attempts yet</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Complete your first quiz to see your history here
        </p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search and sort */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 sm:max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by lecture title..."
            className="w-full rounded-lg border border-input bg-background py-2 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-accent/50 focus-visible:ring-2 focus-visible:ring-ring/30"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Sort by:</span>
          <div className="flex rounded-lg border border-border p-0.5" role="group">
            <button
              type="button"
              onClick={() => setSortBy('date')}
              className={cn(
                'rounded-md px-3 py-1 text-sm font-medium transition-colors',
                sortBy === 'date'
                  ? 'bg-accent/10 text-accent'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              Date
            </button>
            <button
              type="button"
              onClick={() => setSortBy('score')}
              className={cn(
                'rounded-md px-3 py-1 text-sm font-medium transition-colors',
                sortBy === 'score'
                  ? 'bg-accent/10 text-accent'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              Score
            </button>
          </div>
        </div>
      </div>

      {/* Attempt list */}
      <div className="space-y-3">
        {sorted.map((attempt) => (
          <div
            key={attempt.id}
            className="flex items-start gap-4 rounded-xl border border-border bg-card p-4 shadow-soft transition-shadow hover:shadow-md"
          >
            {/* Score badge */}
            <div className="flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-lg border border-border bg-background">
              {attempt.completed && attempt.percentage !== undefined ? (
                <>
                  <p className={cn('text-xl font-medium', getScoreColor(attempt.percentage))}>
                    {attempt.percentage}
                  </p>
                  <p className="text-[10px] text-muted-foreground">SCORE</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-medium text-muted-foreground">—</p>
                  <p className="text-[10px] text-muted-foreground">INCOMPLETE</p>
                </>
              )}
            </div>

            {/* Details */}
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h3 className="font-medium text-foreground">
                  {attempt.videoTitle ?? 'Untitled Quiz'}
                </h3>
                {attempt.isDemo && (
                  <Badge variant="outline" className="text-[10px]">
                    Demo
                  </Badge>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(attempt.attemptedAt)}
                </span>
                <span>{attempt.questionCount} questions</span>
                <span className="capitalize">{attempt.difficulty}</span>
                <span className="capitalize">{attempt.mode}</span>
                {attempt.timeSpent !== undefined && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTime(attempt.timeSpent)}
                  </span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex shrink-0 items-center gap-2">
              {attempt.completed && onViewResults && (
                <SecondaryButton size="sm" onClick={() => onViewResults(attempt.id)}>
                  <Eye className="h-3 w-3" />
                  <span className="hidden sm:inline">View</span>
                </SecondaryButton>
              )}
              {onRetake && (
                <SecondaryButton size="sm" onClick={() => onRetake(attempt.quizId)}>
                  <RotateCcw className="h-3 w-3" />
                  <span className="hidden sm:inline">Retake</span>
                </SecondaryButton>
              )}
            </div>
          </div>
        ))}
      </div>

      {sorted.length === 0 && search && (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center">
          <p className="text-sm text-muted-foreground">No attempts found matching "{search}"</p>
        </div>
      )}
    </div>
  )
}

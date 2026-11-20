import { Flag } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface QuizProgressProps {
  currentQuestion: number
  answeredQuestions: Set<string>
  markedForReview: Set<string>
  questionIds: string[]
  onNavigateToQuestion: (index: number) => void
  className?: string
}

/**
 * Visual quiz progress grid.
 *
 * Shows all question numbers with state indicators (answered, current, marked).
 * Allows jumping to any question.
 */
export function QuizProgress({
  currentQuestion,
  answeredQuestions,
  markedForReview,
  questionIds,
  onNavigateToQuestion,
  className,
}: QuizProgressProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <p className="text-sm font-medium text-foreground">Questions</p>
      <div className="grid grid-cols-5 gap-2 sm:grid-cols-7 md:grid-cols-10">
        {questionIds.map((id, index) => {
          const questionNumber = index + 1
          const isCurrent = questionNumber === currentQuestion
          const isAnswered = answeredQuestions.has(id)
          const isMarked = markedForReview.has(id)

          return (
            <button
              key={id}
              type="button"
              onClick={() => onNavigateToQuestion(index + 1)}
              className={cn(
                'relative flex aspect-square items-center justify-center rounded-lg border text-sm font-medium transition-all',
                isCurrent &&
                  'border-accent bg-accent text-accent-foreground ring-2 ring-accent/20',
                !isCurrent && isAnswered && 'border-green-500 bg-green-50 text-green-700',
                !isCurrent && !isAnswered && 'border-border bg-background text-foreground hover:border-accent/40 hover:bg-muted',
              )}
              aria-label={`Question ${questionNumber}${isCurrent ? ' (current)' : ''}${isAnswered ? ' (answered)' : ''}${isMarked ? ' (marked for review)' : ''}`}
            >
              {questionNumber}
              {isMarked && (
                <Flag className="absolute -right-1 -top-1 h-3 w-3 text-accent" fill="currentColor" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

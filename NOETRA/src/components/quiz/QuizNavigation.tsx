import { ChevronLeft, ChevronRight, Flag, Send } from 'lucide-react'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { cn } from '@/lib/utils'

export interface QuizNavigationProps {
  currentQuestion: number
  totalQuestions: number
  answeredCount: number
  markedForReviewCount: number
  canGoBack: boolean
  canGoNext: boolean
  onPrevious: () => void
  onNext: () => void
  onSubmit: () => void
  onToggleReview: () => void
  isMarkedForReview: boolean
  disabled?: boolean
  className?: string
}

/**
 * Quiz navigation controls.
 *
 * Provides previous/next buttons, submit action, and mark-for-review toggle.
 * Shows progress and prevents accidental submission.
 */
export function QuizNavigation({
  currentQuestion,
  totalQuestions,
  answeredCount,
  markedForReviewCount,
  canGoBack,
  canGoNext,
  onPrevious,
  onNext,
  onSubmit,
  onToggleReview,
  isMarkedForReview,
  disabled = false,
  className,
}: QuizNavigationProps) {
  const unansweredCount = totalQuestions - answeredCount
  const isLastQuestion = currentQuestion === totalQuestions

  return (
    <div className={cn('space-y-4', className)}>
      {/* Progress summary */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground">
            <span className="font-medium text-foreground">{answeredCount}</span> answered
          </span>
          {unansweredCount > 0 && (
            <span className="text-muted-foreground">
              <span className="font-medium text-amber-600">{unansweredCount}</span> remaining
            </span>
          )}
          {markedForReviewCount > 0 && (
            <span className="text-muted-foreground">
              <span className="font-medium text-accent">{markedForReviewCount}</span> marked
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggleReview}
          disabled={disabled}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
            isMarkedForReview
              ? 'bg-accent/10 text-accent hover:bg-accent/20'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground',
          )}
        >
          <Flag className="h-3 w-3" />
          {isMarkedForReview ? 'Marked' : 'Mark for review'}
        </button>
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center gap-3">
        <SecondaryButton
          onClick={onPrevious}
          disabled={!canGoBack || disabled}
          size="lg"
          className="flex-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </SecondaryButton>

        {isLastQuestion ? (
          <PrimaryButton
            onClick={onSubmit}
            disabled={disabled}
            size="lg"
            className="flex-1"
          >
            <Send className="h-4 w-4" />
            Submit Quiz
          </PrimaryButton>
        ) : (
          <PrimaryButton
            onClick={onNext}
            disabled={!canGoNext || disabled}
            size="lg"
            className="flex-1"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </PrimaryButton>
        )}
      </div>
    </div>
  )
}

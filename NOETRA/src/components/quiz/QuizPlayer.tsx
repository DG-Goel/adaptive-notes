import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'
import { QuizQuestion } from './QuizQuestion'
import { QuizNavigation } from './QuizNavigation'
import { QuizProgress } from './QuizProgress'
import { QuizTimer } from './QuizTimer'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { cn } from '@/lib/utils'
import type { Quiz, QuizAttempt } from '@/types/quiz'

export interface QuizPlayerProps {
  quiz: Quiz
  attempt: QuizAttempt
  onUpdateAnswer: (questionId: string, optionIds: string[]) => void
  onToggleReview: (questionId: string) => void
  onSubmit: () => void
  onExit?: () => void
  className?: string
}

/**
 * Interactive quiz player.
 *
 * Handles question navigation, answer selection, timer, progress tracking,
 * and submission. Supports practice and exam modes.
 */
export function QuizPlayer({
  quiz,
  attempt,
  onUpdateAnswer,
  onToggleReview,
  onSubmit,
  onExit,
  className,
}: QuizPlayerProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false)

  const questions = quiz.questions
  const currentQuestion = questions[currentQuestionIndex]!
  const questionIds = questions.map((q) => q.id)

  const selectedAnswers = attempt.answers[currentQuestion.id] ?? []
  const answeredQuestions = new Set(
    Object.entries(attempt.answers)
      .filter(([, answers]) => answers.length > 0)
      .map(([id]) => id),
  )

  const answeredCount = answeredQuestions.size
  const unansweredCount = questions.length - answeredCount

  const handlePrevious = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }, [currentQuestionIndex])

  const handleNext = useCallback(() => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }, [currentQuestionIndex, questions.length])

  const handleSubmit = () => {
    if (unansweredCount > 0) {
      setSubmitDialogOpen(true)
    } else {
      onSubmit()
    }
  }

  const handleConfirmSubmit = () => {
    setSubmitDialogOpen(false)
    onSubmit()
  }

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle when not in an input
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return
      }

      if (event.key === 'ArrowLeft') {
        event.preventDefault()
        handlePrevious()
      } else if (event.key === 'ArrowRight') {
        event.preventDefault()
        handleNext()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentQuestionIndex, questions.length, handlePrevious, handleNext])

  return (
    <div className={cn('flex min-h-screen flex-col', className)}>
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/90">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="min-w-0 flex-1">
            <h1 className="truncate font-serif text-lg font-medium text-foreground">
              {quiz.title}
            </h1>
            <p className="truncate text-xs text-muted-foreground">
              {quiz.config.mode === 'exam' ? 'Exam Mode' : 'Practice Mode'}
              {quiz.isDemo && ' · Demo Quiz'}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            {quiz.config.timed && (
              <QuizTimer
                startTime={new Date(attempt.startedAt)}
                timeLimit={quiz.config.timeLimit}
                onTimeUp={handleSubmit}
              />
            )}

            {onExit && (
              <button
                type="button"
                onClick={onExit}
                aria-label="Exit quiz"
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex flex-1">
        {/* Main question area */}
        <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <QuizQuestion
              question={currentQuestion}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={questions.length}
              selectedAnswers={selectedAnswers}
              onAnswerSelect={(optionIds) => onUpdateAnswer(currentQuestion.id, optionIds)}
              showCorrectness={false}
            />
          </div>
        </div>

        {/* Sidebar with progress (desktop) */}
        <aside className="hidden w-80 shrink-0 border-l border-border bg-muted/30 p-6 lg:block">
          <div className="space-y-6">
            <QuizProgress
              currentQuestion={currentQuestionIndex + 1}
              answeredQuestions={answeredQuestions}
              markedForReview={attempt.markedForReview}
              questionIds={questionIds}
              onNavigateToQuestion={(num) => setCurrentQuestionIndex(num - 1)}
            />
          </div>
        </aside>
      </div>

      {/* Footer navigation */}
      <footer className="sticky bottom-0 z-20 border-t border-border bg-background/95 px-4 py-4 backdrop-blur supports-[backdrop-filter]:bg-background/90 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <QuizNavigation
            currentQuestion={currentQuestionIndex + 1}
            totalQuestions={questions.length}
            answeredCount={answeredCount}
            markedForReviewCount={attempt.markedForReview.size}
            canGoBack={currentQuestionIndex > 0}
            canGoNext={currentQuestionIndex < questions.length - 1}
            onPrevious={handlePrevious}
            onNext={handleNext}
            onSubmit={handleSubmit}
            onToggleReview={() => onToggleReview(currentQuestion.id)}
            isMarkedForReview={attempt.markedForReview.has(currentQuestion.id)}
          />
        </div>
      </footer>

      {/* Submit confirmation dialog */}
      <Dialog open={submitDialogOpen} onOpenChange={setSubmitDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogTitle className="font-serif text-xl font-medium">Submit Quiz?</DialogTitle>
          <div className="space-y-4 py-4">
            {unansweredCount > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <p className="text-sm text-amber-900">
                  You have <strong>{unansweredCount}</strong> unanswered{' '}
                  {unansweredCount === 1 ? 'question' : 'questions'}.
                </p>
              </div>
            )}
            <p className="text-sm text-muted-foreground">
              Once submitted, you won't be able to change your answers.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <SecondaryButton onClick={() => setSubmitDialogOpen(false)} className="flex-1">
              Continue Quiz
            </SecondaryButton>
            <PrimaryButton onClick={handleConfirmSubmit} className="flex-1">
              Submit Anyway
            </PrimaryButton>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

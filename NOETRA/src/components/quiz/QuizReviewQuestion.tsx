import { useNavigate } from 'react-router-dom'
import { Check, X, BookOpen } from 'lucide-react'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { TimestampChip } from '@/components/video/TimestampText'
import { cn } from '@/lib/utils'
import type { QuestionResult } from '@/types/quiz'

export interface QuizReviewQuestionProps {
  questionResult: QuestionResult
  questionNumber: number
  className?: string
}

/**
 * Single question review with correctness, explanation, and source links.
 *
 * Shows user's answers, correct answers, explanation, and provides navigation
 * to relevant video timestamps and notes.
 */
export function QuizReviewQuestion({
  questionResult,
  questionNumber,
  className,
}: QuizReviewQuestionProps) {
  const navigate = useNavigate()
  const { question, userAnswers, correctAnswers, isCorrect, explanation } = questionResult

  const getOptionState = (optionId: string): 'correct' | 'incorrect' | 'neutral' => {
    const isUserAnswer = userAnswers.includes(optionId)
    const isCorrectAnswer = correctAnswers.includes(optionId)

    if (isUserAnswer && isCorrectAnswer) return 'correct'
    if (isUserAnswer && !isCorrectAnswer) return 'incorrect'
    if (!isUserAnswer && isCorrectAnswer) return 'correct'
    return 'neutral'
  }

  return (
    <div className={cn('rounded-xl border border-border bg-background p-5', className)}>
      {/* Question header */}
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">
              Question {questionNumber}
            </span>
            {question.difficulty && (
              <span
                className={cn(
                  'rounded-full border px-2 py-0.5 text-xs font-medium',
                  question.difficulty === 'easy' && 'border-green-200 bg-green-50 text-green-700',
                  question.difficulty === 'medium' && 'border-amber-200 bg-amber-50 text-amber-700',
                  question.difficulty === 'hard' && 'border-red-200 bg-red-50 text-red-700',
                )}
              >
                {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
              </span>
            )}
          </div>
          <p className="text-base font-medium leading-relaxed text-foreground">
            {question.question}
          </p>
        </div>
        <div
          className={cn(
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-full',
            isCorrect ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600',
          )}
        >
          {isCorrect ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
        </div>
      </div>

      {/* Options with correctness indicators */}
      <div className="mb-4 space-y-2">
        {question.options.map((option) => {
          const state = getOptionState(option.id)
          const isUserAnswer = userAnswers.includes(option.id)
          const isCorrectAnswer = correctAnswers.includes(option.id)

          return (
            <div
              key={option.id}
              className={cn(
                'flex items-center gap-3 rounded-lg border p-3',
                state === 'correct' && 'border-green-200 bg-green-50',
                state === 'incorrect' && 'border-red-200 bg-red-50',
                state === 'neutral' && 'border-border bg-background',
              )}
            >
              <span
                className={cn(
                  'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2',
                  state === 'correct' && 'border-green-600 bg-green-600',
                  state === 'incorrect' && 'border-red-600 bg-red-600',
                  state === 'neutral' && 'border-muted-foreground',
                )}
              >
                {(isUserAnswer || isCorrectAnswer) && (
                  <Check className="h-3 w-3 text-white" />
                )}
              </span>
              <span
                className={cn(
                  'flex-1 text-sm',
                  state === 'correct' && 'font-medium text-green-900',
                  state === 'incorrect' && 'font-medium text-red-900',
                  state === 'neutral' && 'text-muted-foreground',
                )}
              >
                {option.text}
              </span>
              {isUserAnswer && !isCorrectAnswer && (
                <span className="text-xs text-red-600">Your answer</span>
              )}
              {!isUserAnswer && isCorrectAnswer && (
                <span className="text-xs text-green-600">Correct answer</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Explanation */}
      {explanation && (
        <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3">
          <p className="mb-1 text-xs font-medium uppercase tracking-wider text-blue-900">
            Explanation
          </p>
          <p className="text-sm leading-relaxed text-blue-800">{explanation}</p>
        </div>
      )}

      {/* Source links */}
      {question.source && (
        <div className="flex flex-wrap items-center gap-2">
          {question.source?.timestampSeconds !== undefined && question.source.videoId && (
            <TimestampChip
              seconds={question.source.timestampSeconds}
              label="Watch explanation"
            />
          )}
          {question.source?.noteSectionId && question.source.videoId && (
            <SecondaryButton
              size="sm"
              onClick={() => navigate(`/notes/${question.source!.videoId}`)}
            >
              <BookOpen className="h-3 w-3" />
              Related notes
            </SecondaryButton>
          )}
        </div>
      )}
    </div>
  )
}

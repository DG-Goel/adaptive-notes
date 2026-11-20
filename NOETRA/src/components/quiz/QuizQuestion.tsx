import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { QuizQuestion as QuizQuestionType, QuestionOption } from '@/types/quiz'

export interface QuizQuestionProps {
  question: QuizQuestionType
  questionNumber: number
  totalQuestions: number
  selectedAnswers: string[]
  onAnswerSelect: (optionIds: string[]) => void
  showCorrectness?: boolean
  disabled?: boolean
  className?: string
}

/**
 * A single quiz question with interactive answer options.
 *
 * Supports single-select, multi-select, and true/false questions.
 * Preserves selected answers when navigating between questions.
 */
export function QuizQuestion({
  question,
  questionNumber,
  totalQuestions,
  selectedAnswers,
  onAnswerSelect,
  showCorrectness = false,
  disabled = false,
  className,
}: QuizQuestionProps) {
  const isSingleSelect = question.type === 'single_select' || question.type === 'true_false'

  const handleOptionClick = (optionId: string) => {
    if (disabled) return

    if (isSingleSelect) {
      onAnswerSelect([optionId])
    } else {
      // Multi-select
      if (selectedAnswers.includes(optionId)) {
        onAnswerSelect(selectedAnswers.filter((id) => id !== optionId))
      } else {
        onAnswerSelect([...selectedAnswers, optionId])
      }
    }
  }

  const getOptionState = (option: QuestionOption): 'correct' | 'incorrect' | 'selected' | 'default' => {
    const isSelected = selectedAnswers.includes(option.id)
    if (!showCorrectness) {
      return isSelected ? 'selected' : 'default'
    }

    const isCorrect = question.correctAnswers?.includes(option.id)
    if (isSelected && isCorrect) return 'correct'
    if (isSelected && !isCorrect) return 'incorrect'
    if (!isSelected && isCorrect) return 'correct' // Show what should have been selected
    return 'default'
  }

  return (
    <div className={cn('space-y-5', className)}>
      {/* Question header */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">
            Question {questionNumber} of {totalQuestions}
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
        <h3 className="font-serif text-xl font-medium leading-relaxed text-foreground">
          {question.question}
        </h3>
        {question.type === 'multi_select' && (
          <p className="mt-2 text-sm text-muted-foreground">Select all that apply</p>
        )}
      </div>

      {/* Answer options */}
      <div className="space-y-3">
        {question.options.map((option) => {
          const state = getOptionState(option)
          const isSelected = selectedAnswers.includes(option.id)

          return (
            <button
              key={option.id}
              type="button"
              onClick={() => handleOptionClick(option.id)}
              disabled={disabled}
              className={cn(
                'flex w-full items-start gap-3 rounded-xl border p-4 text-left transition-all',
                state === 'default' &&
                  'border-border bg-background hover:border-accent/40 hover:bg-muted/50',
                state === 'selected' && 'border-accent bg-accent/5',
                state === 'correct' && 'border-green-500 bg-green-50',
                state === 'incorrect' && 'border-red-500 bg-red-50',
                disabled && 'cursor-default',
              )}
            >
              {/* Selection indicator */}
              {isSingleSelect ? (
                <span
                  className={cn(
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                    state === 'correct' && 'border-green-600 bg-green-600',
                    state === 'incorrect' && 'border-red-600 bg-red-600',
                    state === 'selected' && 'border-accent bg-accent',
                    state === 'default' && 'border-muted-foreground',
                  )}
                >
                  {isSelected && !showCorrectness && (
                    <span className="h-2 w-2 rounded-full bg-white" />
                  )}
                  {showCorrectness && question.correctAnswers?.includes(option.id) && (
                    <Check className="h-3 w-3 text-white" />
                  )}
                </span>
              ) : (
                <span
                  className={cn(
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors',
                    state === 'correct' && 'border-green-600 bg-green-600',
                    state === 'incorrect' && 'border-red-600 bg-red-600',
                    state === 'selected' && 'border-accent bg-accent',
                    state === 'default' && 'border-muted-foreground',
                  )}
                >
                  {(isSelected || (showCorrectness && question.correctAnswers?.includes(option.id))) && (
                    <Check className="h-3 w-3 text-white" />
                  )}
                </span>
              )}

              {/* Option text */}
              <span
                className={cn(
                  'flex-1 text-sm leading-relaxed',
                  state === 'correct' && 'font-medium text-green-900',
                  state === 'incorrect' && 'font-medium text-red-900',
                  state === 'selected' && 'text-foreground',
                  state === 'default' && 'text-foreground',
                )}
              >
                {option.text}
              </span>
            </button>
          )
        })}
      </div>

      {/* Explanation (shown after submission if enabled) */}
      {showCorrectness && question.explanation && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-900">Explanation</p>
          <p className="mt-1 text-sm leading-relaxed text-blue-800">{question.explanation}</p>
        </div>
      )}
    </div>
  )
}

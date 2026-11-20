import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Award, BookOpen, RotateCcw, TrendingUp } from 'lucide-react'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { QuizReviewQuestion } from './QuizReviewQuestion'
import { cn } from '@/lib/utils'
import type { QuizResult } from '@/types/quiz'

export interface QuizResultsProps {
  result: QuizResult
  videoId?: string
  videoTitle?: string
  onRetake?: () => void
  className?: string
}

/**
 * Beautiful quiz results display.
 *
 * Shows overall score, statistics, question-by-question review, and
 * navigation actions. Uses restrained data visualization consistent with
 * NOETRA's design aesthetic.
 */
export function QuizResults({
  result,
  videoId,
  videoTitle,
  onRetake,
  className,
}: QuizResultsProps) {
  const navigate = useNavigate()

  const minutes = Math.floor(result.timeSpent / 60)
  const seconds = result.timeSpent % 60

  // Calculate score color
  const getScoreColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600'
    if (percentage >= 70) return 'text-blue-600'
    if (percentage >= 50) return 'text-amber-600'
    return 'text-red-600'
  }

  return (
    <div className={cn('space-y-8', className)}>
      {/* Header */}
      <div className="text-center">
        <div className="mb-4 inline-flex items-center justify-center rounded-full border-4 border-accent/20 bg-accent/10 p-6">
          <Award className="h-12 w-12 text-accent" />
        </div>
        <h1 className="font-serif text-3xl font-medium tracking-tight text-foreground">
          Quiz Complete!
        </h1>
        {videoTitle && (
          <p className="mt-2 text-sm text-muted-foreground">{videoTitle}</p>
        )}
      </div>

      {/* Score card */}
      <div className="rounded-2xl border border-border bg-card p-8 shadow-soft">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Main score */}
          <div className="text-center md:col-span-3">
            <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              Your Score
            </p>
            <p className={cn('mt-2 font-serif text-6xl font-medium', getScoreColor(result.percentage))}>
              {result.percentage}%
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {result.correctCount} out of {result.totalQuestions} correct
            </p>
          </div>

          {/* Statistics */}
          <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-4">
            <p className="text-2xl font-medium text-green-600">{result.correctCount}</p>
            <p className="mt-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Correct
            </p>
          </div>

          <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-4">
            <p className="text-2xl font-medium text-red-600">{result.incorrectCount}</p>
            <p className="mt-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Incorrect
            </p>
          </div>

          <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-4">
            <p className="text-2xl font-medium text-foreground">
              {minutes}:{String(seconds).padStart(2, '0')}
            </p>
            <p className="mt-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Time Spent
            </p>
          </div>
        </div>

        {/* Performance message */}
        <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4 text-center">
          <p className="text-sm font-medium text-blue-900">
            {result.percentage >= 90 && '🎉 Outstanding! You have excellent understanding of this material.'}
            {result.percentage >= 70 && result.percentage < 90 && '✓ Great work! You have a solid grasp of the concepts.'}
            {result.percentage >= 50 && result.percentage < 70 && 'Good effort! Review the explanations below to strengthen your understanding.'}
            {result.percentage < 50 && 'Keep learning! Review the material and try again to improve.'}
          </p>
        </div>
      </div>

      {/* Topic breakdown (if available) */}
      {result.topicBreakdown && result.topicBreakdown.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-lg font-medium text-foreground">
              Performance by Topic
            </h2>
          </div>
          <div className="space-y-3">
            {result.topicBreakdown.map((topic) => (
              <div key={topic.topic}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">{topic.topic}</span>
                  <span className="text-muted-foreground">
                    {topic.correct}/{topic.total}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      topic.percentage >= 70 ? 'bg-green-500' : 'bg-amber-500',
                    )}
                    style={{ width: `${topic.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question-by-question review */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
        <h2 className="mb-6 font-serif text-lg font-medium text-foreground">Review Your Answers</h2>
        <div className="space-y-6">
          {result.questionResults.map((questionResult, index) => (
            <QuizReviewQuestion
              key={questionResult.questionId}
              questionResult={questionResult}
              questionNumber={index + 1}
            />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        {onRetake && (
          <PrimaryButton onClick={onRetake} size="lg">
            <RotateCcw className="h-4 w-4" />
            Retake Quiz
          </PrimaryButton>
        )}
        {videoId && (
          <SecondaryButton onClick={() => navigate(`/learn/${videoId}`)} size="lg">
            <ArrowLeft className="h-4 w-4" />
            Back to Lecture
          </SecondaryButton>
        )}
        {videoId && (
          <SecondaryButton onClick={() => navigate(`/notes/${videoId}`)} size="lg">
            <BookOpen className="h-4 w-4" />
            Review Notes
          </SecondaryButton>
        )}
      </div>
    </div>
  )
}

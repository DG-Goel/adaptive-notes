import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, BrainCircuit, History, RefreshCw, TriangleAlert } from 'lucide-react'
import { PageTransition } from '@/components/common/PageTransition'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { QuizConfigPanel } from '@/components/quiz/QuizConfigPanel'
import { QuizPlayer } from '@/components/quiz/QuizPlayer'
import { QuizResults } from '@/components/quiz/QuizResults'
import { QuizHistory } from '@/components/quiz/QuizHistory'
import { useLecture } from '@/hooks/use-lecture-queries'
import { generateQuiz, submitQuiz, fetchQuizHistory } from '@/services/api/quiz'
import type { Quiz, QuizAttempt, QuizResult, QuizConfig } from '@/types/quiz'

type QuizStage = 'config' | 'playing' | 'results' | 'history'

/**
 * Quiz Studio main page.
 *
 * Orchestrates the full quiz workflow: configuration → playing → results.
 * Supports quiz history and retakes. All question generation and grading
 * happens via the backend in real mode, deterministically in mock mode.
 */
export function QuizStudioPage() {
  const { videoId } = useParams()
  const { data: lecture, isPending: lecturePending, isError: lectureError } = useLecture(videoId)

  const [stage, setStage] = useState<QuizStage>('config')
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null)
  const [activeAttempt, setActiveAttempt] = useState<QuizAttempt | null>(null)
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null)

  // Fetch quiz history
  const {
    data: history = [],
    isPending: historyPending,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['quiz-history'],
    queryFn: ({ signal }) => fetchQuizHistory(signal),
    staleTime: 30_000,
  })

  // Generate quiz mutation
  const generateMutation = useMutation({
    mutationFn: (config: Partial<QuizConfig>) =>
      generateQuiz(
        {
          videoId: videoId ?? '',
          questionCount: config.questionCount ?? 10,
          difficulty: config.difficulty,
          questionTypes: config.questionTypes,
          context: config.context,
        },
        undefined,
      ),
    onSuccess: (quiz) => {
      setActiveQuiz(quiz)
      setActiveAttempt({
        id: `attempt-${Date.now()}`,
        quizId: quiz.id,
        videoId: quiz.videoId,
        config: quiz.config,
        answers: {},
        markedForReview: new Set(),
        startedAt: new Date().toISOString(),
      })
      setStage('playing')
    },
  })

  // Submit quiz mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!activeQuiz || !activeAttempt) throw new Error('No active quiz')

      const timeSpent = Math.floor(
        (Date.now() - new Date(activeAttempt.startedAt).getTime()) / 1000,
      )

      return submitQuiz(
        activeQuiz,
        {
          quizId: activeAttempt.quizId,
          answers: activeAttempt.answers,
          timeSpent,
        },
        undefined,
      )
    },
    onSuccess: (result) => {
      setQuizResult(result)
      setStage('results')
      void refetchHistory()
    },
  })

  const handleStartQuiz = (config: Partial<QuizConfig>) => {
    generateMutation.mutate(config)
  }

  const handleUpdateAnswer = (questionId: string, optionIds: string[]) => {
    if (!activeAttempt) return
    setActiveAttempt({
      ...activeAttempt,
      answers: { ...activeAttempt.answers, [questionId]: optionIds },
    })
  }

  const handleToggleReview = (questionId: string) => {
    if (!activeAttempt) return
    const next = new Set(activeAttempt.markedForReview)
    if (next.has(questionId)) {
      next.delete(questionId)
    } else {
      next.add(questionId)
    }
    setActiveAttempt({ ...activeAttempt, markedForReview: next })
  }

  const handleSubmit = () => {
    submitMutation.mutate()
  }

  const handleRetake = () => {
    setActiveQuiz(null)
    setActiveAttempt(null)
    setQuizResult(null)
    setStage('config')
  }

  const handleViewHistory = () => {
    setStage('history')
  }

  const handleBackToConfig = () => {
    setStage('config')
  }

  if (!videoId) {
    return (
      <PageTransition>
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="No lecture selected"
          description="Choose a lecture from your library to generate a quiz."
          action={
            <Link to="/library">
              <PrimaryButton>
                <ArrowLeft className="h-4 w-4" /> Back to library
              </PrimaryButton>
            </Link>
          }
        />
      </PageTransition>
    )
  }

  if (lecturePending) {
    return (
      <PageTransition>
        <div className="space-y-4">
          <LoadingSkeleton variant="text" className="max-w-md" />
          <LoadingSkeleton variant="card" />
        </div>
      </PageTransition>
    )
  }

  if (lectureError || !lecture) {
    return (
      <PageTransition>
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="Lecture unavailable"
          description="This lecture could not be loaded."
          action={
            <Link to="/library">
              <SecondaryButton>
                <ArrowLeft className="h-4 w-4" /> Back to library
              </SecondaryButton>
            </Link>
          }
        />
      </PageTransition>
    )
  }

  // Playing stage - full screen quiz player
  if (stage === 'playing' && activeQuiz && activeAttempt) {
    return (
      <PageTransition>
        <div className="-mx-4 -my-6 sm:-mx-6 lg:-mx-8 lg:-my-8">
          <QuizPlayer
            quiz={activeQuiz}
            attempt={activeAttempt}
            onUpdateAnswer={handleUpdateAnswer}
            onToggleReview={handleToggleReview}
            onSubmit={handleSubmit}
            onExit={handleBackToConfig}
          />
        </div>
      </PageTransition>
    )
  }

  // Results stage
  if (stage === 'results' && quizResult) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-4xl">
          <QuizResults
            result={quizResult}
            videoId={videoId}
            videoTitle={lecture.title}
            onRetake={handleRetake}
          />
        </div>
      </PageTransition>
    )
  }

  // History stage
  if (stage === 'history') {
    return (
      <PageTransition>
        <div className="space-y-6">
          <header className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.16em] text-accent">
                Quiz History
              </p>
              <h1 className="mt-1 font-serif text-2xl font-medium tracking-tight text-foreground">
                Your Quiz Attempts
              </h1>
            </div>
            <SecondaryButton onClick={handleBackToConfig}>
              <ArrowLeft className="h-4 w-4" />
              Back
            </SecondaryButton>
          </header>

          {historyPending ? (
            <LoadingSkeleton variant="card" />
          ) : (
            <QuizHistory attempts={history} onRetake={handleRetake} />
          )}
        </div>
      </PageTransition>
    )
  }

  // Config stage (default)
  return (
    <PageTransition>
      <div className="space-y-6">
        <header>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <p className="text-sm font-medium uppercase tracking-[0.16em] text-accent">
                Quiz Studio
              </p>
              <h1 className="mt-1 font-serif text-2xl font-medium tracking-tight text-foreground">
                {lecture.title}
              </h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Test your understanding with AI-generated questions from this lecture.
              </p>
            </div>
            <Link to={`/learn/${videoId}`}>
              <SecondaryButton>
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Back to lecture</span>
              </SecondaryButton>
            </Link>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Quiz configuration */}
          <div className="lg:col-span-2">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
              <div className="mb-6 flex items-center gap-2">
                <BrainCircuit className="h-5 w-5 text-accent" />
                <h2 className="font-serif text-lg font-medium text-foreground">
                  Configure Your Quiz
                </h2>
              </div>

              <QuizConfigPanel
                videoId={videoId}
                videoTitle={lecture.title}
                onStartQuiz={handleStartQuiz}
                loading={generateMutation.isPending}
              />

              {generateMutation.isError && (
                <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                  <p className="text-sm text-foreground">
                    {generateMutation.error instanceof Error
                      ? generateMutation.error.message
                      : 'Failed to generate quiz. Please try again.'}
                  </p>
                  <SecondaryButton
                    size="sm"
                    onClick={() => generateMutation.reset()}
                    className="mt-2"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Try again
                  </SecondaryButton>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quiz history card */}
            <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
              <div className="mb-4 flex items-center gap-2">
                <History className="h-5 w-5 text-accent" />
                <h3 className="font-serif text-base font-medium text-foreground">
                  Recent Attempts
                </h3>
              </div>

              {historyPending ? (
                <LoadingSkeleton variant="text" />
              ) : history.length > 0 ? (
                <>
                  <div className="space-y-3">
                    {history.slice(0, 3).map((attempt) => (
                      <div
                        key={attempt.id}
                        className="flex items-center justify-between rounded-lg border border-border bg-background p-3"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-foreground">
                            {attempt.questionCount} questions
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(attempt.attemptedAt).toLocaleDateString()}
                          </p>
                        </div>
                        {attempt.percentage !== undefined && (
                          <span className="text-lg font-medium text-accent">
                            {attempt.percentage}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                  <SecondaryButton
                    onClick={handleViewHistory}
                    size="sm"
                    className="mt-4 w-full"
                  >
                    View All History
                  </SecondaryButton>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No quiz attempts yet. Generate your first quiz to get started!
                </p>
              )}
            </div>

            {/* Tips card */}
            <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
              <h3 className="mb-3 font-serif text-base font-medium text-blue-900">
                Quiz Tips
              </h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex gap-2">
                  <span className="text-blue-600">•</span>
                  <span>Practice mode shows explanations immediately</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-600">•</span>
                  <span>Exam mode tests you without hints</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-600">•</span>
                  <span>Click timestamps to review relevant lecture moments</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-600">•</span>
                  <span>You can retake quizzes as many times as you like</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}

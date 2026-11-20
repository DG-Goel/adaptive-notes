import { apiClient } from './client'
import { delay } from './mock-support'
import { endpoints, USE_MOCK_API } from '@/config/endpoints'
import { buildMockQuiz, gradeQuizAttempt, mockQuizHistory } from '@/mocks/quiz'
import type {
  Quiz,
  QuizResult,
  QuizAttemptSummary,
  QuestionResult,
} from '@/types/quiz'

/**
 * Backend capability flags for quiz features.
 *
 * These default to the currently-unconfirmed state. Flip a flag only after
 * the backend contract is verified to support the feature.
 */
export const quizCapabilities = {
  supportsGeneration: false,
  supportsHistory: false,
  supportsTimedQuizzes: false,
  supportsCustomQuestionCount: false,
  supportsQuestionTypeFiltering: false,
  supportsContextFiltering: false,
} as const

export interface GenerateQuizRequest {
  videoId: string
  questionCount?: number
  difficulty?: string
  questionTypes?: string[]
  context?: string
  contextId?: string
}

/**
 * Generate a new quiz for a video.
 *
 * Mock mode returns a deterministic Transformer quiz.
 * Real mode calls the configured generation endpoint.
 */
export async function generateQuiz(
  request: GenerateQuizRequest,
  signal?: AbortSignal,
): Promise<Quiz> {
  if (USE_MOCK_API) {
    await delay(800)
    return buildMockQuiz({
      questionCount: request.questionCount ?? 10,
      difficulty: request.difficulty as Quiz['config']['difficulty'],
      questionTypes: request.questionTypes as Quiz['config']['questionTypes'],
    })
  }

  const response = await apiClient.post<Quiz>(
    endpoints.quizGenerate(request.videoId),
    request,
    { signal },
  )
  return response
}

/**
 * Fetch an existing quiz by ID.
 *
 * Mock mode returns the last-generated quiz.
 * Real mode fetches from the backend.
 */
export async function fetchQuiz(quizId: string, signal?: AbortSignal): Promise<Quiz> {
  if (USE_MOCK_API) {
    await delay(300)
    return buildMockQuiz({ questionCount: 10 })
  }

  return apiClient.get<Quiz>(endpoints.quiz(quizId), { signal })
}

export interface SubmitQuizRequest {
  quizId: string
  answers: Record<string, string[]>
  timeSpent: number
}

/**
 * Submit quiz answers and receive graded results.
 *
 * Mock mode evaluates answers deterministically against the fixture answer keys.
 * Real mode submits to the backend for grading.
 */
export async function submitQuiz(
  quiz: Quiz,
  request: SubmitQuizRequest,
  signal?: AbortSignal,
): Promise<QuizResult> {
  if (USE_MOCK_API) {
    await delay(600)

    const { score, correctCount, incorrectCount, unansweredCount } = gradeQuizAttempt(
      quiz,
      request.answers,
    )

    const totalQuestions = quiz.questions.length
    const percentage = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0

    const questionResults: QuestionResult[] = quiz.questions.map((question) => {
      const userAnswers = request.answers[question.id] ?? []
      const correctAnswers = question.correctAnswers ?? []
      const isCorrect =
        userAnswers.length === correctAnswers.length &&
        userAnswers.every((ans) => correctAnswers.includes(ans))

      return {
        questionId: question.id,
        question,
        userAnswers,
        correctAnswers,
        isCorrect,
        explanation: question.explanation,
      }
    })

    return {
      attemptId: `attempt-${Date.now()}`,
      quizId: request.quizId,
      score,
      totalQuestions,
      correctCount,
      incorrectCount,
      unansweredCount,
      percentage,
      timeSpent: request.timeSpent,
      questionResults,
    }
  }

  return apiClient.post<QuizResult>(endpoints.quizSubmit(request.quizId), request, { signal })
}

/**
 * Retrieve quiz attempt history.
 *
 * Mock mode returns deterministic demo attempts.
 * Real mode fetches from backend if persistence is supported.
 */
export async function fetchQuizHistory(signal?: AbortSignal): Promise<QuizAttemptSummary[]> {
  if (USE_MOCK_API) {
    await delay(400)
    return [...mockQuizHistory]
  }

  if (!quizCapabilities.supportsHistory) {
    return []
  }

  const response = await apiClient.get<{ attempts: QuizAttemptSummary[] }>(
    endpoints.quizHistory,
    { signal },
  )
  return response.attempts
}

/**
 * Quiz attempt storage for mock/local mode.
 *
 * In mock mode, attempts persist to localStorage with a clear "Local demo history" label.
 * In real mode, persistence is backend-dependent.
 */
const STORAGE_KEY = 'noetra.quiz.attempts'

export const quizStorage = {
  isLocal: USE_MOCK_API,
  label: USE_MOCK_API ? 'Local demo history' : quizCapabilities.supportsHistory ? 'Server' : 'Session only',

  list(): string {
    if (USE_MOCK_API) {
      return localStorage.getItem(STORAGE_KEY) ?? '[]'
    }
    return '[]'
  },

  save(json: string): void {
    if (USE_MOCK_API) {
      localStorage.setItem(STORAGE_KEY, json)
    }
  },

  clear(): void {
    if (USE_MOCK_API) {
      localStorage.removeItem(STORAGE_KEY)
    }
  },
}

/* Quiz and assessment type definitions */

export type QuestionType = 'single_select' | 'multi_select' | 'true_false'

export type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed'

export type QuizMode = 'practice' | 'exam'

export interface QuestionOption {
  id: string
  text: string
}

export interface QuestionSource {
  videoId?: string
  chapterId?: string
  timestampSeconds?: number
  noteSectionId?: string
  excerpt?: string
}

export interface QuizQuestion {
  id: string
  type: QuestionType
  question: string
  options: QuestionOption[]
  correctAnswers?: string[] // Only present after submission or in mock mode
  explanation?: string
  difficulty?: QuizDifficulty
  source?: QuestionSource
}

export interface QuizConfig {
  videoId?: string
  questionCount: number
  difficulty: QuizDifficulty
  questionTypes: QuestionType[]
  context: 'video' | 'chapter' | 'timestamp' | 'notes'
  contextId?: string
  showExplanations: boolean
  timed: boolean
  timeLimit?: number // seconds
  shuffleQuestions: boolean
  shuffleOptions: boolean
  mode: QuizMode
}

export interface QuizAttempt {
  id: string
  quizId: string
  videoId?: string
  config: QuizConfig
  answers: Record<string, string[]> // questionId -> selected option IDs
  markedForReview: Set<string>
  startedAt: string
  submittedAt?: string
  timeSpent?: number
}

export interface QuizResult {
  attemptId: string
  quizId: string
  score: number
  totalQuestions: number
  correctCount: number
  incorrectCount: number
  unansweredCount: number
  percentage: number
  timeSpent: number
  questionResults: QuestionResult[]
  topicBreakdown?: TopicScore[]
}

export interface QuestionResult {
  questionId: string
  question: QuizQuestion
  userAnswers: string[]
  correctAnswers: string[]
  isCorrect: boolean
  explanation?: string
}

export interface TopicScore {
  topic: string
  correct: number
  total: number
  percentage: number
}

export interface Quiz {
  id: string
  videoId?: string
  title: string
  config: QuizConfig
  questions: QuizQuestion[]
  createdAt: string
  isDemo?: boolean
}

export interface QuizHistory {
  attempts: QuizAttemptSummary[]
}

export interface QuizAttemptSummary {
  id: string
  quizId: string
  videoId?: string
  videoTitle?: string
  questionCount: number
  difficulty: QuizDifficulty
  mode: QuizMode
  score?: number
  percentage?: number
  timeSpent?: number
  attemptedAt: string
  completed: boolean
  isDemo?: boolean
}

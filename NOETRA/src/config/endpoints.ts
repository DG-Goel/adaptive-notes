export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000/api/v1'

export const USE_MOCK_API =
  (import.meta.env.VITE_USE_MOCK_API as string | undefined) === 'true'

/**
 * API endpoint registry.
 *
 * The paths below are the proposed frontend contract — they are NOT verified
 * against the existing backend. All mappings live here so they can be
 * reconciled with the real API in one place. `API_BASE_URL` already includes
 * the `/api/v1` prefix.
 */
export const endpoints = {
  health: '/health',

  // Videos
  videos: '/videos',
  video: (id: string) => `/videos/${id}`,
  videoStream: (id: string) => `/videos/${id}/stream`,
  videoChapters: (id: string) => `/videos/${id}/chapters`,
  videoUpload: '/videos/upload',
  videoImport: '/videos/import',

  // Transcript
  videoTranscript: (id: string) => `/videos/${id}/transcript`,

  // Notes & summary
  /** Structured note document (sections + blocks). GET to read, PUT to save. */
  notesDocument: (videoId: string) => `/videos/${videoId}/notes/document`,
  notesGenerate: (videoId: string) => `/videos/${videoId}/notes/generate`,
  /** Second-pass pipeline: analyse existing notes for visual opportunities. */
  notesEnhance: (videoId: string) => `/videos/${videoId}/notes/enhance`,
  /** Processing status for a generation / enhancement job. */
  notesStatus: (videoId: string) => `/videos/${videoId}/notes/status`,
  notesVersions: (videoId: string) => `/videos/${videoId}/notes/versions`,
  notesExport: (videoId: string) => `/videos/${videoId}/notes/export`,
  videoSummary: (videoId: string) => `/videos/${videoId}/summary`,
  videoVisuals: (videoId: string) => `/videos/${videoId}/visuals`,

  // Quizzes
  quizGenerate: (videoId: string) => `/videos/${videoId}/quiz/generate`,
  quiz: (quizId: string) => `/quizzes/${quizId}`,
  quizSubmit: (quizId: string) => `/quizzes/${quizId}/submit`,
  quizResults: (quizId: string) => `/quizzes/${quizId}/results`,
  quizHistory: '/quizzes/history',

  // Knowledge map
  knowledgeMap: (videoId: string) => `/videos/${videoId}/knowledge-map`,
  conceptDetail: (conceptId: string) => `/concepts/${conceptId}`,

  // AI tutor
  ask: '/ask',
  tutor: '/tutor/chat',
} as const

export type EndpointKey = keyof typeof endpoints

/**
 * Tunables for the AI question-answering contract.
 * The backend contract is not verified yet, so the video scope stays behind a
 * flag that can be switched on once it is confirmed.
 */
export const askDefaults = {
  mode: 'lecture',
  topK: 4,
  /** Set to true once the backend confirms it accepts a video-scoped question. */
  includeVideoScope: false,
} as const

/* AI tutor conversation and question-answering contract types. */

export type TutorRole = 'user' | 'assistant'

/**
 * Citation source type. The citation model is extensible: the backend may not
 * return all fields, so everything beyond `id` and `type` is optional. When a
 * backend response contains only answer text, no citations are fabricated.
 */
export type TutorCitationType = 'video' | 'transcript' | 'notes' | 'document'

export interface TutorCitation {
  id: string
  type: TutorCitationType
  /** Short label shown on the citation chip (e.g. chapter or section title). */
  label?: string
  /** Referenced lecture timestamp in seconds. Kept for backward compatibility. */
  timestamp?: number
  startSeconds?: number
  endSeconds?: number
  videoId?: string
  sectionId?: string
  sourceId?: string
  title?: string
  excerpt?: string
}

export interface TutorMessage {
  id: string
  role: TutorRole
  content: string
  /** ISO date string. */
  createdAt: string
  citations?: TutorCitation[]
  /** Marks deterministic mock replies so the UI can label them as examples. */
  isDemo?: boolean
  /** When true the message is a placeholder while the assistant answer streams. */
  pending?: boolean
  /** Error message when this assistant turn failed. */
  error?: string
}

/**
 * Conversation context. This is a frontend model — it does not assume the
 * backend accepts every field. Mapping to the request body is centralized in
 * the service layer and gated by capability flags.
 */
export type TutorContext =
  | { type: 'general' }
  | { type: 'video'; videoId: string }
  | { type: 'chapter'; videoId: string; chapterId: string }
  | { type: 'timestamp'; videoId: string; startSeconds: number; endSeconds: number }
  | { type: 'notes'; videoId: string; sectionId: string; selectedText?: string }

/**
 * Explanation style. Frontend preference only — mapped to the backend only
 * when a capability flag confirms support. The backend's existing `mode` value
 * (e.g. `strict`) is retrieval-oriented and is NOT treated as a synonym for any
 * of these styles.
 */
export type ExplanationMode = 'simple' | 'detailed' | 'step-by-step' | 'examples' | 'revision'

export interface ExplanationPreferences {
  mode?: ExplanationMode
  /** 'short' | 'medium' | 'long' — frontend hint, sent only if supported. */
  length?: 'short' | 'medium' | 'long'
  includeExamples?: boolean
  includeMath?: boolean
  preferBullets?: boolean
}

export interface TutorConversation {
  id: string
  title: string
  videoId?: string
  context: TutorContext
  messages: TutorMessage[]
  createdAt: string
  updatedAt: string
  /** True when the conversation was created in mock mode. */
  isDemo?: boolean
}

/**
 * Request body for the AI question-answering backend.
 *
 * The existing backend exposes a route resembling `POST /api/v1/ask` with
 * fields such as `question`, `mode`, `top_k`, and `conversation_history`.
 * `video_id` is optional and only sent when a video-scoped contract is
 * configured — the endpoint is not assumed to be video-scoped yet.
 */
export interface AskRequest {
  question: string
  mode: string
  top_k: number
  conversation_history: { role: TutorRole; content: string }[]
  video_id?: string
}

export interface AskResponse {
  answer: string
  citations?: TutorCitation[]
  isDemo?: boolean
}

/**
 * Streaming chunk. The streaming interface is defined but only used when a
 * real streaming endpoint is confirmed; otherwise responses are rendered
 * complete. Token streaming is never simulated in real API mode.
 */
export interface AskStreamChunk {
  type: 'delta' | 'done' | 'error'
  delta?: string
  answer?: string
  citations?: TutorCitation[]
  error?: string
}

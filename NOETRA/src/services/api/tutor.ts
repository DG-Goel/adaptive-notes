import { USE_MOCK_API } from '@/config/endpoints'
import type {
  AskResponse,
  AskStreamChunk,
  ExplanationPreferences,
  TutorCitation,
  TutorContext,
  TutorRole,
} from '@/types/tutor'

/**
 * Raw shape returned by the ask route. The backend contract is not verified,
 * so the mapping is deliberately defensive.
 */
interface AskBackendResponse {
  answer?: string
  response?: string
  citations?: {
    id?: string
    type?: string
    label?: string
    timestamp?: number
    start?: number
    end?: number
    video_id?: string
    section_id?: string
    source_id?: string
    title?: string
    excerpt?: string
    doc_title?: string
    section_path?: string
    chunk_id?: string
  }[]
  isDemo?: boolean
}

function normaliseCitations(
  raw: AskBackendResponse['citations'],
): TutorCitation[] | undefined {
  if (!raw || raw.length === 0) return undefined
  return raw
    .map((citation, index) => {
      const timestamp = citation.timestamp ?? citation.start
      return {
        id: citation.id ?? `citation-${index}`,
        type: (citation.type as TutorCitation['type']) ?? 'video',
        label: citation.label ?? citation.title ?? citation.doc_title ?? 'Source',
        timestamp: Number.isFinite(timestamp) ? timestamp : undefined,
        startSeconds: Number.isFinite(citation.start) ? citation.start : undefined,
        endSeconds: Number.isFinite(citation.end) ? citation.end : undefined,
        videoId: citation.video_id,
        sectionId: citation.section_id,
        sourceId: citation.source_id,
        title: citation.title ?? citation.doc_title,
        excerpt: citation.excerpt ?? citation.section_path,
      }
    })
    .filter((citation) => citation.timestamp !== undefined || citation.title !== undefined)
}

/**
 * Backend capability flags. These default to the currently-confirmed state:
 * only `video_id` is optionally supported (behind the existing
 * `includeVideoScope` flag). All other scopes, streaming, and conversation
 * persistence are unconfirmed and therefore disabled.
 *
 * Flip a flag here only after the backend contract is verified to accept the
 * corresponding field.
 */
export const tutorCapabilities = {
  supportsVideoScope: true,
  supportsChapterScope: false,
  supportsTimestampScope: false,
  supportsNotesScope: false,
  supportsExplanationMode: false,
  supportsStreaming: false,
  supportsConversationPersistence: false,
} as const

export interface AskTutorOptions {
  question: string
  history: { role: TutorRole; content: string }[]
  videoId?: string
  context?: TutorContext
  preferences?: ExplanationPreferences
  signal?: AbortSignal
}

/**
 * Map the frontend context/preferences onto the confirmed backend request
 * shape. Unsupported fields are dropped — never silently substituted.
 */
export async function askTutor({
  question,
  videoId,
  context,
  signal,
}: AskTutorOptions): Promise<AskResponse> {
  const scopedVideo = videoId ?? (context && 'videoId' in context ? context.videoId : undefined)
  const video = scopedVideo?.startsWith('local:') ? scopedVideo.slice('local:'.length) : undefined
  const jobId = scopedVideo ? localStorage.getItem('noetra:video-notes:' + scopedVideo) : null
  if (scopedVideo && !video && !jobId) throw new Error('Generate notes in this video’s AI Notes tab first.')
  const response = await fetch('/api/video-notes/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, job_id: jobId, video }),
    signal,
  })
  const data = await response.json().catch(() => null) as (AskBackendResponse & { detail?: string }) | null
  if (!response.ok || !data) throw new Error(data?.detail ?? 'The local tutor service is unavailable.')
  const answer = data?.answer ?? data?.response ?? ''
  return {
    answer,
    citations: normaliseCitations(data?.citations),
  }
}

export interface AskTutorStreamOptions extends AskTutorOptions {
  onChunk?: (chunk: AskStreamChunk) => void
}

/**
 * Streaming ask. The interface exists so the UI can render partial output once
 * a real streaming endpoint is confirmed. Until then:
 * - Real mode rejects with a clear "streaming not supported" error (no token
 *   simulation).
 * - Mock mode yields the full answer in a single chunk (not token-by-token).
 */
export async function askTutorStream(options: AskTutorStreamOptions): Promise<AskResponse> {
  void options
  throw new Error('Streaming endpoint is not configured.')
}

/* -------------------------------------------------------------------------- */
/* Conversation persistence helpers                                           */
/* -------------------------------------------------------------------------- */

const STORAGE_KEY = 'noetra.tutor.conversations'

/**
 * In mock mode conversations persist to localStorage and are labelled as local
 * demo history. In real mode persistence is session-only (no localStorage
 * writes) until a backend endpoint is confirmed.
 */
export const conversationStorage = {
  isLocal: USE_MOCK_API,
  label: USE_MOCK_API ? 'Local demo history' : 'Session only',

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
    // Real mode: intentionally a no-op until persistence is confirmed.
  },

  clear(): void {
    if (USE_MOCK_API) {
      localStorage.removeItem(STORAGE_KEY)
    }
  },
}

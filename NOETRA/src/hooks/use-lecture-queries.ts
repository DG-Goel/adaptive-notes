import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getNoteDocument,
  getNotesExportCapabilities,
  getNotesStatus,
  getNoteVersions,
  getSummary,
  getTranscript,
  getVideo,
  getVisuals,
  saveNoteDocument,
  startNotesEnhancement,
  startNotesGeneration,
} from '@/services/api'
import type { NotesGenerationOptions, SaveNoteDocumentRequest } from '@/types/notes'

/**
 * TanStack Query wrappers for the learning workspace and the Notes Studio.
 *
 * All async lecture data flows through these hooks so loading, error, and
 * caching behaviour stays consistent and cancellation is handled by the query
 * client's signal.
 */

export const lectureKeys = {
  video: (videoId: string) => ['lecture', 'video', videoId] as const,
  transcript: (videoId: string) => ['lecture', 'transcript', videoId] as const,
  noteDocument: (videoId: string) => ['lecture', 'notes', 'document', videoId] as const,
  noteVersions: (videoId: string) => ['lecture', 'notes', 'versions', videoId] as const,
  notesStatus: (videoId: string) => ['lecture', 'notes', 'status', videoId] as const,
  notesExport: (videoId: string) => ['lecture', 'notes', 'export', videoId] as const,
  summary: (videoId: string) => ['lecture', 'summary', videoId] as const,
  visuals: (videoId: string) => ['lecture', 'visuals', videoId] as const,
}

export function useLecture(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.video(videoId ?? ''),
    queryFn: ({ signal }) => getVideo(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

export function useTranscript(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.transcript(videoId ?? ''),
    queryFn: ({ signal }) => getTranscript(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

/** The structured note document rendered by the shared notes renderer. */
export function useNoteDocument(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.noteDocument(videoId ?? ''),
    queryFn: ({ signal }) => getNoteDocument(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

export function useNoteVersions(videoId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: lectureKeys.noteVersions(videoId ?? ''),
    queryFn: ({ signal }) => getNoteVersions(videoId as string, signal),
    enabled: Boolean(videoId) && enabled,
  })
}

/**
 * Processing status for a generation / enhancement job.
 *
 * Polling is opt-in and always driven by the API response — the progress value
 * shown in the UI is whatever the backend reported, never an invented number.
 */
export function useNotesStatus(
  videoId: string | undefined,
  options: { enabled?: boolean; poll?: boolean } = {},
) {
  const { enabled = false, poll = false } = options
  return useQuery({
    queryKey: lectureKeys.notesStatus(videoId ?? ''),
    queryFn: ({ signal }) => getNotesStatus(videoId as string, signal),
    enabled: Boolean(videoId) && enabled,
    refetchInterval: poll
      ? (query) => {
          const stage = query.state.data?.stage
          return stage === 'completed' || stage === 'failed' ? false : 2500
        }
      : false,
  })
}

export function useNotesExportCapabilities(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.notesExport(videoId ?? ''),
    queryFn: ({ signal }) => getNotesExportCapabilities(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

export function useSummary(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.summary(videoId ?? ''),
    queryFn: ({ signal }) => getSummary(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

export function useVisuals(videoId: string | undefined) {
  return useQuery({
    queryKey: lectureKeys.visuals(videoId ?? ''),
    queryFn: ({ signal }) => getVisuals(videoId as string, signal),
    enabled: Boolean(videoId),
  })
}

/* ------------------------------------------------------------------ *
 * Mutations
 * ------------------------------------------------------------------ */

export function useSaveNoteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: SaveNoteDocumentRequest) => saveNoteDocument(request),
    onSuccess: (result) => {
      queryClient.setQueryData(
        lectureKeys.noteDocument(result.document.videoId),
        result.document,
      )
      void queryClient.invalidateQueries({
        queryKey: lectureKeys.noteVersions(result.document.videoId),
      })
    },
  })
}

export function useStartNotesGeneration() {
  return useMutation({
    mutationFn: (options: NotesGenerationOptions) => startNotesGeneration(options),
  })
}

export function useStartNotesEnhancement() {
  return useMutation({
    mutationFn: (videoId: string) => startNotesEnhancement(videoId),
  })
}

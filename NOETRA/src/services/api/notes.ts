import { apiClient } from './client'
import { delay } from './mock-support'
import { endpoints, USE_MOCK_API } from '@/config/endpoints'
import { ApiErrorException } from '@/types/api'
import type {
  LectureSummary,
  NoteDocument,
  NoteDocumentVersion,
  NotesExportCapability,
  NotesExportFormat,
  NotesExportResult,
  NotesGenerationOptions,
  NotesProcessingStatus,
  SaveNoteDocumentRequest,
  SaveNoteDocumentResult,
  VisualArtifact,
} from '@/types/notes'
import {
  findMockNoteDocument,
  findMockNoteVersions,
  findMockSummary,
  findMockVisuals,
  mockExportCapabilities,
  mockQueuedStatus,
} from '@/mocks/notes'

export async function getSummary(
  videoId: string,
  signal?: AbortSignal,
): Promise<LectureSummary> {
  if (USE_MOCK_API) {
    await delay(280)
    const summary = findMockSummary(videoId)
    if (!summary) {
      throw new ApiErrorException({
        status: 404,
        message: `No summary is available for "${videoId}".`,
      })
    }
    return summary
  }
  return apiClient.get<LectureSummary>(endpoints.videoSummary(videoId), { signal })
}

export async function getVisuals(
  videoId: string,
  signal?: AbortSignal,
): Promise<VisualArtifact[]> {
  if (USE_MOCK_API) {
    await delay(200)
    return findMockVisuals(videoId)
  }
  return apiClient.get<VisualArtifact[]>(endpoints.videoVisuals(videoId), { signal })
}

/* ------------------------------------------------------------------ *
 * Structured note document
 * ------------------------------------------------------------------ */

export async function getNoteDocument(
  videoId: string,
  signal?: AbortSignal,
): Promise<NoteDocument> {
  if (USE_MOCK_API) {
    await delay(340)
    const document = findMockNoteDocument(videoId)
    if (!document) {
      throw new ApiErrorException({
        status: 404,
        message: `No note document is available for "${videoId}".`,
      })
    }
    return document
  }
  // Real mode never falls back to fixtures — a failure surfaces to the UI.
  return apiClient.get<NoteDocument>(endpoints.notesDocument(videoId), { signal })
}

export async function saveNoteDocument(
  request: SaveNoteDocumentRequest,
  signal?: AbortSignal,
): Promise<SaveNoteDocumentResult> {
  if (USE_MOCK_API) {
    await delay(420)
    const existing = findMockNoteDocument(request.videoId)
    if (!existing) {
      throw new ApiErrorException({
        status: 404,
        message: `No note document is available for "${request.videoId}".`,
      })
    }
    // Demo editing only: nothing is persisted anywhere. The UI labels this
    // explicitly instead of claiming the edit reached a server.
    return {
      document: {
        ...existing,
        title: request.title,
        sections: request.sections,
        version: request.version + 1,
        updatedAt: existing.updatedAt,
      },
      conflict: false,
    }
  }
  return apiClient.put<SaveNoteDocumentResult>(endpoints.notesDocument(request.videoId), request, {
    signal,
  })
}

export async function getNoteVersions(
  videoId: string,
  signal?: AbortSignal,
): Promise<NoteDocumentVersion[]> {
  if (USE_MOCK_API) {
    await delay(180)
    return findMockNoteVersions(videoId)
  }
  return apiClient.get<NoteDocumentVersion[]>(endpoints.notesVersions(videoId), { signal })
}

/* ------------------------------------------------------------------ *
 * Generation & visual enhancement
 * ------------------------------------------------------------------ */

export async function startNotesGeneration(
  options: NotesGenerationOptions,
  signal?: AbortSignal,
): Promise<NotesProcessingStatus> {
  if (USE_MOCK_API) {
    await delay(260)
    return mockQueuedStatus(options.videoId, 'notes')
  }
  return apiClient.post<NotesProcessingStatus>(endpoints.notesGenerate(options.videoId), options, {
    signal,
  })
}

export async function startNotesEnhancement(
  videoId: string,
  signal?: AbortSignal,
): Promise<NotesProcessingStatus> {
  if (USE_MOCK_API) {
    await delay(260)
    return mockQueuedStatus(videoId, 'visuals')
  }
  return apiClient.post<NotesProcessingStatus>(endpoints.notesEnhance(videoId), undefined, { signal })
}

export async function getNotesStatus(
  videoId: string,
  signal?: AbortSignal,
): Promise<NotesProcessingStatus> {
  if (USE_MOCK_API) {
    await delay(240)
    return mockQueuedStatus(videoId, 'notes')
  }
  return apiClient.get<NotesProcessingStatus>(endpoints.notesStatus(videoId), { signal })
}

/* ------------------------------------------------------------------ *
 * Export
 * ------------------------------------------------------------------ */

export async function getNotesExportCapabilities(
  videoId: string,
  signal?: AbortSignal,
): Promise<NotesExportCapability[]> {
  if (USE_MOCK_API) {
    await delay(140)
    return mockExportCapabilities()
  }
  return apiClient.get<NotesExportCapability[]>(endpoints.notesExport(videoId), { signal })
}

/**
 * Request a server-side export (PDF/DOCX). Markdown and sanitised HTML are
 * produced entirely on the client and never reach this function, so nothing is
 * silently substituted when a format is unavailable.
 */
export async function requestNotesExport(
  videoId: string,
  format: NotesExportFormat,
  payload: string,
  signal?: AbortSignal,
): Promise<NotesExportResult> {
  if (USE_MOCK_API) {
    throw new ApiErrorException({
      status: 501,
      message: `The backend does not provide ${format.toUpperCase()} export. Markdown and HTML can be exported locally.`,
    })
  }
  return apiClient.post<NotesExportResult>(
    endpoints.notesExport(videoId),
    { videoId, format, payload },
    { signal },
  )
}

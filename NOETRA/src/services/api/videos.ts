import { apiClient } from './client'
import { delay } from './mock-support'
import { API_BASE_URL, endpoints, USE_MOCK_API } from '@/config/endpoints'
import { ApiErrorException } from '@/types/api'
import type { VideoImportRequest, VideoImportResult, VideoLecture } from '@/types/video'
import { findMockLecture, mockVideoLectures } from '@/mocks/videos'

export async function listLocalVideos(signal?: AbortSignal): Promise<VideoLecture[]> {
  const response = await fetch('/api/videos', { signal })
  if (!response.ok) throw new Error('Start the local video notes service to load your lectures.')
  const names: string[] = await response.json()
  return names.map(name => ({
    id: 'local:' + name,
    title: name,
    description: '',
    course: 'Local videos',
    instructor: '',
    duration: 0,
    source: { url: '/api/videos/' + encodeURIComponent(name), provider: 'Local video' },
    status: 'ready',
    updatedAt: '',
    objectives: [],
    keyConcepts: [],
    chapters: [],
    resources: [],
  }))
}

/**
 * Video service.
 *
 * In mock mode it returns the local fixture; otherwise it calls the configured
 * backend routes. Proposed routes are not yet verified against the API.
 */

export async function listVideos(signal?: AbortSignal): Promise<VideoLecture[]> {
  if (USE_MOCK_API) {
    await delay(200)
    return mockVideoLectures
  }
  const data = await apiClient.get<VideoLecture[]>(endpoints.videos, { signal })
  return data ?? []
}

export async function getVideo(id: string, signal?: AbortSignal): Promise<VideoLecture> {
  if (id.startsWith('local:')) {
    const lecture = (await listLocalVideos(signal)).find(video => video.id === id)
    if (!lecture) throw new ApiErrorException({ status: 404, message: 'This local video was not found.' })
    return lecture
  }
  if (USE_MOCK_API) {
    await delay(250)
    const lecture = findMockLecture(id)
    if (!lecture) {
      throw new ApiErrorException({
        status: 404,
        message: `Lecture "${id}" was not found.`,
      })
    }
    return lecture
  }
  return apiClient.get<VideoLecture>(endpoints.video(id), { signal })
}

export async function getChapters(id: string, signal?: AbortSignal) {
  if (id.startsWith('local:')) return (await getVideo(id, signal)).chapters
  if (USE_MOCK_API) {
    await delay(120)
    const lecture = findMockLecture(id)
    if (!lecture) {
      throw new ApiErrorException({ status: 404, message: `Lecture "${id}" was not found.` })
    }
    return lecture.chapters
  }
  return apiClient.get<VideoLecture['chapters']>(endpoints.videoChapters(id), { signal })
}

/**
 * Resolve the streaming URL for a lecture.
 * In mock mode the lecture's own source URL is used directly.
 */
export function getStreamUrl(id: string): string {
  if (USE_MOCK_API) {
    return findMockLecture(id)?.source.url ?? ''
  }
  return `${API_BASE_URL}${endpoints.videoStream(id)}`
}

/**
 * Import a lecture from a URL.
 *
 * No import is ever claimed as complete here: mock mode reports that the
 * import route is not connected rather than fabricating a result.
 */
export async function importVideoByUrl(
  request: VideoImportRequest,
  signal?: AbortSignal,
): Promise<VideoImportResult> {
  if (USE_MOCK_API) {
    await delay(400)
    throw new ApiErrorException({
      status: 501,
      message:
        'URL import is prepared but not connected in demo mode. No request was sent to a backend.',
      code: 'MOCK_NOT_IMPLEMENTED',
    })
  }
  return apiClient.post<VideoImportResult>(endpoints.videoImport, request, { signal })
}

export async function uploadVideo(
  formData: FormData,
  signal?: AbortSignal,
): Promise<VideoImportResult> {
  if (USE_MOCK_API) {
    await delay(400)
    throw new ApiErrorException({
      status: 501,
      message:
        'Upload is prepared but not connected in demo mode. No request was sent to a backend.',
      code: 'MOCK_NOT_IMPLEMENTED',
    })
  }
  return apiClient.request<VideoImportResult>(endpoints.videoUpload, {
    method: 'POST',
    body: formData,
    signal,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

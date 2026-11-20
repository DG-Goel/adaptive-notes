import { apiClient } from './client'
import { delay } from './mock-support'
import { endpoints, USE_MOCK_API } from '@/config/endpoints'
import { ApiErrorException } from '@/types/api'
import type { VideoTranscript } from '@/types/transcript'
import { findMockTranscript } from '@/mocks/transcripts'

export async function getTranscript(
  videoId: string,
  signal?: AbortSignal,
): Promise<VideoTranscript> {
  if (USE_MOCK_API) {
    await delay(300)
    const transcript = findMockTranscript(videoId)
    if (!transcript) {
      throw new ApiErrorException({
        status: 404,
        message: `No transcript is available for "${videoId}".`,
      })
    }
    return transcript
  }
  return apiClient.get<VideoTranscript>(endpoints.videoTranscript(videoId), { signal })
}

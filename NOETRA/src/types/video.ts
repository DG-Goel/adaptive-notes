/* Lecture, chapter, and video-source domain types. */

/** How a lecture's source URL should be played back in the browser. */
export type VideoSourceKind = 'html5' | 'youtube' | 'unsupported'

export interface VideoSource {
  /** Original source URL supplied by the lecture record. */
  url: string
  /** Human-readable provider label, e.g. "Local preview", "YouTube". */
  provider?: string
}

export type VideoStatus = 'ready' | 'processing' | 'new'

export interface Chapter {
  id: string
  title: string
  /** Start position in seconds. */
  startTime: number
  /** End position in seconds, when known. */
  endTime?: number
  summary?: string
}

export interface VideoResource {
  id: string
  label: string
  kind: 'link' | 'file'
  url?: string
  description?: string
}

export interface VideoLecture {
  id: string
  title: string
  description: string
  course: string
  instructor: string
  /** Total lecture duration in seconds. */
  duration: number
  thumbnailUrl?: string
  source: VideoSource
  status: VideoStatus
  /** ISO date string of the last update. */
  updatedAt: string
  objectives: string[]
  keyConcepts: string[]
  chapters: Chapter[]
  resources: VideoResource[]
  /** True when the playback sample does not match the lecture topic. */
  isPlaybackDemo?: boolean
  /** Explanation shown when the playback sample is a stand-in. */
  playbackNote?: string
}

export interface VideoImportRequest {
  url: string
}

export interface VideoImportResult {
  videoId: string
  status: VideoStatus
}

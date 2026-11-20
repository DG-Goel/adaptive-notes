/* Timestamped transcript domain types. */

export interface TranscriptSegment {
  id: string
  /** Start position in seconds. */
  startTime: number
  /** End position in seconds. */
  endTime: number
  text: string
  speaker?: string
}

export interface VideoTranscript {
  videoId: string
  language: string
  segments: TranscriptSegment[]
}

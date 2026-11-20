import { createContext, useContext, useSyncExternalStore } from 'react'
import type { Chapter } from '@/types/video'
import type { PlaybackAdapter, PlaybackAdapterCallbacks } from '@/lib/playback-adapter'
import type { VideoTimeStore } from '@/lib/video-time-store'

/** Features the attached playback surface actually supports. */
export interface VideoPlayerCapabilities {
  hasCaptions: boolean
  canPictureInPicture: boolean
}

/**
 * Centralized video controller surface.
 *
 * `currentTime` is intentionally NOT part of this value — it is read through
 * `useVideoTime()` so frequent position updates never re-render the whole tree.
 */
export interface VideoPlayerContextValue {
  isPlaying: boolean
  isBuffering: boolean
  isReady: boolean
  error: string | null
  duration: number
  playbackRate: number
  volume: number
  muted: boolean
  activeChapter: Chapter | null
  chapters: Chapter[]
  /**
   * True when the playable media is a stand-in clip, so chapters/transcript
   * timestamps describe the lecture rather than the clip and must be labelled
   * as illustrative.
   */
  isIllustrative: boolean
  capabilities: VideoPlayerCapabilities
  timeStore: VideoTimeStore
  /** Internal bindings used to construct playback adapters. */
  bindings: PlaybackAdapterCallbacks
  attachAdapter(adapter: PlaybackAdapter | null): void
  play(): void
  pause(): void
  togglePlay(): void
  seekTo(seconds: number): void
  seekBy(delta: number): void
  setPlaybackRate(rate: number): void
  setVolume(volume: number): void
  toggleMute(): void
  getBufferedFraction(): number
  setCaptionsEnabled(enabled: boolean): void
  requestPictureInPicture(): void
}

export const VideoPlayerContext = createContext<VideoPlayerContextValue | null>(null)

export function useVideoPlayer(): VideoPlayerContextValue {
  const value = useContext(VideoPlayerContext)
  if (!value) {
    throw new Error('useVideoPlayer must be used inside a VideoPlayerProvider.')
  }
  return value
}

/**
 * Read the shared controller when one is mounted, without requiring it.
 *
 * Used by surfaces (notes, timestamp chips) that live both inside the video
 * workspace and on standalone routes, so they can seek when a player exists
 * and fall back to a deep link when it does not.
 */
export function useVideoPlayerOptional(): VideoPlayerContextValue | null {
  return useContext(VideoPlayerContext)
}

/** Subscribe to the isolated, throttled playback position. */
export function useVideoTime(): number {
  const { timeStore } = useVideoPlayer()
  return useSyncExternalStore(timeStore.subscribe, timeStore.getSnapshot, timeStore.getSnapshot)
}

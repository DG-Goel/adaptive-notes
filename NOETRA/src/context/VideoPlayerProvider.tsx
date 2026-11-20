import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Chapter } from '@/types/video'
import type { PlaybackAdapter, PlaybackAdapterCallbacks } from '@/lib/playback-adapter'
import { createVideoTimeStore } from '@/lib/video-time-store'
import { findChapterIndex } from '@/lib/chapters'
import {
  VideoPlayerContext,
  type VideoPlayerCapabilities,
  type VideoPlayerContextValue,
} from './video-player-context'

interface CoarseState {
  isPlaying: boolean
  isBuffering: boolean
  isReady: boolean
  error: string | null
  duration: number
  playbackRate: number
  volume: number
  muted: boolean
}

const initialState: CoarseState = {
  isPlaying: false,
  isBuffering: false,
  isReady: false,
  error: null,
  duration: 0,
  playbackRate: 1,
  volume: 1,
  muted: false,
}

export interface VideoPlayerProviderProps {
  chapters: Chapter[]
  /** Set when the playable media is a stand-in clip for the described lecture. */
  illustrative?: boolean
  children: ReactNode
}

/**
 * Owns playback state for a learning workspace.
 *
 * Only coarse, infrequent state (play/pause, buffering, duration, chapter) lives
 * in React. Frequent position updates go through the external time store, so
 * switching tabs or scrubbing never re-renders the whole workspace.
 */
export function VideoPlayerProvider({
  chapters,
  illustrative = false,
  children,
}: VideoPlayerProviderProps) {
  const adapterRef = useRef<PlaybackAdapter | null>(null)
  const chaptersRef = useRef<Chapter[]>(chapters)
  const [timeStore] = useState(() => createVideoTimeStore())
  const [state, setState] = useState<CoarseState>(initialState)
  const [capabilities, setCapabilities] = useState<VideoPlayerCapabilities>({
    hasCaptions: false,
    canPictureInPicture: false,
  })
  const [activeChapterIndex, setActiveChapterIndex] = useState(() =>
    findChapterIndex(0, chapters),
  )

  useEffect(() => {
    chaptersRef.current = chapters
  }, [chapters])

  useEffect(() => () => timeStore.dispose(), [timeStore])

  const refreshCapabilities = useCallback(() => {
    const adapter = adapterRef.current
    setCapabilities(
      adapter
        ? { hasCaptions: adapter.hasCaptions(), canPictureInPicture: adapter.canPictureInPicture() }
        : { hasCaptions: false, canPictureInPicture: false },
    )
  }, [])

  const bindings = useMemo<PlaybackAdapterCallbacks>(
    () => ({
      onReady: (duration) => {
        setState((prev) => ({ ...prev, isReady: true, duration, error: null }))
        // Caption tracks and PiP support become known once metadata has loaded.
        refreshCapabilities()
      },
      onDurationChange: (duration) =>
        setState((prev) => (prev.duration === duration ? prev : { ...prev, duration })),
      onTimeUpdate: (time) => {
        timeStore.push(time)
        const index = findChapterIndex(time, chaptersRef.current)
        setActiveChapterIndex((prev) => (prev === index ? prev : index))
      },
      onPlayingChange: (isPlaying) =>
        setState((prev) => (prev.isPlaying === isPlaying ? prev : { ...prev, isPlaying })),
      onBufferingChange: (isBuffering) =>
        setState((prev) => (prev.isBuffering === isBuffering ? prev : { ...prev, isBuffering })),
      onError: (message) =>
        setState((prev) => ({ ...prev, error: message, isPlaying: false, isBuffering: false })),
      onVolumeChange: (volume, muted) => setState((prev) => ({ ...prev, volume, muted })),
      onRateChange: (rate) =>
        setState((prev) => (prev.playbackRate === rate ? prev : { ...prev, playbackRate: rate })),
      onEnded: () => setState((prev) => ({ ...prev, isPlaying: false, isBuffering: false })),
    }),
    [timeStore, refreshCapabilities],
  )

  const attachAdapter = useCallback(
    (adapter: PlaybackAdapter | null) => {
      adapterRef.current = adapter
      setCapabilities(
        adapter
          ? {
              hasCaptions: adapter.hasCaptions(),
              canPictureInPicture: adapter.canPictureInPicture(),
            }
          : { hasCaptions: false, canPictureInPicture: false },
      )
    },
    [],
  )

  const play = useCallback(() => {
    adapterRef.current?.play()
  }, [])

  const pause = useCallback(() => {
    adapterRef.current?.pause()
  }, [])

  const togglePlay = useCallback(() => {
    const adapter = adapterRef.current
    if (!adapter) return
    if (state.isPlaying) adapter.pause()
    else adapter.play()
  }, [state.isPlaying])

  const seekTo = useCallback(
    (seconds: number) => {
      const adapter = adapterRef.current
      if (!adapter) return
      adapter.seekTo(seconds)
      timeStore.push(adapter.getCurrentTime(), true)
    },
    [timeStore],
  )

  const seekBy = useCallback(
    (delta: number) => {
      const adapter = adapterRef.current
      if (!adapter) return
      const target = Math.max(0, adapter.getCurrentTime() + delta)
      adapter.seekTo(target)
      timeStore.push(target, true)
    },
    [timeStore],
  )

  const setPlaybackRate = useCallback((rate: number) => {
    adapterRef.current?.setPlaybackRate(rate)
    setState((prev) => (prev.playbackRate === rate ? prev : { ...prev, playbackRate: rate }))
  }, [])

  const setVolume = useCallback((volume: number) => {
    const clamped = Math.max(0, Math.min(1, volume))
    adapterRef.current?.setVolume(clamped)
    setState((prev) => ({
      ...prev,
      volume: clamped,
      muted: clamped === 0 ? true : prev.muted,
    }))
  }, [])

  const toggleMute = useCallback(() => {
    const nextMuted = !state.muted
    adapterRef.current?.setMuted(nextMuted)
    setState((prev) => ({ ...prev, muted: nextMuted }))
  }, [state.muted])

  const getBufferedFraction = useCallback(
    () => adapterRef.current?.getBufferedFraction() ?? 0,
    [],
  )

  const setCaptionsEnabled = useCallback((enabled: boolean) => {
    adapterRef.current?.setCaptionsEnabled(enabled)
  }, [])

  const requestPictureInPicture = useCallback(() => {
    adapterRef.current?.requestPictureInPicture()
  }, [])

  const value = useMemo<VideoPlayerContextValue>(
    () => ({
      ...state,
      activeChapter:
        activeChapterIndex >= 0 ? chapters[activeChapterIndex] ?? null : null,
      chapters,
      isIllustrative: illustrative,
      capabilities,
      timeStore,
      bindings,
      attachAdapter,
      play,
      pause,
      togglePlay,
      seekTo,
      seekBy,
      setPlaybackRate,
      setVolume,
      toggleMute,
      getBufferedFraction,
      setCaptionsEnabled,
      requestPictureInPicture,
    }),
    [
      state,
      activeChapterIndex,
      chapters,
      illustrative,
      capabilities,
      timeStore,
      bindings,
      attachAdapter,
      play,
      pause,
      togglePlay,
      seekTo,
      seekBy,
      setPlaybackRate,
      setVolume,
      toggleMute,
      getBufferedFraction,
      setCaptionsEnabled,
      requestPictureInPicture,
    ],
  )

  return <VideoPlayerContext.Provider value={value}>{children}</VideoPlayerContext.Provider>
}

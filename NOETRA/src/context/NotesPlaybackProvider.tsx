import { useMemo } from 'react'
import type { ReactNode } from 'react'
import { NotesPlaybackContext } from './notes-playback-context'
import type { NotesPlaybackTarget } from './notes-playback-context'
import { useVideoPlayerOptional } from './video-player-context'

export interface NotesPlaybackProviderProps {
  videoId: string
  children: ReactNode
}

/**
 * Provide the notes tree with a seek target.
 *
 * `seekTo` comes from the shared `VideoPlayerProvider`, so this adds no second
 * controller — it only forwards the existing one to notes components. The value
 * is memoised on the (stable) `seekTo` identity so frequent playback updates
 * never re-render the notes document.
 */
export function NotesPlaybackProvider({ videoId, children }: NotesPlaybackProviderProps) {
  const player = useVideoPlayerOptional()
  const seekTo = player?.seekTo

  const value = useMemo<NotesPlaybackTarget>(() => ({ videoId, seekTo }), [videoId, seekTo])

  return <NotesPlaybackContext.Provider value={value}>{children}</NotesPlaybackContext.Provider>
}

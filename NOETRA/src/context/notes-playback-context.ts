import { createContext, useContext } from 'react'

/**
 * Seek bridge shared by the Notes Studio and the video workspace.
 *
 * Notes rendered standalone (`/notes/:videoId`) have no mounted player, so a
 * timestamp chip becomes a deep link into `/learn/:videoId?t=<seconds>` rather
 * than trying to control a player that does not exist. Inside the workspace the
 * exact same chip seeks the already-mounted shared controller, so there is only
 * ever one playback implementation.
 */
export interface NotesPlaybackTarget {
  videoId: string
  /** Present only while a real player is mounted and can be controlled. */
  seekTo?: (seconds: number) => void
}

export const NotesPlaybackContext = createContext<NotesPlaybackTarget | null>(null)

export function useNotesPlaybackTarget(): NotesPlaybackTarget | null {
  return useContext(NotesPlaybackContext)
}

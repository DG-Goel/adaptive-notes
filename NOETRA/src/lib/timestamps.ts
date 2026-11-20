/** Parsing and labelling for the `[mm:ss]` markers used across notes text. */

import { formatTime } from './format'

/**
 * Read a bracketed `[mm:ss]` or `[hh:mm:ss]` token.
 * Returns `null` for anything that is not a well-formed timestamp, so callers
 * can fall back to rendering the original text.
 */
export function parseTimestamp(token: string): number | null {
  const parts = token.slice(1, -1).split(':').map(Number)
  if (parts.some((part) => !Number.isFinite(part))) return null
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return null
}

/**
 * Label for a timestamp chip. Shares the workspace's time formatting so a chip
 * in the notes and the player transport always show the same value.
 */
export const timestampLabel = formatTime

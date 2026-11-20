import type { VideoSourceKind } from '@/types/video'

export interface ResolvedVideoSource {
  kind: VideoSourceKind
  url: string
  /** Present when `kind === 'youtube'`. */
  youtubeId?: string
  /** Explanation surfaced for unsupported sources. */
  reason?: string
}

const HTML5_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.ogv', '.m4v', '.mov']

function normaliseHost(hostname: string): string {
  return hostname.replace(/^www\./, '').toLowerCase()
}

function extractYouTubeId(url: URL, host: string): string | undefined {
  if (host === 'youtu.be') {
    const id = url.pathname.slice(1).split('/')[0]
    return id || undefined
  }
  const queryId = url.searchParams.get('v')
  if (queryId) return queryId
  const match = url.pathname.match(/^\/(?:embed|shorts|v|live)\/([^/?#]+)/)
  return match?.[1]
}

/**
 * Parse a source string into an absolute URL.
 *
 * Absolute URLs (and `blob:`/`data:` handled separately) pass through directly.
 * Root-relative paths — such as a bundled fixture at `/videos/demo.mp4` — are
 * resolved against the app origin so same-origin assets work without a host.
 */
function parseSourceUrl(url: string): URL | null {
  try {
    return new URL(url)
  } catch {
    if (typeof window !== 'undefined' && url.startsWith('/')) {
      try {
        return new URL(url, window.location.origin)
      } catch {
        return null
      }
    }
    return null
  }
}

/**
 * Classify a raw source URL so the player can pick the right playback surface.
 * Unknown-but-absolute URLs are treated as native media — the player shows a
 * clear error state if the browser cannot actually play them.
 */
export function resolveVideoSource(rawUrl: string | undefined): ResolvedVideoSource {
  const url = rawUrl?.trim() ?? ''
  if (!url) {
    return { kind: 'unsupported', url: '', reason: 'No video source was provided for this lecture.' }
  }

  if (url.startsWith('blob:') || url.startsWith('data:')) {
    return { kind: 'html5', url }
  }

  const parsed = parseSourceUrl(url)
  if (!parsed) {
    return {
      kind: 'unsupported',
      url,
      reason: 'The video source is not a valid absolute URL.',
    }
  }

  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return {
      kind: 'unsupported',
      url,
      reason: `The "${parsed.protocol}" protocol is not supported for video playback.`,
    }
  }

  const host = normaliseHost(parsed.hostname)
  const isYouTube =
    host === 'youtube.com' || host === 'm.youtube.com' || host === 'music.youtube.com' || host === 'youtu.be'

  if (isYouTube) {
    const youtubeId = extractYouTubeId(parsed, host)
    if (!youtubeId) {
      return {
        kind: 'unsupported',
        url,
        reason: 'This YouTube link does not contain a recognisable video id.',
      }
    }
    return { kind: 'youtube', url, youtubeId }
  }

  const path = parsed.pathname.toLowerCase()
  if (HTML5_EXTENSIONS.some((extension) => path.endsWith(extension))) {
    return { kind: 'html5', url }
  }

  // Unknown extension: let the browser try native playback.
  return { kind: 'html5', url }
}

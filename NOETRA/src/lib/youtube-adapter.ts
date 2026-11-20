import type { PlaybackAdapter, PlaybackAdapterCallbacks } from './playback-adapter'

/**
 * YouTube playback adapter.
 *
 * Wraps the official IFrame Player API behind the same `PlaybackAdapter`
 * interface as the native `<video>` adapter, so the workspace controller does
 * not need to know which surface is playing.
 *
 * The IFrame API has no `timeupdate` event, so position is polled while the
 * player is in the PLAYING state only.
 */

interface YouTubePlayer {
  playVideo(): void
  pauseVideo(): void
  seekTo(seconds: number, allowSeekAhead: boolean): void
  setPlaybackRate(rate: number): void
  setVolume(volume: number): void
  mute(): void
  unMute(): void
  getCurrentTime(): number
  getDuration(): number
  getPlayerState(): number
  getVideoLoadedFraction(): number
  destroy(): void
}

interface YouTubePlayerEvent {
  target: YouTubePlayer
  data?: number
}

interface YouTubePlayerOptions {
  videoId: string
  host?: string
  playerVars?: Record<string, number | string>
  events?: {
    onReady?: (event: YouTubePlayerEvent) => void
    onStateChange?: (event: YouTubePlayerEvent) => void
    onError?: (event: YouTubePlayerEvent) => void
  }
}

interface YouTubeApi {
  Player: new (element: HTMLElement, options: YouTubePlayerOptions) => YouTubePlayer
  PlayerState: {
    UNSTARTED: number
    ENDED: number
    PLAYING: number
    PAUSED: number
    BUFFERING: number
    CUED: number
  }
}

declare global {
  interface Window {
    YT?: YouTubeApi
    onYouTubeIframeAPIReady?: () => void
  }
}

const API_SRC = 'https://www.youtube.com/iframe_api'
const SCRIPT_MARKER = 'data-noetra-youtube-api'
const POLL_INTERVAL_MS = 250

let apiPromise: Promise<YouTubeApi> | null = null

function loadYouTubeApi(): Promise<YouTubeApi> {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return Promise.reject(new Error('The YouTube player requires a browser environment.'))
  }
  if (window.YT?.Player) return Promise.resolve(window.YT)
  if (apiPromise) return apiPromise

  apiPromise = new Promise<YouTubeApi>((resolve, reject) => {
    const previous = window.onYouTubeIframeAPIReady
    window.onYouTubeIframeAPIReady = () => {
      previous?.()
      if (window.YT?.Player) resolve(window.YT)
      else reject(new Error('The YouTube player API loaded but did not initialise.'))
    }

    if (!document.querySelector(`script[${SCRIPT_MARKER}]`)) {
      const script = document.createElement('script')
      script.src = API_SRC
      script.async = true
      script.setAttribute(SCRIPT_MARKER, 'true')
      script.addEventListener('error', () => {
        apiPromise = null
        reject(
          new Error('Could not load the YouTube player API — the network may be offline or blocking it.'),
        )
      })
      document.head.appendChild(script)
    }
  })

  return apiPromise
}

function describeYouTubeError(code: number | undefined): string {
  switch (code) {
    case 2:
      return 'The YouTube video id is invalid.'
    case 5:
      return 'This YouTube video cannot be played in the embedded player.'
    case 100:
      return 'This YouTube video is private or has been removed.'
    case 101:
    case 150:
      return 'The video owner does not allow embedded playback.'
    default:
      return 'This YouTube video could not be played.'
  }
}

/**
 * Create an adapter that drives an embedded YouTube player inside `host`.
 * Operations issued before the player is ready are queued and replayed.
 */
export function createYouTubeAdapter(
  host: HTMLElement,
  videoId: string,
  callbacks: PlaybackAdapterCallbacks,
): PlaybackAdapter {
  const mount = document.createElement('div')
  mount.className = 'h-full w-full'
  host.appendChild(mount)

  let player: YouTubePlayer | null = null
  let destroyed = false
  let playing = false
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let duration = 0
  let playbackRate = 1
  let volume = 1
  let muted = false
  let currentTime = 0
  const queued: ((active: YouTubePlayer) => void)[] = []

  const withPlayer = (action: (active: YouTubePlayer) => void) => {
    if (player) action(player)
    else queued.push(action)
  }

  const stopPolling = () => {
    if (pollTimer !== null) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  const startPolling = () => {
    if (pollTimer !== null) return
    pollTimer = setInterval(() => {
      if (!player || destroyed) return
      const time = player.getCurrentTime()
      if (Number.isFinite(time)) {
        currentTime = time
        callbacks.onTimeUpdate(time)
      }
    }, POLL_INTERVAL_MS)
  }

  const handleStateChange = (state: number) => {
    const YT = window.YT
    if (!YT) return
    if (state === YT.PlayerState.PLAYING) {
      playing = true
      callbacks.onPlayingChange(true)
      callbacks.onBufferingChange(false)
      startPolling()
    } else if (state === YT.PlayerState.BUFFERING) {
      callbacks.onBufferingChange(true)
    } else if (state === YT.PlayerState.PAUSED || state === YT.PlayerState.CUED) {
      playing = false
      stopPolling()
      callbacks.onPlayingChange(false)
      callbacks.onBufferingChange(false)
    } else if (state === YT.PlayerState.ENDED) {
      playing = false
      stopPolling()
      callbacks.onPlayingChange(false)
      callbacks.onBufferingChange(false)
      callbacks.onEnded()
    }
  }

  loadYouTubeApi()
    .then((YT) => {
      if (destroyed) return
      player = new YT.Player(mount, {
        videoId,
        playerVars: {
          controls: 0,
          modestbranding: 1,
          rel: 0,
          playsinline: 1,
          disablekb: 1,
          iv_load_policy: 3,
        },
        events: {
          onReady: (event) => {
            if (destroyed) return
            duration = event.target.getDuration() || 0
            event.target.setVolume(volume * 100)
            if (muted) event.target.mute()
            event.target.setPlaybackRate(playbackRate)
            callbacks.onReady(duration)
            callbacks.onDurationChange(duration)
            callbacks.onVolumeChange(volume, muted)
            queued.splice(0).forEach((action) => action(event.target))
          },
          onStateChange: (event) => {
            if (typeof event.data === 'number') handleStateChange(event.data)
          },
          onError: (event) => callbacks.onError(describeYouTubeError(event.data)),
        },
      })
    })
    .catch((error: unknown) => {
      callbacks.onError(
        error instanceof Error ? error.message : 'The YouTube player could not be loaded.',
      )
    })

  return {
    play() {
      withPlayer((active) => active.playVideo())
    },
    pause() {
      const at = player?.getCurrentTime()
      withPlayer((active) => active.pauseVideo())
      if (typeof at === 'number' && Number.isFinite(at)) currentTime = at
    },
    seekTo(seconds) {
      if (!Number.isFinite(seconds)) return
      const target = Math.max(0, duration > 0 ? Math.min(seconds, duration) : seconds)
      currentTime = target
      withPlayer((active) => active.seekTo(target, true))
      callbacks.onTimeUpdate(target)
    },
    setPlaybackRate(rate) {
      playbackRate = rate
      withPlayer((active) => active.setPlaybackRate(rate))
    },
    setVolume(next) {
      volume = Math.max(0, Math.min(1, next))
      if (volume > 0) muted = false
      withPlayer((active) => active.setVolume(volume * 100))
      callbacks.onVolumeChange(volume, muted)
    },
    setMuted(next) {
      muted = next
      withPlayer((active) => {
        if (next) active.mute()
        else active.unMute()
      })
      callbacks.onVolumeChange(volume, muted)
    },
    getCurrentTime() {
      const live = player?.getCurrentTime()
      if (typeof live === 'number' && Number.isFinite(live)) currentTime = live
      return currentTime
    },
    getDuration() {
      const live = player?.getDuration()
      if (typeof live === 'number' && Number.isFinite(live) && live > 0) duration = live
      return duration
    },
    getBufferedFraction() {
      const loaded = player?.getVideoLoadedFraction()
      return typeof loaded === 'number' && Number.isFinite(loaded) ? Math.min(loaded, 1) : 0
    },
    hasCaptions() {
      // The IFrame API only exposes captions through an optional module that is
      // not loaded here, so the toggle stays unavailable rather than pretending.
      return false
    },
    setCaptionsEnabled() {
      // No-op: see `hasCaptions`.
    },
    canPictureInPicture() {
      return false
    },
    requestPictureInPicture() {
      // The embedded player cannot be promoted to Picture-in-Picture.
    },
    destroy() {
      destroyed = true
      stopPolling()
      queued.length = 0
      if (playing) player?.pauseVideo()
      playing = false
      try {
        player?.destroy()
      } catch {
        // The player may already have been torn down by the API.
      }
      player = null
      mount.remove()
    },
  }
}

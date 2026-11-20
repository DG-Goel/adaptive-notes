/**
 * Playback adapter abstraction.
 *
 * A single adapter interface lets the workspace drive either a native
 * `<video>` element or an embedded YouTube player through the same controller.
 * Adapters never hold application state — they report everything back through
 * the callbacks object so the provider stays the single source of truth.
 */

export interface PlaybackAdapterCallbacks {
  onReady(duration: number): void
  onDurationChange(duration: number): void
  onTimeUpdate(time: number): void
  onPlayingChange(isPlaying: boolean): void
  onBufferingChange(isBuffering: boolean): void
  onError(message: string): void
  onVolumeChange(volume: number, muted: boolean): void
  onRateChange(rate: number): void
  onEnded(): void
}

export interface PlaybackAdapter {
  play(): void
  pause(): void
  seekTo(seconds: number): void
  setPlaybackRate(rate: number): void
  setVolume(volume: number): void
  setMuted(muted: boolean): void
  getCurrentTime(): number
  getDuration(): number
  /** Buffered fraction in the range 0–1. */
  getBufferedFraction(): number
  hasCaptions(): boolean
  setCaptionsEnabled(enabled: boolean): void
  canPictureInPicture(): boolean
  requestPictureInPicture(): void
  destroy(): void
}

function describeMediaError(media: HTMLVideoElement): string {
  const code = media.error?.code
  switch (code) {
    case 1:
      return 'Playback was aborted.'
    case 2:
      return 'A network error interrupted the video download.'
    case 3:
      return 'The video could not be decoded — the file may be corrupt.'
    case 4:
      return 'This video source or format is not supported by your browser.'
    default:
      return 'The video could not be played.'
  }
}

function bufferedFraction(media: HTMLVideoElement): number {
  const { buffered, duration } = media
  if (!duration || buffered.length === 0) return 0
  for (let index = buffered.length - 1; index >= 0; index -= 1) {
    const start = buffered.start(index)
    const end = buffered.end(index)
    if (media.currentTime >= start && media.currentTime <= end) {
      return Math.min(end / duration, 1)
    }
  }
  return Math.min(buffered.end(buffered.length - 1) / duration, 1)
}

/** Adapter backed by a native HTML5 `<video>` element. */
export function createHtml5Adapter(
  media: HTMLVideoElement,
  callbacks: PlaybackAdapterCallbacks,
): PlaybackAdapter {
  const handleLoadedMetadata = () => callbacks.onReady(media.duration || 0)
  const handleDurationChange = () => callbacks.onDurationChange(media.duration || 0)
  const handleTimeUpdate = () => callbacks.onTimeUpdate(media.currentTime)
  const handlePlay = () => callbacks.onPlayingChange(true)
  const handlePlaying = () => callbacks.onBufferingChange(false)
  const handlePause = () => callbacks.onPlayingChange(false)
  const handleWaiting = () => callbacks.onBufferingChange(true)
  const handleCanPlay = () => callbacks.onBufferingChange(false)
  const handleEnded = () => callbacks.onEnded()
  const handleError = () => callbacks.onError(describeMediaError(media))
  const handleVolumeChange = () => callbacks.onVolumeChange(media.volume, media.muted)
  const handleRateChange = () => callbacks.onRateChange(media.playbackRate)

  media.addEventListener('loadedmetadata', handleLoadedMetadata)
  media.addEventListener('durationchange', handleDurationChange)
  media.addEventListener('timeupdate', handleTimeUpdate)
  media.addEventListener('play', handlePlay)
  media.addEventListener('playing', handlePlaying)
  media.addEventListener('pause', handlePause)
  media.addEventListener('waiting', handleWaiting)
  media.addEventListener('canplay', handleCanPlay)
  media.addEventListener('ended', handleEnded)
  media.addEventListener('error', handleError)
  media.addEventListener('volumechange', handleVolumeChange)
  media.addEventListener('ratechange', handleRateChange)

  const textTracks = media.textTracks

  return {
    play() {
      const result = media.play()
      if (result && typeof result.catch === 'function') {
        result.catch((error: unknown) => {
          if (error instanceof DOMException && error.name === 'AbortError') return
          callbacks.onError('Playback could not start. Press play again to retry.')
        })
      }
    },
    pause() {
      media.pause()
    },
    seekTo(seconds) {
      if (!Number.isFinite(seconds)) return
      media.currentTime = Math.max(0, Math.min(seconds, media.duration || seconds))
      callbacks.onTimeUpdate(media.currentTime)
    },
    setPlaybackRate(rate) {
      media.playbackRate = rate
    },
    setVolume(volume) {
      media.volume = Math.max(0, Math.min(1, volume))
    },
    setMuted(muted) {
      media.muted = muted
    },
    getCurrentTime() {
      return media.currentTime
    },
    getDuration() {
      return media.duration || 0
    },
    getBufferedFraction() {
      return bufferedFraction(media)
    },
    hasCaptions() {
      return textTracks !== undefined && textTracks.length > 0
    },
    setCaptionsEnabled(enabled) {
      if (!textTracks) return
      for (let index = 0; index < textTracks.length; index += 1) {
        const track = textTracks[index]
        if (!track) continue
        track.mode = enabled ? 'showing' : 'hidden'
      }
    },
    canPictureInPicture() {
      return typeof document !== 'undefined' && document.pictureInPictureEnabled === true
    },
    requestPictureInPicture() {
      if (typeof media.requestPictureInPicture !== 'function') return
      void media.requestPictureInPicture().catch(() => undefined)
    },
    destroy() {
      media.removeEventListener('loadedmetadata', handleLoadedMetadata)
      media.removeEventListener('durationchange', handleDurationChange)
      media.removeEventListener('timeupdate', handleTimeUpdate)
      media.removeEventListener('play', handlePlay)
      media.removeEventListener('playing', handlePlaying)
      media.removeEventListener('pause', handlePause)
      media.removeEventListener('waiting', handleWaiting)
      media.removeEventListener('canplay', handleCanPlay)
      media.removeEventListener('ended', handleEnded)
      media.removeEventListener('error', handleError)
      media.removeEventListener('volumechange', handleVolumeChange)
      media.removeEventListener('ratechange', handleRateChange)
      media.pause()
    },
  }
}

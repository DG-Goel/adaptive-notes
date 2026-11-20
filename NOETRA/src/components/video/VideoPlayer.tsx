import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import {
  Captions,
  Gauge,
  Loader2,
  Maximize,
  Minimize,
  Pause,
  PictureInPicture2,
  Play,
  RotateCcw,
  SkipBack,
  SkipForward,
  TriangleAlert,
  Volume1,
  Volume2,
  VolumeX,
} from 'lucide-react'
import { VideoTimeline } from './VideoTimeline'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useVideoPlayer, useVideoTime } from '@/context/video-player-context'
import { createHtml5Adapter } from '@/lib/playback-adapter'
import { createYouTubeAdapter } from '@/lib/youtube-adapter'
import { resolveVideoSource } from '@/lib/video-source'
import { formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { VideoLecture } from '@/types/video'

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

/** True when a key event originated from a text-entry surface. */
function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (tag === 'INPUT') return (target as HTMLInputElement).type !== 'range'
  return target.isContentEditable
}

interface ControlButtonProps {
  label: string
  onClick(): void
  disabled?: boolean
  active?: boolean
  children: ReactNode
}

function ControlButton({ label, onClick, disabled, active, children }: ControlButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          disabled={disabled}
          className={cn(
            'inline-flex h-9 w-9 items-center justify-center rounded-lg text-foreground/80 transition-colors',
            'hover:bg-muted hover:text-foreground',
            'disabled:pointer-events-none disabled:opacity-40',
            active && 'bg-accent/10 text-accent hover:bg-accent/15 hover:text-accent',
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}

export interface VideoPlayerProps {
  lecture: VideoLecture
  className?: string
}

/**
 * The lecture playback surface.
 *
 * Owns the media element (native `<video>` or an embedded YouTube player),
 * creates the matching playback adapter, and drives everything through the
 * shared `VideoPlayerProvider` controller. The element stays mounted while the
 * learning tabs switch, so playback never restarts.
 */
export function VideoPlayer({ lecture, className }: VideoPlayerProps) {
  const resolved = useMemo(() => resolveVideoSource(lecture.source.url), [lecture.source.url])
  const {
    isPlaying,
    isBuffering,
    isReady,
    error,
    duration,
    playbackRate,
    volume,
    muted,
    capabilities,
    activeChapter,
    bindings,
    attachAdapter,
    togglePlay,
    seekBy,
    setPlaybackRate,
    setVolume,
    toggleMute,
    setCaptionsEnabled,
    requestPictureInPicture,
  } = useVideoPlayer()
  const currentTime = useVideoTime()

  const containerRef = useRef<HTMLDivElement>(null)
  const mediaRef = useRef<HTMLVideoElement>(null)
  const youTubeHostRef = useRef<HTMLDivElement>(null)
  const [reloadToken, setReloadToken] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [captionsEnabled, setCaptionsEnabledState] = useState(false)

  const isHtml5 = resolved.kind === 'html5'
  const isYouTube = resolved.kind === 'youtube'

  // Create / tear down the native media adapter.
  useEffect(() => {
    if (!isHtml5) return
    const media = mediaRef.current
    if (!media) return
    const adapter = createHtml5Adapter(media, bindings)
    attachAdapter(adapter)
    return () => {
      adapter.destroy()
      attachAdapter(null)
    }
  }, [isHtml5, resolved.url, bindings, attachAdapter, reloadToken])

  // Create / tear down the YouTube adapter.
  useEffect(() => {
    if (!isYouTube || !resolved.youtubeId) return
    const host = youTubeHostRef.current
    if (!host) return
    const adapter = createYouTubeAdapter(host, resolved.youtubeId, bindings)
    attachAdapter(adapter)
    return () => {
      adapter.destroy()
      attachAdapter(null)
    }
  }, [isYouTube, resolved.youtubeId, bindings, attachAdapter, reloadToken])

  useEffect(() => {
    setCaptionsEnabled(captionsEnabled)
  }, [captionsEnabled, setCaptionsEnabled])

  useEffect(() => {
    const handleChange = () => setIsFullscreen(document.fullscreenElement === containerRef.current)
    document.addEventListener('fullscreenchange', handleChange)
    return () => document.removeEventListener('fullscreenchange', handleChange)
  }, [])

  const toggleFullscreen = useCallback(() => {
    const element = containerRef.current
    if (!element) return
    if (document.fullscreenElement === element) {
      void document.exitFullscreen().catch(() => undefined)
      return
    }
    void element.requestFullscreen().catch(() => undefined)
  }, [])

  // Keyboard shortcuts — deliberately skipped while typing in any input,
  // textarea, or the tutor chat so typing never controls playback.
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return
      if (isTypingTarget(event.target)) return
      switch (event.key) {
        case ' ':
        case 'k':
        case 'K':
          event.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
          event.preventDefault()
          seekBy(-5)
          break
        case 'ArrowRight':
          event.preventDefault()
          seekBy(5)
          break
        case 'm':
        case 'M':
          event.preventDefault()
          toggleMute()
          break
        case 'f':
        case 'F':
          event.preventDefault()
          toggleFullscreen()
          break
        default:
          break
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [togglePlay, seekBy, toggleMute, toggleFullscreen])

  const canInteract = resolved.kind !== 'unsupported'
  const showPlayOverlay = canInteract && !error && isReady && !isPlaying && !isBuffering

  const volumeIcon =
    muted || volume === 0 ? (
      <VolumeX className="h-4 w-4" />
    ) : volume < 0.5 ? (
      <Volume1 className="h-4 w-4" />
    ) : (
      <Volume2 className="h-4 w-4" />
    )

  return (
    <div
      ref={containerRef}
      className={cn(
        'group/player overflow-hidden rounded-2xl border border-border bg-card shadow-soft',
        isFullscreen && 'flex h-full flex-col rounded-none',
        className,
      )}
    >
      <div
        className={cn('relative w-full bg-black', isFullscreen ? 'flex-1' : 'aspect-video')}
        onClick={canInteract ? togglePlay : undefined}
        role={canInteract ? 'button' : undefined}
        aria-label={canInteract ? 'Toggle playback' : undefined}
      >
        {isHtml5 && (
          <video
            key={reloadToken}
            ref={mediaRef}
            src={resolved.url}
            poster={lecture.thumbnailUrl}
            preload="metadata"
            playsInline
            className="h-full w-full cursor-pointer object-contain"
          />
        )}

        {isYouTube && <div key={reloadToken} ref={youTubeHostRef} className="h-full w-full" />}

        {resolved.kind === 'unsupported' && (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3 px-6 text-center">
            <TriangleAlert className="h-7 w-7 text-amber-400" />
            <p className="max-w-sm text-sm text-white/80">
              {resolved.reason ?? 'This lecture source cannot be played in the browser.'}
            </p>
          </div>
        )}

        {/* Chapter + source chips */}
        <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-2 p-3">
          {activeChapter && canInteract && (
            <span className="max-w-[60%] truncate rounded-full bg-black/55 px-3 py-1 text-[11px] font-medium text-white backdrop-blur">
              {activeChapter.title}
            </span>
          )}
          {lecture.isPlaybackDemo && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="pointer-events-auto ml-auto rounded-full bg-black/55 px-3 py-1 text-[11px] font-medium text-amber-200 backdrop-blur">
                  Playback demo
                </span>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                {lecture.playbackNote ??
                  'The bundled sample clip does not match this lecture’s topic.'}
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {isBuffering && canInteract && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <Loader2 className="h-9 w-9 animate-spin text-white" />
          </div>
        )}

        {showPlayOverlay && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/90 text-foreground shadow-elevated transition-transform duration-200 group-hover/player:scale-105">
              <Play className="ml-0.5 h-7 w-7" />
            </span>
          </div>
        )}

        {error && canInteract && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/80 px-6 text-center">
            <TriangleAlert className="h-7 w-7 text-amber-400" />
            <p className="max-w-sm text-sm text-white/85">{error}</p>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                setReloadToken((token) => token + 1)
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-white/20"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Reload player
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 border-t border-border bg-card px-3 py-3">
        <VideoTimeline />

        <div className="flex items-center gap-1.5">
          <ControlButton
            label={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
            onClick={togglePlay}
            disabled={!canInteract}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </ControlButton>

          <ControlButton
            label="Back 10 seconds"
            onClick={() => seekBy(-10)}
            disabled={!canInteract}
          >
            <SkipBack className="h-4 w-4" />
          </ControlButton>

          <ControlButton
            label="Forward 10 seconds"
            onClick={() => seekBy(10)}
            disabled={!canInteract}
          >
            <SkipForward className="h-4 w-4" />
          </ControlButton>

          <span className="ml-1 font-mono text-xs tabular-nums text-muted-foreground">
            {formatTime(currentTime)}
            <span className="mx-1 text-muted-foreground/50">/</span>
            {formatTime(duration)}
          </span>

          <div className="ml-auto flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  aria-label="Playback speed"
                  className="inline-flex h-9 items-center gap-1 rounded-lg px-2 text-foreground/80 transition-colors hover:bg-muted hover:text-foreground"
                >
                  <Gauge className="h-4 w-4" />
                  <span className="font-mono text-[11px] tabular-nums">{playbackRate}×</span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Playback speed</DropdownMenuLabel>
                <DropdownMenuRadioGroup
                  value={String(playbackRate)}
                  onValueChange={(value) => setPlaybackRate(Number(value))}
                >
                  {PLAYBACK_RATES.map((rate) => (
                    <DropdownMenuRadioItem key={rate} value={String(rate)}>
                      {rate}×
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>

            <ControlButton
              label={
                capabilities.hasCaptions
                  ? captionsEnabled
                    ? 'Turn captions off'
                    : 'Turn captions on'
                  : 'Captions are not available for this source'
              }
              onClick={() => setCaptionsEnabledState((enabled) => !enabled)}
              disabled={!capabilities.hasCaptions}
              active={captionsEnabled && capabilities.hasCaptions}
            >
              <Captions className="h-4 w-4" />
            </ControlButton>

            <ControlButton
              label={
                capabilities.canPictureInPicture
                  ? 'Picture in picture'
                  : 'Picture in picture is not available for this source'
              }
              onClick={requestPictureInPicture}
              disabled={!capabilities.canPictureInPicture}
            >
              <PictureInPicture2 className="h-4 w-4" />
            </ControlButton>

            <div className="hidden items-center gap-1 sm:flex">
              <ControlButton
                label={muted ? 'Unmute (M)' : 'Mute (M)'}
                onClick={toggleMute}
                disabled={!canInteract}
              >
                {volumeIcon}
              </ControlButton>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={muted ? 0 : volume}
                onChange={(event) => setVolume(Number(event.target.value))}
                disabled={!canInteract}
                aria-label="Volume"
                style={{ accentColor: 'hsl(var(--accent))' }}
                className="h-1 w-20 cursor-pointer appearance-none rounded-full bg-muted-foreground/30 disabled:cursor-not-allowed"
              />
            </div>

            <ControlButton
              label={isFullscreen ? 'Exit full screen (F)' : 'Full screen (F)'}
              onClick={toggleFullscreen}
              disabled={!canInteract}
            >
              {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
            </ControlButton>
          </div>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  BookOpen,
  BrainCircuit,
  Map,
  Maximize,
  MessageSquare,
  Minimize,
  Plus,
  RefreshCw,
  TriangleAlert,
} from 'lucide-react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { PageTransition } from '@/components/common/PageTransition'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { VideoPlayer } from '@/components/video/VideoPlayer'
import { ChapterNavigation } from '@/components/video/ChapterNavigation'
import { LearningTabs } from '@/components/video/LearningTabs'
import { OverviewPanel } from '@/components/video/panels/OverviewPanel'
import { TutorSidebar } from '@/components/video/TutorSidebar'
import { VideoImportDialog } from '@/components/video/VideoImportDialog'
import { VideoPlayerProvider } from '@/context/VideoPlayerProvider'
import { useVideoPlayer } from '@/context/video-player-context'
import { useLecture } from '@/hooks/use-lecture-queries'
import { formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { VideoLecture } from '@/types/video'
import { VideoQuizDialog } from '@/components/quiz/VideoQuizDialog'

const TUTOR_MIN = 300
const TUTOR_MAX = 560
const TUTOR_DEFAULT = 384
const TUTOR_COLLAPSED = 48

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(query).matches,
  )

  useEffect(() => {
    const mql = window.matchMedia(query)
    const handleChange = (event: MediaQueryListEvent) => setMatches(event.matches)
    mql.addEventListener('change', handleChange)
    return () => mql.removeEventListener('change', handleChange)
  }, [query])

  return matches
}

/**
 * Apply a `?t=<seconds>` deep link to the shared player.
 *
 * Timestamp chips in the Notes Studio link here, so a note timestamp opens the
 * lecture at the right moment. The seek runs once per link, after the media
 * reports it is ready, and the query parameter is then removed so a later
 * reload or tab switch does not yank playback back to the old position.
 */
function useDeepLinkSeek() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { isReady, seekTo } = useVideoPlayer()
  const appliedRef = useRef(false)
  const rawTarget = searchParams.get('t')

  useEffect(() => {
    if (appliedRef.current || !isReady || rawTarget === null) return
    const seconds = Number(rawTarget)
    if (!Number.isFinite(seconds) || seconds < 0) return
    appliedRef.current = true
    seekTo(seconds)
    const next = new URLSearchParams(searchParams)
    next.delete('t')
    setSearchParams(next, { replace: true })
  }, [isReady, rawTarget, searchParams, seekTo, setSearchParams])
}

interface WorkspaceProps {
  lecture: VideoLecture
}

function LectureWorkspace({ lecture }: WorkspaceProps) {
  useDeepLinkSeek()
  const { seekTo, duration } = useVideoPlayer()
  const isDesktop = useMediaQuery('(min-width: 1024px)')
  const [focusMode, setFocusMode] = useState(false)
  const [tutorCollapsed, setTutorCollapsed] = useState(false)
  const [tutorWidth, setTutorWidth] = useState(TUTOR_DEFAULT)
  const [isResizing, setIsResizing] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [mobileTutorOpen, setMobileTutorOpen] = useState(false)
  const dragRef = useRef<{ startX: number; startWidth: number } | null>(null)

  // Drag the divider to resize the tutor panel.
  useEffect(() => {
    if (!isResizing) return
    const handleMove = (event: PointerEvent) => {
      const drag = dragRef.current
      if (!drag) return
      setTutorWidth(clamp(drag.startWidth + (drag.startX - event.clientX), TUTOR_MIN, TUTOR_MAX))
    }
    const handleUp = () => {
      setIsResizing(false)
      dragRef.current = null
    }
    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', handleUp)
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', handleUp)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [isResizing])

  const startDrag = (event: React.PointerEvent) => {
    dragRef.current = { startX: event.clientX, startWidth: tutorWidth }
    setIsResizing(true)
  }

  const handleDividerKey = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      setTutorWidth((width) => clamp(width + 24, TUTOR_MIN, TUTOR_MAX))
    } else if (event.key === 'ArrowRight') {
      event.preventDefault()
      setTutorWidth((width) => clamp(width - 24, TUTOR_MIN, TUTOR_MAX))
    }
  }

  const showTutorPanel = isDesktop && !focusMode
  const tutorEffectiveWidth = tutorCollapsed ? TUTOR_COLLAPSED : tutorWidth

  return (
    <div className="space-y-4">
      <header className="sticky top-0 z-20 -mx-4 flex h-16 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/75 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <Link
          to="/library"
          className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Library</span>
        </Link>

        <div className="min-w-0 flex-1">
          <p className="truncate text-[11px] font-medium uppercase tracking-[0.16em] text-accent">
            {lecture.course} · {lecture.instructor}
          </p>
          <h1 className="truncate font-serif text-base font-medium tracking-tight text-foreground sm:text-lg">
            {lecture.title}
          </h1>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <span className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
            <BookOpen className="h-3.5 w-3.5" />
            {lecture.chapters.length} chapters · {formatTime(lecture.duration)}
          </span>

          <Badge variant={lecture.status === 'ready' ? 'accent' : 'outline'} className="text-[10px]">
            {lecture.status === 'ready' ? 'Ready' : lecture.status}
          </Badge>

          {lecture.id.startsWith('local:') ? (
            <VideoQuizDialog key={lecture.id} video={lecture.id.slice('local:'.length)} onSeek={seekTo} duration={duration || lecture.duration} />
          ) : <Link to={`/quiz/${lecture.id}`}>
            <SecondaryButton size="sm" title="Generate quiz">
              <BrainCircuit className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">Quiz</span>
            </SecondaryButton>
          </Link>}

          <Link to={`/knowledge/${lecture.id}`}>
            <SecondaryButton size="sm" title="View knowledge map">
              <Map className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">Map</span>
            </SecondaryButton>
          </Link>

          <SecondaryButton size="sm" onClick={() => setImportOpen(true)}>
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Add lecture</span>
          </SecondaryButton>

          {isDesktop && (
            <SecondaryButton
              size="sm"
              onClick={() => setFocusMode((value) => !value)}
              aria-pressed={focusMode}
              className={cn(focusMode && 'border-accent/40 bg-accent/10 text-accent')}
            >
              {focusMode ? <Minimize className="h-3.5 w-3.5" /> : <Maximize className="h-3.5 w-3.5" />}
              <span className="hidden md:inline">Focus</span>
            </SecondaryButton>
          )}

          {!isDesktop && (
            <SecondaryButton size="sm" onClick={() => setMobileTutorOpen(true)} aria-label="Open AI tutor">
              <MessageSquare className="h-3.5 w-3.5" />
            </SecondaryButton>
          )}
        </div>
      </header>

      <div className="flex items-start">
        <div className="min-w-0 flex-1 space-y-5">
          <VideoPlayer lecture={lecture} />
          <OverviewPanel lecture={lecture} duration={duration} />
          <ChapterNavigation defaultOpen={false} />
          <LearningTabs lecture={lecture} videoId={lecture.id} stickyTopClassName="top-16" />
        </div>

        {showTutorPanel && (
          <>
            {!tutorCollapsed && (
              <div
                role="separator"
                aria-orientation="vertical"
                aria-label="Resize AI tutor panel"
                aria-valuenow={tutorWidth}
                aria-valuemin={TUTOR_MIN}
                aria-valuemax={TUTOR_MAX}
                tabIndex={0}
                onPointerDown={startDrag}
                onKeyDown={handleDividerKey}
                className={cn(
                  'mx-1.5 hidden w-1 shrink-0 cursor-col-resize self-stretch rounded-full transition-colors lg:block',
                  isResizing ? 'bg-accent/50' : 'bg-transparent hover:bg-accent/30',
                )}
              />
            )}
            <aside
              className="sticky top-20 hidden h-[calc(100vh-7rem)] shrink-0 self-start lg:flex"
              style={{ width: tutorEffectiveWidth }}
            >
              <TutorSidebar
                videoId={lecture.id}
                collapsed={tutorCollapsed}
                onToggleCollapse={() => setTutorCollapsed((value) => !value)}
                className="w-full"
              />
            </aside>
          </>
        )}
      </div>

      <VideoImportDialog open={importOpen} onOpenChange={setImportOpen} />

      <Dialog open={mobileTutorOpen} onOpenChange={setMobileTutorOpen}>
        <DialogContent className="max-w-md p-0">
          <DialogTitle className="sr-only">AI tutor</DialogTitle>
          <div className="h-[72vh] p-3">
            <TutorSidebar videoId={lecture.id} className="h-full" />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export function VideoWorkspacePage() {
  const { videoId } = useParams()
  const { data: lecture, isPending, isError, error, refetch } = useLecture(videoId)

  if (!videoId) {
    return (
      <PageTransition>
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="No lecture selected"
          description="Choose a lecture from your library to open the workspace."
          action={
            <Link to="/library">
              <PrimaryButton>
                <ArrowLeft className="h-4 w-4" /> Back to library
              </PrimaryButton>
            </Link>
          }
        />
      </PageTransition>
    )
  }

  if (isPending) {
    return (
      <PageTransition>
        <div className="space-y-4">
          <LoadingSkeleton variant="text" className="max-w-md" />
          <LoadingSkeleton variant="card" />
        </div>
      </PageTransition>
    )
  }

  if (isError || !lecture) {
    return (
      <PageTransition>
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="Lecture unavailable"
          description={error instanceof Error ? error.message : 'This lecture could not be loaded.'}
          action={
            <div className="flex items-center gap-2">
              <SecondaryButton onClick={() => void refetch()}>
                <RefreshCw className="h-3.5 w-3.5" /> Try again
              </SecondaryButton>
              <Link to="/library">
                <PrimaryButton variant="outline">
                  <ArrowLeft className="h-4 w-4" /> Back to library
                </PrimaryButton>
              </Link>
            </div>
          }
        />
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      {/* The provider wraps the workspace so the player stays mounted across tab switches. */}
      <VideoPlayerProvider chapters={lecture.chapters} illustrative={lecture.isPlaybackDemo}>
        <LectureWorkspace lecture={lecture} />
      </VideoPlayerProvider>
    </PageTransition>
  )
}

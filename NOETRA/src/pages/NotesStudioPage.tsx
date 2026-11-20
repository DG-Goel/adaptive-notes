import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  BrainCircuit,
  Check,
  Columns3,
  Copy,
  FileText,
  ListTree,
  Loader2,
  Map as MapIcon,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Pencil,
  Printer,
  RefreshCw,
  Save,
  Sparkles,
  TriangleAlert,
  Undo2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { PageTransition } from '@/components/common/PageTransition'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { NotesDocumentRenderer } from '@/components/notes/NotesDocumentRenderer'
import { NotesOutline } from '@/components/notes/NotesOutline'
import { NotesContextPanel } from '@/components/notes/NotesContextPanel'
import { NotesSearchBar } from '@/components/notes/NotesSearchBar'
import { NotesEditorDialog } from '@/components/notes/NotesEditorDialog'
import { NotesExportMenu } from '@/components/notes/NotesExportMenu'
import { NotesGenerationDialog } from '@/components/notes/NotesGenerationControls'
import { VideoPlayerProvider } from '@/context/VideoPlayerProvider'
import { usePersistentState } from '@/hooks/use-persistent-state'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import {
  useLecture,
  useNoteDocument,
  useNotesStatus,
  useSaveNoteDocument,
} from '@/hooks/use-lecture-queries'
import { buildOutline, searchNoteDocument } from '@/lib/notes/outline'
import { noteDocumentToMarkdown } from '@/lib/notes/markdown'
import { cn } from '@/lib/utils'
import { USE_MOCK_API } from '@/config/endpoints'
import type { EditableNoteBlock, NoteBlock, NoteSection } from '@/types/notes'
import type { VideoLecture } from '@/types/video'

/**
 * The Notes Studio.
 *
 * Three responsive areas over one structured document: a hierarchical outline,
 * the notes themselves rendered by the shared document renderer, and the
 * learning context. Playback is not reimplemented — the studio mounts the same
 * `VideoPlayer` component inside the same provider, so a timestamp chip in the
 * notes seeks the real player, and every section also offers a deep link into
 * the lecture workspace.
 */

type ReadingMode = 'standard' | 'comfortable' | 'focus'
type StudioView = 'outline' | 'notes' | 'context'
type SaveState = 'clean' | 'dirty' | 'saving' | 'saved' | 'error' | 'conflict'

const WIDTH_CLASSES: Record<ReadingMode, string> = {
  standard: 'max-w-3xl',
  comfortable: 'max-w-2xl',
  focus: 'max-w-xl',
}

const READING_MODES: { value: ReadingMode; label: string }[] = [
  { value: 'standard', label: 'Standard' },
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'focus', label: 'Focus' },
]

interface DraftState {
  sections: NoteSection[]
  /** Version the edit was based on, so a stale save can be refused. */
  baseVersion: number
}

/** Track which section the reader is actually on, inside any scroll container. */
function useActiveSection(sectionIds: string[], enabled: boolean): string | undefined {
  const [active, setActive] = useState<string | undefined>(undefined)

  useEffect(() => {
    if (!enabled || sectionIds.length === 0) return
    const observed = new Map<string, HTMLElement>()
    for (const id of sectionIds) {
      const element = document.querySelector<HTMLElement>(`[data-section-id="${id}"]`)
      if (element) observed.set(id, element)
    }
    if (observed.size === 0) return

    const tops = new Map<string, number>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = (entry.target as HTMLElement).dataset.sectionId
          if (!id) continue
          tops.set(id, entry.isIntersecting ? entry.boundingClientRect.top : Number.POSITIVE_INFINITY)
        }
        let best: string | undefined
        let bestTop = Number.POSITIVE_INFINITY
        for (const id of sectionIds) {
          const top = tops.get(id)
          if (top === undefined || !Number.isFinite(top)) continue
          if (top < bestTop) {
            bestTop = top
            best = id
          }
        }
        if (best) setActive((previous) => (previous === best ? previous : best))
      },
      { rootMargin: '-150px 0px -55% 0px', threshold: 0 },
    )

    observed.forEach((element) => observer.observe(element))
    return () => observer.disconnect()
  }, [sectionIds, enabled])

  return active
}

function NotesStudioBody({ lecture, videoId }: { lecture: VideoLecture; videoId: string }) {
  const { data, isPending, isError, error, refetch } = useNoteDocument(videoId)

  const [mode, setMode] = useState<'read' | 'edit'>('read')
  const [readingMode, setReadingMode] = usePersistentState<ReadingMode>(
    'noetra:notes:reading-mode',
    'standard',
  )
  const [view, setView] = useState<StudioView>('notes')
  const [outlineCollapsed, setOutlineCollapsed] = useState(false)
  const [contextCollapsed, setContextCollapsed] = useState(false)
  const [collapsedSections, setCollapsedSections] = useState<ReadonlySet<string>>(() => new Set())
  const [collapsedGroups, setCollapsedGroups] = useState<ReadonlySet<string>>(() => new Set())
  const [query, setQuery] = useState('')
  const [matchIndex, setMatchIndex] = useState(0)
  const [draft, setDraft] = useState<DraftState | null>(null)
  const [editorBlock, setEditorBlock] = useState<EditableNoteBlock | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [generationOpen, setGenerationOpen] = useState(false)
  const [jobStarted, setJobStarted] = useState(false)

  const save = useSaveNoteDocument()
  const { copied, copy } = useCopyToClipboard()
  const status = useNotesStatus(videoId, { enabled: jobStarted, poll: jobStarted })

  const displayDocument = useMemo(
    () => (draft && data ? { ...data, sections: draft.sections } : data),
    [data, draft],
  )

  const outline = useMemo(() => buildOutline(displayDocument), [displayDocument])
  const sectionIds = useMemo(() => outline.map((entry) => entry.id), [outline])

  const matches = useMemo(() => searchNoteDocument(displayDocument, query), [displayDocument, query])
  const safeIndex = matches.length === 0 ? 0 : Math.min(matchIndex, matches.length - 1)
  const activeMatch = matches[safeIndex]
  const highlightedBlockId = activeMatch?.blockId

  // Focus mode collapses to a single column, so it must win over the view state.
  const effectiveView: StudioView = readingMode === 'focus' ? 'notes' : view
  const showOutline = readingMode !== 'focus' && !outlineCollapsed
  const showContext = readingMode !== 'focus' && !contextCollapsed

  const activeSectionId = useActiveSection(sectionIds, Boolean(displayDocument))

  /**
   * A section holding the current search match is always shown, so a hit can
   * never stay hidden behind a collapsed heading. Derived during render rather
   * than written into state, so revealing it costs no extra render pass.
   */
  const visibleCollapsedSections = useMemo(() => {
    if (!activeMatch || !collapsedSections.has(activeMatch.sectionId)) return collapsedSections
    const next = new Set(collapsedSections)
    next.delete(activeMatch.sectionId)
    return next
  }, [collapsedSections, activeMatch])

  // Scroll the block the reader searched for into view once the document shows it.
  useEffect(() => {
    if (!activeMatch) return
    document
      .querySelector<HTMLElement>(`[data-block-id="${activeMatch.blockId}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [activeMatch])

  const navigateToSection = useCallback((sectionId: string) => {
    if (readingMode === 'focus') setView('notes')
    document
      .querySelector<HTMLElement>(`[data-section-id="${sectionId}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [readingMode])

  const toggleSection = useCallback((sectionId: string) => {
    setCollapsedSections((previous) => {
      const next = new Set(previous)
      if (next.has(sectionId)) next.delete(sectionId)
      else next.add(sectionId)
      return next
    })
  }, [])

  const toggleGroup = useCallback((sectionId: string) => {
    setCollapsedGroups((previous) => {
      const next = new Set(previous)
      if (next.has(sectionId)) next.delete(sectionId)
      else next.add(sectionId)
      return next
    })
  }, [])

  const openEditor = useCallback((block: EditableNoteBlock) => {
    setEditorBlock(block)
    setEditorOpen(true)
  }, [])

  /** Replace exactly one block; every other block keeps its position. */
  const applyBlockChange = useCallback(
    (updated: NoteBlock) => {
      if (!data) return
      const baseSections = draft?.sections ?? data.sections
      const sections = baseSections.map((section) => ({
        ...section,
        blocks: section.blocks.map((block) => (block.id === updated.id ? updated : block)),
      }))
      setDraft({ sections, baseVersion: draft?.baseVersion ?? data.version })
      setEditorOpen(false)
      setEditorBlock(null)
    },
    [data, draft],
  )

  const conflict = save.data?.conflict === true

  const handleSave = () => {
    if (!data || !draft || save.isPending) return
    save.mutate(
      {
        documentId: data.id,
        videoId,
        version: draft.baseVersion,
        title: data.title,
        sections: draft.sections,
      },
      {
        onSuccess: (result) => {
          if (!result.conflict) setDraft(null)
        },
      },
    )
  }

  const handleDiscard = () => {
    setDraft(null)
    save.reset()
  }

  const saveState: SaveState = save.isPending
    ? 'saving'
    : save.error
      ? 'error'
      : conflict
        ? 'conflict'
        : draft
          ? 'dirty'
          : save.isSuccess
            ? 'saved'
            : 'clean'

  if (isPending) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton variant="text" className="max-w-md" />
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  if (isError || !data || !displayDocument) {
    return (
      <EmptyState
        icon={<TriangleAlert className="h-5 w-5" />}
        title="Notes unavailable"
        description={
          error instanceof Error
            ? error.message
            : 'No note document could be loaded for this lecture.'
        }
        action={
          <div className="flex items-center gap-2">
            <SecondaryButton onClick={() => void refetch()}>
              <RefreshCw className="h-3.5 w-3.5" /> Try again
            </SecondaryButton>
            <Link to={`/learn/${videoId}`}>
              <PrimaryButton variant="outline">
                <ArrowLeft className="h-4 w-4" /> Open lecture
              </PrimaryButton>
            </Link>
          </div>
        }
      />
    )
  }

  const statusLabel: Record<SaveState, string> = {
    clean: USE_MOCK_API ? 'Demo editing — changes stay in this session' : 'Up to date',
    dirty: 'Unsaved changes',
    saving: 'Saving…',
    saved: USE_MOCK_API ? 'Applied to the local demo document' : 'Saved',
    error: 'Save failed',
    conflict: 'A newer version exists on the server',
  }

  return (
    <div className="space-y-4">
      <header className="no-print sticky top-0 z-20 -mx-4 border-b border-border bg-background/90 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/75 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <div className="flex h-16 items-center gap-3">
          <Link
            to={`/learn/${videoId}`}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Lecture</span>
          </Link>

          <div className="min-w-0 flex-1">
            <p className="truncate text-[11px] font-medium uppercase tracking-[0.16em] text-accent">
              Notes Studio · {lecture.course}
            </p>
            <h1 className="truncate font-serif text-base font-medium tracking-tight text-foreground sm:text-lg">
              {lecture.title}
            </h1>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {data.isDemonstration && (
              <Badge variant="outline" className="hidden text-[10px] md:inline-flex">
                Demonstration document
              </Badge>
            )}

            <span
              role="status"
              className={cn(
                'hidden items-center gap-1.5 text-[11px] font-medium lg:inline-flex',
                saveState === 'error' || saveState === 'conflict'
                  ? 'text-destructive'
                  : saveState === 'dirty'
                    ? 'text-amber-700'
                    : 'text-muted-foreground',
              )}
            >
              {saveState === 'saving' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : saveState === 'saved' ? (
                <Check className="h-3 w-3" />
              ) : saveState === 'dirty' ? (
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500" aria-hidden />
              ) : null}
              {statusLabel[saveState]}
            </span>

            <Link to={`/quiz/${videoId}`}>
              <SecondaryButton
                size="sm"
                className="hidden sm:inline-flex"
                title="Practice with quiz"
              >
                <BrainCircuit className="h-3.5 w-3.5" />
                <span className="hidden lg:inline">Quiz</span>
              </SecondaryButton>
            </Link>

            <Link to={`/knowledge/${videoId}`}>
              <SecondaryButton
                size="sm"
                className="hidden sm:inline-flex"
                title="Explore knowledge map"
              >
                <MapIcon className="h-3.5 w-3.5" />
                <span className="hidden lg:inline">Map</span>
              </SecondaryButton>
            </Link>

            {draft && (
              <div className="flex items-center gap-1">
                <SecondaryButton size="sm" onClick={handleDiscard} disabled={save.isPending}>
                  <Undo2 className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Discard</span>
                </SecondaryButton>
                <PrimaryButton size="sm" onClick={handleSave} loading={save.isPending}>
                  <Save className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Save</span>
                </PrimaryButton>
              </div>
            )}

            <SecondaryButton
              size="sm"
              onClick={() => setMode((value) => (value === 'read' ? 'edit' : 'read'))}
              aria-pressed={mode === 'edit'}
              className={cn(mode === 'edit' && 'border-accent/40 bg-accent/10 text-accent')}
            >
              <Pencil className="h-3.5 w-3.5" />
              <span className="hidden md:inline">{mode === 'edit' ? 'Read' : 'Edit'}</span>
            </SecondaryButton>

            <SecondaryButton size="sm" onClick={() => void copy(noteDocumentToMarkdown(displayDocument))}>
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              <span className="hidden lg:inline">{copied ? 'Copied' : 'Copy notes'}</span>
            </SecondaryButton>

            <NotesExportMenu videoId={videoId} document={displayDocument} className="hidden sm:flex" />

            <PrimaryButton size="sm" onClick={() => setGenerationOpen(true)}>
              <Sparkles className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Generate</span>
            </PrimaryButton>
          </div>
        </div>

        <div className="flex h-12 items-center gap-2">
          <NotesSearchBar
            query={query}
            onQueryChange={(value) => {
              setQuery(value)
              setMatchIndex(0)
            }}
            matchCount={matches.length}
            activeIndex={safeIndex}
            onPrevious={() => setMatchIndex((index) => (matches.length === 0 ? 0 : (index - 1 + matches.length) % matches.length))}
            onNext={() => setMatchIndex((index) => (matches.length === 0 ? 0 : (index + 1) % matches.length))}
            className="min-w-0 flex-1 xl:max-w-md"
          />

          <div className="ml-auto flex shrink-0 items-center gap-1.5">
            <div className="flex items-center rounded-lg border border-border p-0.5" role="group" aria-label="Reading width">
              {READING_MODES.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setReadingMode(option.value)}
                  aria-pressed={readingMode === option.value}
                  className={cn(
                    'rounded-md px-2 py-1 text-[11px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    readingMode === option.value
                      ? 'bg-accent/10 text-accent'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="flex items-center rounded-lg border border-border p-0.5 xl:hidden" role="group" aria-label="Panel">
              {(
                [
                  { value: 'outline' as StudioView, label: 'Outline', icon: ListTree },
                  { value: 'notes' as StudioView, label: 'Notes', icon: FileText },
                  { value: 'context' as StudioView, label: 'Panels', icon: Columns3 },
                ]
              ).map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setView(option.value)}
                  aria-pressed={effectiveView === option.value}
                  className={cn(
                    'inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    effectiveView === option.value
                      ? 'bg-accent/10 text-accent'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  <option.icon className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{option.label}</span>
                </button>
              ))}
            </div>

            <div className="hidden items-center gap-1 xl:flex">
              <button
                type="button"
                onClick={() => setOutlineCollapsed((value) => !value)}
                aria-pressed={outlineCollapsed}
                aria-label={outlineCollapsed ? 'Show outline' : 'Hide outline'}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {outlineCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
              </button>
              <button
                type="button"
                onClick={() => setContextCollapsed((value) => !value)}
                aria-pressed={contextCollapsed}
                aria-label={contextCollapsed ? 'Show context panel' : 'Hide context panel'}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {contextCollapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                aria-label="Print notes"
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Printer className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex items-start gap-5">
        {showOutline && (
          <aside
            className={cn(
              'no-print w-full shrink-0 xl:w-60',
              effectiveView !== 'outline' && 'hidden xl:block',
            )}
          >
            <div className="rounded-2xl border border-border bg-card p-3 shadow-soft xl:sticky xl:top-32 xl:flex xl:h-[calc(100vh-9.5rem)] xl:flex-col">
              <NotesOutline
                entries={outline}
                activeSectionId={activeSectionId}
                collapsedGroups={collapsedGroups}
                onToggleGroup={toggleGroup}
                onNavigate={navigateToSection}
                className="min-h-0 flex-1"
              />
            </div>
          </aside>
        )}

        <div
          className={cn(
            'print-region min-w-0 flex-1',
            effectiveView !== 'notes' && 'hidden xl:block',
          )}
        >
          <NotesDocumentRenderer
            document={displayDocument}
            highlightedBlockId={highlightedBlockId}
            collapsedSections={visibleCollapsedSections}
            onToggleCollapse={toggleSection}
            editing={mode === 'edit'}
            onEditBlock={openEditor}
            showHeader
            widthClass={WIDTH_CLASSES[readingMode]}
          />
        </div>

        {showContext && (
          <aside
            className={cn(
              'no-print w-full shrink-0 xl:w-[19rem]',
              effectiveView !== 'context' && 'hidden xl:block',
            )}
          >
            <div className="xl:sticky xl:top-32 xl:max-h-[calc(100vh-9.5rem)] xl:overflow-y-auto xl:pr-1">
              <NotesContextPanel
                lecture={lecture}
                document={displayDocument}
                activeSectionId={activeSectionId}
                onNavigateSection={navigateToSection}
                status={status.data}
                statusPending={status.isPending}
                statusError={status.error}
              />
            </div>
          </aside>
        )}
      </div>

      <NotesEditorDialog
        block={editorBlock}
        open={editorOpen}
        onOpenChange={(open) => {
          setEditorOpen(open)
          if (!open) setEditorBlock(null)
        }}
        onApply={applyBlockChange}
      />

      <NotesGenerationDialog
        open={generationOpen}
        onOpenChange={setGenerationOpen}
        videoId={videoId}
        document={displayDocument}
        status={status.data}
        statusPending={status.isPending}
        statusError={status.error}
        onJobStarted={() => setJobStarted(true)}
      />
    </div>
  )
}

export function NotesStudioPage() {
  const { videoId } = useParams()
  const { data: lecture, isPending, isError, error, refetch } = useLecture(videoId)

  if (!videoId) {
    return (
      <PageTransition>
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="No lecture selected"
          description="Open a lecture from your library to read its notes."
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
      {/* The shared playback architecture, reused rather than reimplemented. */}
      <VideoPlayerProvider chapters={lecture.chapters} illustrative={lecture.isPlaybackDemo}>
        <NotesStudioBody lecture={lecture} videoId={videoId} />
      </VideoPlayerProvider>
    </PageTransition>
  )
}

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eraser, Maximize2, PanelRightOpen, Sparkles } from 'lucide-react'
import { MessageList } from '@/components/tutor/MessageList'
import { MessageComposer } from '@/components/tutor/MessageComposer'
import { useTutorConversation } from '@/context/tutor-conversation-context'
import { cn } from '@/lib/utils'

export interface TutorSidebarProps {
  videoId: string
  collapsed?: boolean
  onToggleCollapse?(): void
  className?: string
}

/**
 * Compact AI tutor panel for the video workspace.
 *
 * Reuses the shared `TutorConversationProvider` state and the same message /
 * composer components as the full Tutor page, so a conversation started here
 * continues seamlessly at `/tutor`. New messages are scoped to this lecture's
 * video context.
 *
 * Video playback is never interrupted: the tutor only reads the shared player
 * context for seek actions and never touches playback state.
 */
export function TutorSidebar({
  videoId,
  collapsed = false,
  onToggleCollapse,
  className,
}: TutorSidebarProps) {
  const navigate = useNavigate()
  const {
    activeConversation,
    draft,
    isSending,
    newConversation,
    selectConversation,
    conversations,
    setDraft,
    sendMessage,
    retry,
    regenerate,
    stop,
  } = useTutorConversation()

  // Ensure there is an active conversation scoped to this lecture.
  useEffect(() => {
    const existing = conversations.find((c) => c.videoId === videoId && !c.isDemo)
    if (existing) {
      selectConversation(existing.id)
      return
    }
    if (!activeConversation || activeConversation.videoId !== videoId || activeConversation.isDemo) {
      newConversation({ type: 'video', videoId }, `Tutor · ${videoId}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId])

  const ready = activeConversation?.videoId === videoId && !activeConversation.isDemo
  const messages = ready ? activeConversation.messages.filter((message) => !message.isDemo) : []

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={onToggleCollapse}
        aria-label="Expand AI tutor"
        className={cn(
          'flex h-full w-12 flex-col items-center gap-3 rounded-2xl border border-border bg-card py-4 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground',
          className,
        )}
      >
        <PanelRightOpen className="h-4 w-4" />
        <span className="text-[11px] font-medium [writing-mode:vertical-rl]">AI Tutor</span>
      </button>
    )
  }

  return (
    <section
      className={cn(
        'flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-soft',
        className,
      )}
    >
      <header className="flex items-center gap-2 border-b border-border px-4 py-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Sparkles className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="font-serif text-base font-medium tracking-tight text-foreground">
            AI Tutor
          </h2>
          <p className="truncate text-[11px] text-muted-foreground">
            Uses this lecture’s generated notes
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/tutor')}
          aria-label="Open full Tutor workspace"
          title="Open full Tutor"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Collapse AI tutor"
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <PanelRightOpen className="h-4 w-4 rotate-180" />
          </button>
        )}
      </header>

      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        <span className="text-sm text-muted-foreground">This lecture</span>
        <button
          type="button"
          onClick={() => newConversation({ type: 'video', videoId }, `Tutor · ${videoId}`)}
          aria-label="New conversation"
          className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Eraser className="h-3.5 w-3.5" />
        </button>
      </div>

      <MessageList
        messages={messages}
        context={{ type: 'video', videoId }}
        isSending={isSending}
        onSelectSuggestion={(q) => setDraft(q)}
        onRetry={retry}
        onRegenerate={regenerate}
      />

      <MessageComposer
        value={draft}
        onChange={setDraft}
        onSubmit={() => ready && draft.trim() && sendMessage(draft)}
        onStop={stop}
        isSending={isSending}
        placeholder="Ask a question about this lecture…"
      />
    </section>
  )
}

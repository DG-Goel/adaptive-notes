import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react'
import { ConversationList } from './ConversationList'
import { MessageList } from './MessageList'
import { MessageComposer } from './MessageComposer'
import { ContextSelector } from './ContextSelector'
import { ExplanationModeSelector } from './ExplanationModeSelector'
import { useTutorConversation } from '@/context/tutor-conversation-context'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface TutorWorkspaceProps {
  /** When true the left conversation list is hidden (compact sidebar mode). */
  hideConversationList?: boolean
  /** When true the right context panel is hidden by default. */
  defaultContextCollapsed?: boolean
  className?: string
}

/**
 * The AI Tutor conversation workspace.
 *
 * Three-column responsive layout: conversation list | conversation | learning
 * context panel. On narrow screens the context panel collapses and the
 * conversation list becomes a drawer. All state comes from the shared
 * `TutorConversationProvider` so the same conversation is visible from both
 * the full page and the compact sidebar.
 */
export function TutorWorkspace({
  hideConversationList = false,
  defaultContextCollapsed = false,
  className,
}: TutorWorkspaceProps) {
  const {
    conversations,
    activeConversationId,
    activeConversation,
    draft,
    context,
    preferences,
    isSending,
    error,
    newConversation,
    selectConversation,
    deleteConversation,
    setDraft,
    setContext,
    setPreferences,
    sendMessage,
    retry,
    regenerate,
    stop,
  } = useTutorConversation()

  const navigate = useNavigate()
  const [contextCollapsed, setContextCollapsed] = useState(defaultContextCollapsed)
  const [listOpen, setListOpen] = useState(false)

  const messages = activeConversation?.messages ?? []
  const videoId = activeConversation?.videoId

  const handleSubmit = () => {
    if (!draft.trim()) return
    sendMessage(draft)
  }

  return (
    <div className={cn('flex h-full min-h-0 overflow-hidden', className)}>
      {/* Left: conversation list (desktop) */}
      {!hideConversationList && (
        <aside className="hidden w-64 shrink-0 border-r border-border bg-card/50 md:block">
          <ConversationList
            conversations={conversations}
            activeId={activeConversationId}
            onSelect={selectConversation}
            onNew={() => newConversation()}
            onDelete={deleteConversation}
          />
        </aside>
      )}

      {/* Mobile drawer toggle */}
      {!hideConversationList && (
        <button
          type="button"
          onClick={() => setListOpen(true)}
          className="absolute left-3 top-3 z-10 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground md:hidden"
          aria-label="Open conversations"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      )}

      {/* Mobile drawer */}
      {listOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setListOpen(false)}
            aria-hidden
          />
          <div className="absolute left-0 top-0 h-full w-72 bg-card shadow-xl">
            <ConversationList
              conversations={conversations}
              activeId={activeConversationId}
              onSelect={(id) => {
                selectConversation(id)
                setListOpen(false)
              }}
              onNew={() => {
                newConversation()
                setListOpen(false)
              }}
              onDelete={deleteConversation}
            />
          </div>
        </div>
      )}

      {/* Center: conversation */}
      <section className="flex min-w-0 flex-1 flex-col bg-background">
        <header className="flex items-center gap-2 border-b border-border px-4 py-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <Sparkles className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="truncate font-serif text-base font-medium tracking-tight text-foreground">
              {activeConversation?.title ?? 'AI Tutor'}
            </h2>
            <p className="truncate text-[11px] text-muted-foreground">
              {activeConversation?.isDemo ? 'Demo replies · not a live model' : 'Grounded in your content'}
            </p>
          </div>
          <ContextSelector context={context} onChange={setContext} videoId={videoId} />
          <ExplanationModeSelector preferences={preferences} onChange={setPreferences} />
        </header>

        <MessageList
          messages={messages}
          context={context}
          isSending={isSending}
          onSelectSuggestion={(q) => setDraft(q)}
          onRetry={retry}
          onRegenerate={regenerate}
        />

        {error && (
          <div className="mx-4 mb-2 flex items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/5 px-3 py-2">
            <p className="min-w-0 flex-1 text-xs text-foreground">{error}</p>
          </div>
        )}

        <MessageComposer
          value={draft}
          onChange={setDraft}
          onSubmit={handleSubmit}
          onStop={stop}
          isSending={isSending}
          placeholder="Ask a question about this lecture…"
        />
      </section>

      {/* Right: learning context panel */}
      {!contextCollapsed ? (
        <aside className="hidden w-72 shrink-0 border-l border-border bg-card/50 lg:block">
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-border px-3 py-2">
              <h3 className="text-xs font-semibold text-foreground">Learning context</h3>
              <button
                type="button"
                onClick={() => setContextCollapsed(true)}
                aria-label="Collapse context panel"
                className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 text-xs text-muted-foreground">
              {videoId ? (
                <div className="space-y-3">
                  <div>
                    <p className="font-medium text-foreground">Selected lecture</p>
                    <p>{videoId}</p>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Active context</p>
                    <Badge variant="outline" className="mt-1">
                      {context.type}
                    </Badge>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/notes/${videoId}`)}
                    className="text-accent hover:underline"
                  >
                    Open notes →
                  </button>
                </div>
              ) : (
                <p>No lecture selected. Start from a video or notes page to add context.</p>
              )}
            </div>
          </div>
        </aside>
      ) : (
        <button
          type="button"
          onClick={() => setContextCollapsed(false)}
          aria-label="Expand context panel"
          className="hidden w-8 shrink-0 items-center justify-center border-l border-border bg-card/50 text-muted-foreground hover:bg-muted lg:flex"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

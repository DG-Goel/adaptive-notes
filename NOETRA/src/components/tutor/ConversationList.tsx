import { useMemo, useState } from 'react'
import { MessageSquarePlus, Search, Trash2 } from 'lucide-react'
import { conversationStorage } from '@/services/api/tutor'
import { cn } from '@/lib/utils'
import type { TutorConversation } from '@/types/tutor'

export interface ConversationListProps {
  conversations: TutorConversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
  className?: string
}

function groupByTime(conversations: TutorConversation[]): { label: string; items: TutorConversation[] }[] {
  const now = Date.now()
  const day = 24 * 60 * 60 * 1000
  const groups: Record<string, TutorConversation[]> = {
    Today: [],
    'Previous 7 days': [],
    'Previous 30 days': [],
    Older: [],
  }

  for (const conversation of conversations) {
    const age = now - new Date(conversation.updatedAt).getTime()
    if (age < day) groups['Today'].push(conversation)
    else if (age < 7 * day) groups['Previous 7 days'].push(conversation)
    else if (age < 30 * day) groups['Previous 30 days'].push(conversation)
    else groups['Older'].push(conversation)
  }

  return Object.entries(groups)
    .filter(([, items]) => items.length > 0)
    .map(([label, items]) => ({ label, items }))
}

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  className,
}: ConversationListProps) {
  const [query, setQuery] = useState('')
  const [confirmId, setConfirmId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    if (!query.trim()) return conversations
    const q = query.toLowerCase()
    return conversations.filter((c) => c.title.toLowerCase().includes(q))
  }, [conversations, query])

  const grouped = useMemo(() => groupByTime(filtered), [filtered])

  const contextLabel = (conversation: TutorConversation): string => {
    switch (conversation.context.type) {
      case 'general':
        return 'General'
      case 'video':
        return 'Video'
      case 'chapter':
        return 'Chapter'
      case 'timestamp':
        return 'Clip'
      case 'notes':
        return 'Notes'
    }
  }

  return (
    <div className={cn('flex h-full flex-col', className)}>
      <div className="flex items-center gap-2 border-b border-border p-3">
        <button
          type="button"
          onClick={onNew}
          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-xs font-medium text-accent-foreground transition-colors hover:bg-accent/90"
        >
          <MessageSquarePlus className="h-3.5 w-3.5" />
          New conversation
        </button>
      </div>

      <div className="border-b border-border p-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search conversations"
            aria-label="Search conversations"
            className="w-full rounded-lg border border-input bg-background py-1.5 pl-8 pr-2 text-xs outline-none placeholder:text-muted-foreground focus-visible:border-accent/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {grouped.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">
            No conversations yet.
          </p>
        ) : (
          grouped.map((group) => (
            <div key={group.label} className="mb-3">
              <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((conversation) => {
                  const active = conversation.id === activeId
                  const confirming = confirmId === conversation.id
                  return (
                    <li key={conversation.id}>
                      <div
                        className={cn(
                          'group flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors',
                          active ? 'bg-accent/10 text-accent' : 'hover:bg-muted',
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => onSelect(conversation.id)}
                          className="min-w-0 flex-1"
                        >
                          <p className="truncate text-xs font-medium">{conversation.title}</p>
                          <p className="truncate text-[10px] text-muted-foreground">
                            {contextLabel(conversation)} · {conversation.messages.length} messages
                          </p>
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmId(confirming ? null : conversation.id)}
                          aria-label="Delete conversation"
                          className="shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                      {confirming && (
                        <div className="ml-1 mb-1 rounded-lg border border-destructive/30 bg-destructive/5 p-2">
                          <p className="mb-1.5 text-[11px] text-foreground">
                            Delete this conversation?
                          </p>
                          <div className="flex gap-1.5">
                            <button
                              type="button"
                              onClick={() => {
                                onDelete(conversation.id)
                                setConfirmId(null)
                              }}
                              className="rounded bg-destructive px-2 py-1 text-[10px] font-medium text-destructive-foreground hover:bg-destructive/90"
                            >
                              Delete
                            </button>
                            <button
                              type="button"
                              onClick={() => setConfirmId(null)}
                              className="rounded bg-muted px-2 py-1 text-[10px] font-medium text-foreground hover:bg-muted/80"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-border px-3 py-2">
        <p className="text-[10px] text-muted-foreground">{conversationStorage.label}</p>
      </div>
    </div>
  )
}

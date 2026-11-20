import { useEffect, useRef } from 'react'
import { MessageBubble } from './MessageBubble'
import { SuggestedQuestions } from './SuggestedQuestions'
import type { TutorContext, TutorMessage } from '@/types/tutor'

export interface MessageListProps {
  messages: TutorMessage[]
  context: TutorContext
  isSending: boolean
  onSelectSuggestion: (question: string) => void
  onRetry?: () => void
  onRegenerate?: () => void
}

/**
 * Scrollable list of conversation messages.
 *
 * Auto-scrolls to the latest message only when the user is already near the
 * bottom — if they are reading history, the scroll position is preserved.
 */
export function MessageList({
  messages,
  context,
  isSending,
  onSelectSuggestion,
  onRetry,
  onRegenerate,
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const nearBottomRef = useRef(true)

  const handleScroll = () => {
    const node = scrollRef.current
    if (!node) return
    const distanceFromBottom = node.scrollHeight - node.scrollTop - node.clientHeight
    nearBottomRef.current = distanceFromBottom < 120
  }

  useEffect(() => {
    if (!nearBottomRef.current) return
    const node = scrollRef.current
    if (!node) return
    node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' })
  }, [messages.length, isSending])

  if (messages.length === 0) {
    return (
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-5">
          <div className="rounded-2xl border border-dashed border-border bg-muted/30 p-5 text-center">
            <p className="font-serif text-lg font-medium tracking-tight text-foreground">
              Ask anything about this lecture
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Answers cite the lecture timeline so you can jump straight to the
              moment they come from.
            </p>
          </div>
          <SuggestedQuestions context={context} onSelect={onSelectSuggestion} />
        </div>
      </div>
    )
  }

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 py-4"
    >
      <ul className="mx-auto max-w-3xl space-y-5">
        {messages.map((message, index) => {
          const isLast = index === messages.length - 1
          return (
            <MessageBubble
              key={message.id}
              message={message}
              onRetry={isLast && message.error ? onRetry : undefined}
              onRegenerate={isLast && message.role === 'assistant' && !message.error ? onRegenerate : undefined}
            />
          )
        })}
        {isSending && (
          <MessageBubble message={{ id: 'pending', role: 'assistant', content: '', createdAt: '', pending: true }} />
        )}
      </ul>
    </div>
  )
}

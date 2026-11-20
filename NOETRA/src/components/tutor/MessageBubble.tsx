import { memo, useState } from 'react'
import { Bot, Check, Copy, RefreshCw, TriangleAlert, User } from 'lucide-react'
import { MarkdownBlock } from '@/components/notes/MarkdownBlock'
import { SourceCitationList } from './SourceCitation'
import { cn } from '@/lib/utils'
import type { TutorMessage } from '@/types/tutor'

export interface MessageBubbleProps {
  message: TutorMessage
  onRetry?: () => void
  onRegenerate?: () => void
}

/**
 * A single conversation message.
 *
 * User messages are compact. Assistant messages render Markdown (including
 * KaTeX math, syntax-highlighted code, and tables) through the existing
 * `MarkdownBlock` — no raw HTML is ever injected. Failed assistant turns show
 * the error with a retry action.
 */
export const MessageBubble = memo(function MessageBubble({
  message,
  onRetry,
  onRegenerate,
}: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  if (message.pending) {
    return (
      <li className="flex gap-2.5">
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Bot className="h-4 w-4" />
        </span>
        <span className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-muted px-3.5 py-3">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/60" />
        </span>
      </li>
    )
  }

  return (
    <li className={cn('flex gap-2.5', isUser && 'justify-end')}>
      {!isUser && (
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Bot className="h-4 w-4" />
        </span>
      )}
      {isUser && (
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
          <User className="h-4 w-4" />
        </span>
      )}

      <div className={cn('min-w-0 max-w-[85%] space-y-2', isUser && 'flex flex-col items-end')}>
        {message.error ? (
          <div className="flex items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/5 px-3 py-2">
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-foreground">{message.error}</p>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-accent hover:underline"
                >
                  <RefreshCw className="h-3 w-3" /> Try again
                </button>
              )}
            </div>
          </div>
        ) : isUser ? (
          <div className="rounded-2xl rounded-br-md bg-accent px-3.5 py-2.5 text-sm leading-relaxed text-accent-foreground">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (
          <div className="rounded-2xl rounded-bl-md bg-muted/40 px-4 py-3">
            <MarkdownBlock content={message.content} className="prose-sm max-w-none" />
          </div>
        )}

        {!isUser && !message.error && (
          <div className="flex flex-wrap items-center gap-1.5">
            {message.isDemo && (
              <span className="rounded-full border border-border bg-background px-2 py-0.5 text-[10px] text-muted-foreground">
                Demo reply
              </span>
            )}
            {message.citations && message.citations.length > 0 && (
              <SourceCitationList citations={message.citations} />
            )}
            <button
              type="button"
              onClick={handleCopy}
              aria-label="Copy answer"
              className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            {onRegenerate && (
              <button
                type="button"
                onClick={onRegenerate}
                aria-label="Regenerate answer"
                className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <RefreshCw className="h-3 w-3" /> Regenerate
              </button>
            )}
          </div>
        )}
      </div>
    </li>
  )
})

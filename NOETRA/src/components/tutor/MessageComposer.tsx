import { useEffect, useRef } from 'react'
import { SendHorizontal, Square } from 'lucide-react'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { cn } from '@/lib/utils'

export interface MessageComposerProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onStop?: () => void
  isSending: boolean
  placeholder?: string
  className?: string
}

/**
 * Auto-growing message composer.
 *
 * Enter sends, Shift+Enter inserts a newline. The textarea resizes up to a
 * maximum height while typing. While a request is in flight the send button
 * becomes a stop button.
 */
export function MessageComposer({
  value,
  onChange,
  onSubmit,
  onStop,
  isSending,
  placeholder = 'Ask a question…',
  className,
}: MessageComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-grow the textarea to fit its content, capped at 10rem.
  useEffect(() => {
    const node = textareaRef.current
    if (!node) return
    node.style.height = 'auto'
    node.style.height = `${Math.min(node.scrollHeight, 160)}px`
  }, [value])

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (isSending) return
    onSubmit()
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!isSending) onSubmit()
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cn('border-t border-border p-3', className)}>
      <div className="flex items-end gap-2 rounded-xl border border-input bg-background px-3 py-2 focus-within:border-accent/50 focus-within:ring-2 focus-within:ring-ring/30">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={placeholder}
          aria-label="Ask the AI tutor"
          className="max-h-40 flex-1 resize-none bg-transparent text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
        />
        {isSending && onStop ? (
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop generating"
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground transition-colors hover:bg-muted/80"
          >
            <Square className="h-3.5 w-3.5" />
          </button>
        ) : (
          <PrimaryButton
            type="submit"
            size="sm"
            disabled={!value.trim()}
            aria-label="Send message"
          >
            <SendHorizontal className="h-3.5 w-3.5" />
          </PrimaryButton>
        )}
      </div>
      <p className="mt-1.5 text-[11px] text-muted-foreground">
        Enter to send · Shift+Enter for a new line
      </p>
    </form>
  )
}

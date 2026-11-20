import { Sparkles } from 'lucide-react'
import { notesSuggestedPrompts, suggestedTutorPrompts } from '@/mocks/tutor'
import { cn } from '@/lib/utils'
import { USE_MOCK_API } from '@/config/endpoints'
import type { TutorContext } from '@/types/tutor'

export interface SuggestedQuestionsProps {
  context: TutorContext
  onSelect: (question: string) => void
  className?: string
}

/**
 * Context-appropriate suggested questions.
 *
 * In mock mode these are deterministic sample suggestions. In real mode they
 * are predefined UI suggestions, clearly not AI-generated. We never pretend
 * suggestions were produced dynamically unless a backend recommendation
 * feature exists.
 */
export function SuggestedQuestions({ context, onSelect, className }: SuggestedQuestionsProps) {
  const prompts = context.type === 'notes' ? notesSuggestedPrompts : suggestedTutorPrompts

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        <Sparkles className="h-3 w-3" />
        <span>{USE_MOCK_API ? 'Try a demo question' : 'Suggested questions'}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelect(prompt)}
            className="rounded-full border border-border bg-background px-3 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:border-accent/40 hover:text-foreground"
          >
            {prompt}
          </button>
        ))}
      </div>
      {!USE_MOCK_API && (
        <p className="text-[10px] text-muted-foreground/70">
          These are predefined suggestions, not AI-generated.
        </p>
      )}
    </div>
  )
}

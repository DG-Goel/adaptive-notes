import { ChevronDown, Layers } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { CONTEXT_OPTIONS } from '@/mocks/tutor'
import { cn } from '@/lib/utils'
import type { TutorContext } from '@/types/tutor'

export interface ContextSelectorProps {
  context: TutorContext
  onChange: (context: TutorContext) => void
  videoId?: string
  className?: string
}

const TYPE_LABEL: Record<TutorContext['type'], string> = {
  general: 'General Tutor',
  video: 'Full Video',
  chapter: 'Current Chapter',
  timestamp: 'Timestamp Range',
  notes: 'Selected Notes',
}

/**
 * Select the conversation context.
 *
 * Modes that the backend has not confirmed support for are disabled with an
 * explanation — they are never silently mapped to whole-video retrieval.
 */
export function ContextSelector({ context, onChange, videoId, className }: ContextSelectorProps) {
  const currentType = context.type
  const label = TYPE_LABEL[currentType]

  const handleSelect = (type: TutorContext['type']) => {
    switch (type) {
      case 'general':
        onChange({ type: 'general' })
        break
      case 'video':
        onChange({ type: 'video', videoId: videoId ?? '' })
        break
      case 'chapter':
        onChange({ type: 'chapter', videoId: videoId ?? '', chapterId: '' })
        break
      case 'timestamp':
        onChange({ type: 'timestamp', videoId: videoId ?? '', startSeconds: 0, endSeconds: 0 })
        break
      case 'notes':
        onChange({ type: 'notes', videoId: videoId ?? '', sectionId: '' })
        break
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            'inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted',
            className,
          )}
        >
          <Layers className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="max-w-[8rem] truncate">{label}</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Conversation context</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {CONTEXT_OPTIONS.map((option) => {
          const active = option.value === currentType
          const disabled = !option.supported
          return (
            <DropdownMenuItem
              key={option.value}
              disabled={disabled}
              onSelect={() => handleSelect(option.value)}
              className={cn('flex flex-col items-start gap-0.5', active && 'bg-accent/5')}
            >
              <span className="flex w-full items-center justify-between">
                <span className="text-sm font-medium">{option.label}</span>
                {active && <span className="text-[10px] text-accent">Active</span>}
              </span>
              <span className="text-[11px] text-muted-foreground">{option.description}</span>
              {disabled && (
                <span className="text-[10px] text-amber-600">
                  Not supported by the backend yet
                </span>
              )}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

import { ChevronDown, Wand2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { EXPLANATION_MODES } from '@/mocks/tutor'
import { cn } from '@/lib/utils'
import type { ExplanationMode, ExplanationPreferences } from '@/types/tutor'

export interface ExplanationModeSelectorProps {
  preferences: ExplanationPreferences
  onChange: (preferences: ExplanationPreferences) => void
  className?: string
}

/**
 * Select the explanation style.
 *
 * These are frontend preferences. They are only sent to the backend when a
 * capability flag confirms support — until then they are a UI hint and the
 * selector makes that clear.
 */
export function ExplanationModeSelector({
  preferences,
  onChange,
  className,
}: ExplanationModeSelectorProps) {
  const current = preferences.mode ?? 'detailed'
  const currentOption = EXPLANATION_MODES.find((m) => m.value === current) ?? EXPLANATION_MODES[1]

  const handleSelect = (mode: ExplanationMode) => {
    onChange({ ...preferences, mode })
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
          <Wand2 className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="max-w-[7rem] truncate">{currentOption.label}</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Explanation style</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {EXPLANATION_MODES.map((option) => {
          const active = option.value === current
          return (
            <DropdownMenuItem
              key={option.value}
              onSelect={() => handleSelect(option.value)}
              className={cn('flex flex-col items-start gap-0.5', active && 'bg-accent/5')}
            >
              <span className="flex w-full items-center justify-between">
                <span className="text-sm font-medium">{option.label}</span>
                {active && <span className="text-[10px] text-accent">Active</span>}
              </span>
              <span className="text-[11px] text-muted-foreground">{option.description}</span>
            </DropdownMenuItem>
          )
        })}
        <DropdownMenuSeparator />
        <p className="px-2 py-1 text-[10px] text-muted-foreground">
          Style is a frontend preference until the backend confirms support.
        </p>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

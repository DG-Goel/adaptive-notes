import { useState } from 'react'
import { BrainCircuit, ChevronDown, Clock, Shuffle } from 'lucide-react'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import type { QuizConfig, QuizDifficulty, QuestionType, QuizMode } from '@/types/quiz'

const QUESTION_COUNTS = [5, 10, 15, 20]
const DIFFICULTIES: { value: QuizDifficulty; label: string; description: string }[] = [
  { value: 'easy', label: 'Easy', description: 'Fundamental concepts and definitions' },
  { value: 'medium', label: 'Medium', description: 'Moderate understanding and application' },
  { value: 'hard', label: 'Hard', description: 'Advanced concepts and analysis' },
  { value: 'mixed', label: 'Mixed', description: 'Combination of all difficulty levels' },
]

const QUESTION_TYPES: { value: QuestionType; label: string; icon: string }[] = [
  { value: 'single_select', label: 'Single Choice', icon: '●' },
  { value: 'multi_select', label: 'Multiple Choice', icon: '☑' },
  { value: 'true_false', label: 'True/False', icon: '⊤⊥' },
]

const MODES: { value: QuizMode; label: string; description: string }[] = [
  { value: 'practice', label: 'Practice Mode', description: 'Learn at your own pace with feedback' },
  { value: 'exam', label: 'Exam Mode', description: 'Test yourself without hints' },
]

export interface QuizConfigPanelProps {
  videoId?: string
  videoTitle?: string
  onStartQuiz: (config: Partial<QuizConfig>) => void
  loading?: boolean
  className?: string
}

/**
 * Elegant quiz configuration panel.
 *
 * Allows users to customize question count, difficulty, types, mode, and
 * additional options before generating a quiz. Uses NOETRA's premium design
 * language rather than a plain form.
 */
export function QuizConfigPanel({
  videoId,
  videoTitle,
  onStartQuiz,
  loading = false,
  className,
}: QuizConfigPanelProps) {
  const [questionCount, setQuestionCount] = useState(10)
  const [difficulty, setDifficulty] = useState<QuizDifficulty>('mixed')
  const [selectedTypes, setSelectedTypes] = useState<Set<QuestionType>>(
    new Set(['single_select', 'multi_select', 'true_false']),
  )
  const [mode, setMode] = useState<QuizMode>('practice')
  const [showExplanations, setShowExplanations] = useState(true)
  const [shuffleQuestions, setShuffleQuestions] = useState(false)
  const [shuffleOptions, setShuffleOptions] = useState(false)
  const [timed, setTimed] = useState(false)

  const toggleType = (type: QuestionType) => {
    const next = new Set(selectedTypes)
    if (next.has(type)) {
      if (next.size > 1) next.delete(type)
    } else {
      next.add(type)
    }
    setSelectedTypes(next)
  }

  const handleStart = () => {
    onStartQuiz({
      videoId,
      questionCount,
      difficulty,
      questionTypes: Array.from(selectedTypes),
      context: 'video',
      showExplanations,
      timed,
      shuffleQuestions,
      shuffleOptions,
      mode,
    })
  }

  const selectedDifficulty = DIFFICULTIES.find((d) => d.value === difficulty)

  return (
    <div className={cn('space-y-6', className)}>
      {/* Video context */}
      {videoTitle && (
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Quiz for
          </p>
          <p className="mt-1 font-serif text-base text-foreground">{videoTitle}</p>
        </div>
      )}

      {/* Question count */}
      <div>
        <label className="block text-sm font-medium text-foreground">Number of Questions</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {QUESTION_COUNTS.map((count) => (
            <button
              key={count}
              type="button"
              onClick={() => setQuestionCount(count)}
              className={cn(
                'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                questionCount === count
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border bg-background text-foreground hover:bg-muted',
              )}
            >
              {count}
            </button>
          ))}
        </div>
      </div>

      {/* Difficulty */}
      <div>
        <label className="block text-sm font-medium text-foreground">Difficulty</label>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="mt-2 inline-flex w-full items-center justify-between rounded-lg border border-border bg-background px-4 py-2.5 text-left text-sm transition-colors hover:bg-muted"
            >
              <span className="font-medium text-foreground">
                {selectedDifficulty?.label ?? 'Mixed'}
              </span>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64">
            {DIFFICULTIES.map((diff) => (
              <DropdownMenuItem
                key={diff.value}
                onSelect={() => setDifficulty(diff.value)}
                className="flex flex-col items-start gap-0.5"
              >
                <span className="font-medium">{diff.label}</span>
                <span className="text-xs text-muted-foreground">{diff.description}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Question types */}
      <div>
        <label className="block text-sm font-medium text-foreground">Question Types</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {QUESTION_TYPES.map((type) => {
            const selected = selectedTypes.has(type.value)
            return (
              <button
                key={type.value}
                type="button"
                onClick={() => toggleType(type.value)}
                className={cn(
                  'inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                  selected
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border bg-background text-foreground hover:bg-muted',
                )}
              >
                <span className="text-base">{type.icon}</span>
                {type.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Mode */}
      <div>
        <label className="block text-sm font-medium text-foreground">Mode</label>
        <div className="mt-2 space-y-2">
          {MODES.map((modeOption) => {
            const selected = mode === modeOption.value
            return (
              <button
                key={modeOption.value}
                type="button"
                onClick={() => setMode(modeOption.value)}
                className={cn(
                  'flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors',
                  selected
                    ? 'border-accent bg-accent/10'
                    : 'border-border bg-background hover:bg-muted',
                )}
              >
                <span
                  className={cn(
                    'mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2',
                    selected ? 'border-accent' : 'border-muted-foreground',
                  )}
                >
                  {selected && <span className="h-2 w-2 rounded-full bg-accent" />}
                </span>
                <div className="flex-1">
                  <p className={cn('font-medium', selected ? 'text-accent' : 'text-foreground')}>
                    {modeOption.label}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{modeOption.description}</p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Additional options */}
      <div>
        <label className="block text-sm font-medium text-foreground">Options</label>
        <div className="mt-2 space-y-2">
          <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-background p-3 transition-colors hover:bg-muted">
            <input
              type="checkbox"
              checked={showExplanations}
              onChange={(e) => setShowExplanations(e.target.checked)}
              className="h-4 w-4 rounded border-muted-foreground text-accent focus:ring-2 focus:ring-accent/20"
            />
            <span className="flex-1 text-sm text-foreground">Show explanations after submission</span>
          </label>

          <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-background p-3 transition-colors hover:bg-muted">
            <input
              type="checkbox"
              checked={shuffleQuestions}
              onChange={(e) => setShuffleQuestions(e.target.checked)}
              className="h-4 w-4 rounded border-muted-foreground text-accent focus:ring-2 focus:ring-accent/20"
            />
            <div className="flex flex-1 items-center gap-2">
              <Shuffle className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-sm text-foreground">Shuffle questions</span>
            </div>
          </label>

          <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-background p-3 transition-colors hover:bg-muted">
            <input
              type="checkbox"
              checked={shuffleOptions}
              onChange={(e) => setShuffleOptions(e.target.checked)}
              className="h-4 w-4 rounded border-muted-foreground text-accent focus:ring-2 focus:ring-accent/20"
            />
            <div className="flex flex-1 items-center gap-2">
              <Shuffle className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-sm text-foreground">Shuffle answer options</span>
            </div>
          </label>

          <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-background p-3 transition-colors hover:bg-muted">
            <input
              type="checkbox"
              checked={timed}
              onChange={(e) => setTimed(e.target.checked)}
              className="h-4 w-4 rounded border-muted-foreground text-accent focus:ring-2 focus:ring-accent/20"
            />
            <div className="flex flex-1 items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-sm text-foreground">Timed quiz</span>
            </div>
          </label>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-3 border-t border-border pt-6">
        <PrimaryButton
          onClick={handleStart}
          loading={loading}
          disabled={loading || selectedTypes.size === 0}
          size="lg"
          className="flex-1"
        >
          <BrainCircuit className="h-4 w-4" />
          Generate Quiz
        </PrimaryButton>
        <SecondaryButton size="lg">View History</SecondaryButton>
      </div>

      <p className="text-center text-xs text-muted-foreground">
        Questions are AI-generated from your lecture content
      </p>
    </div>
  )
}

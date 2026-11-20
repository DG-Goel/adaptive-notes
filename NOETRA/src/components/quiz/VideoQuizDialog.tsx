import { useQuery } from '@tanstack/react-query'
import { BrainCircuit } from 'lucide-react'
import { formatTime as timestamp } from '@/lib/format'
import { useState } from 'react'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'

type GeneratedQuiz = {
  status: string
  duration_seconds?: number
  questions: {
    id: string; question: string; bloom_level: string; answer: string; explanation: string
    topic?: string
    options?: string[]
    correct_option_index?: number
    review_timestamps?: { source_id: string; segment_id: string; start: number; end: number }[]
  }[]
}

export function VideoQuizDialog({ video, onSeek, buttonLabel, duration }: {
  video: string
  onSeek: (seconds: number) => void
  buttonLabel?: string
  duration?: number
}) {
  const [open, setOpen] = useState(false)
  const [analysing, setAnalysing] = useState(false)
  const [selfGrades, setSelfGrades] = useState<Record<string, 'correct' | 'incorrect' | null>>({})
  const [choices, setChoices] = useState<Record<string, number>>({})
  const quiz = useQuery({
    queryKey: ['generated-video-quiz', video],
    enabled: open,
    retry: false,
    queryFn: async ({ signal }): Promise<GeneratedQuiz | null> => {
      const response = await fetch('/api/videos/' + encodeURIComponent(video) + '/quiz', { signal })
      if (response.status === 404) return null
      if (!response.ok) throw new Error('Could not load the quiz.')
      return response.json()
    },
  })
  const questions = quiz.data?.questions ?? []
  const choiceCount = questions.filter(row => row.options?.length === 4).length
  const results = questions.map(question => {
    const choice = choices[question.id]
    const graded = question.options?.length === 4 && question.correct_option_index !== undefined
    const outcome = graded && choice !== undefined
      ? choice === question.correct_option_index ? 'correct' : 'incorrect'
      : selfGrades[question.id] ?? null
    return { question, outcome }
  })
  const correct = results.filter(row => row.outcome === 'correct').length
  const incorrect = results.filter(row => row.outcome === 'incorrect').length
  const topics = new Map<string, typeof results>()
  for (const row of results) {
    const key = (row.question.topic?.trim() || 'Unlabelled topic').toLowerCase()
    const group = topics.get(key) ?? []
    group.push(row)
    topics.set(key, group)
  }

  const spanEnd = Math.max(0, ...questions.flatMap(row =>
    (row.review_timestamps ?? []).map(span => Number.isFinite(span.end) ? span.end : 0)))
  const knownDuration = [duration, quiz.data?.duration_seconds].find(
    value => value !== undefined && Number.isFinite(value) && value > 0)
  const timelineEnd = Math.ceil(Math.max(knownDuration ?? 0, spanEnd))
  const windowSize = Math.max(1, Math.ceil(timelineEnd / 8))
  const windows = Array.from({ length: Math.ceil(timelineEnd / windowSize) }, () => 0)
  let unplaced = 0
  for (const { question, outcome } of results) {
    if (outcome !== 'incorrect') continue
    const starts = (question.review_timestamps ?? []).map(span => span.start)
      .filter(start => Number.isFinite(start) && start >= 0 && start <= timelineEnd)
    if (!starts.length || !windows.length) {
      unplaced++
      continue
    }
    const index = Math.min(windows.length - 1, Math.floor(Math.min(...starts) / windowSize))
    windows[index]++
  }
  const peak = Math.max(0, ...windows)
  const seek = (seconds: number) => {
    onSeek(seconds)
    setOpen(false)
  }

  return (
    <>
      <SecondaryButton size="sm" title="Open lecture quiz" aria-label="Open lecture quiz" onClick={() => setOpen(true)}>
        <BrainCircuit className="h-3.5 w-3.5" />
        {buttonLabel ?? <span className="hidden lg:inline">Quiz</span>}
      </SecondaryButton>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-2xl">
          <DialogTitle>Lecture quiz</DialogTitle>
          <DialogDescription>{video}</DialogDescription>
          {quiz.isPending ? <p role="status">Loading quiz…</p> : quiz.isError ? (
            <div role="alert" className="space-y-2">
              <p>Could not load the quiz.</p>
              <SecondaryButton onClick={() => void quiz.refetch()}>Try again</SecondaryButton>
            </div>
          ) : !quiz.data?.questions.length ? (
            <p>No quiz questions available yet. Generate AI notes for this video to create its quiz.</p>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">
                {quiz.data.questions.length} questions · {choiceCount === questions.length
                  ? 'Multiple choice'
                  : choiceCount === 0 ? 'Short answer' : `${choiceCount} multiple choice`}
                {quiz.data.status === 'incomplete' && ' · Some chunks are missing'}
              </p>
              <SecondaryButton type="button" onClick={() => setAnalysing(value => !value)}>
                {analysing ? 'Back to quiz' : 'Analyse quiz'}
              </SecondaryButton>
              {analysing ? (
                <section aria-label="Quiz analysis" className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    {correct} correct · {incorrect} incorrect · {questions.length - correct - incorrect} ungraded
                  </p>
                  <div className="space-y-4 rounded-xl border border-border p-4">
                    <h2 className="font-semibold">Results by topic</h2>
                    <p className="text-xs">
                      <span className="text-emerald-500">● Correct</span>
                      <span className="ml-4 text-rose-500">● Incorrect</span>
                      <span className="ml-4 text-muted-foreground">● Ungraded</span>
                    </p>
                    {[...topics].map(([key, rows]) => {
                      const counts = [
                        rows.filter(row => row.outcome === 'correct').length,
                        rows.filter(row => row.outcome === 'incorrect').length,
                        rows.filter(row => row.outcome === null).length,
                      ]
                      const label = rows[0].question.topic?.trim() || 'Unlabelled topic'
                      return <div key={key} className="space-y-1.5">
                        <div className="flex flex-wrap justify-between gap-x-2 text-sm">
                          <h3 className="font-medium">{label}</h3>
                          <span className="text-xs text-muted-foreground">
                            {counts[0]} correct · {counts[1]} incorrect · {counts[2]} ungraded
                          </span>
                        </div>
                        <div aria-hidden="true" className="flex h-2 overflow-hidden rounded-full bg-muted">
                          {counts.map((count, index) => (
                            <span key={index} className={['bg-emerald-500', 'bg-rose-500', 'bg-muted-foreground/30'][index]}
                              style={{ width: (count / rows.length) * 100 + '%' }} />
                          ))}
                        </div>
                      </div>
                    })}
                  </div>
                  <div className="space-y-3 rounded-xl border border-border p-4">
                    <h2 className="font-semibold">Missed questions across the lecture</h2>
                    <p className="text-xs text-muted-foreground">
                      Each missed question is counted at its earliest review timestamp.
                      {!knownDuration && timelineEnd > 0 && ' The chart ends at the last available quiz timestamp.'}
                    </p>
                    {windows.length > 0 && <>
                      <div className="flex gap-1.5">
                        {windows.map((count, index) => {
                          const start = index * windowSize
                          const end = Math.min(start + windowSize, timelineEnd)
                          const highest = count > 0 && count === peak
                          const label = `${timestamp(start)}–${timestamp(end)} · ${count} missed${highest ? ' · Most missed' : ''}`
                          return <button key={start} type="button" aria-label={label} title={label}
                            onClick={() => seek(start)}
                            className="flex min-w-0 flex-col justify-end gap-1 rounded-sm text-xs hover:bg-muted focus-visible:outline focus-visible:outline-2"
                            style={{ flex: end - start }}>
                            <span aria-hidden="true">{count}</span>
                            <span aria-hidden="true" className="flex h-24 items-end rounded-t bg-muted/40">
                              <span className={`w-full rounded-t ${highest ? 'bg-rose-500' : 'bg-rose-400/50'}`}
                                style={{ height: count === 0 ? 0 : (count / peak) * 100 + '%' }} />
                            </span>
                          </button>
                        })}
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>0:00</span><span>{timestamp(timelineEnd)}</span>
                      </div>
                    </>}
                    {peak > 0 ? <p className="text-sm font-medium">
                      Most missed ({peak}) · {windows.flatMap((count, index) => count === peak
                        ? [`${timestamp(index * windowSize)}–${timestamp(Math.min((index + 1) * windowSize, timelineEnd))}`]
                        : []).join(', ')}
                    </p> : <p className="text-sm text-muted-foreground">No timestamped misses yet.</p>}
                    {unplaced > 0 && <p className="text-xs text-muted-foreground">
                      Missed questions without a review timestamp · {unplaced}
                    </p>}
                  </div>
                  <div className="space-y-3">
                    <h2 className="font-semibold">Missed questions</h2>
                    {incorrect === 0 && <p className="text-sm text-muted-foreground">No missed questions yet.</p>}
                    {results.filter(row => row.outcome === 'incorrect').map(({ question: row }) => (
                      <article key={row.id} className="space-y-2 rounded-lg border border-border p-3 text-sm">
                        <p className="text-xs text-muted-foreground">{row.topic?.trim() || 'Unlabelled topic'}</p>
                        <p className="font-medium">{row.question}</p>
                        <p className="text-muted-foreground">Correct answer · {row.answer}</p>
                        {row.review_timestamps?.map(span => (
                          <button key={span.source_id + ':' + span.segment_id} type="button"
                            className="mr-3 underline" onClick={() => seek(span.start)}>
                            Review at {timestamp(span.start)}
                          </button>
                        ))}
                      </article>
                    ))}
                  </div>
                </section>
              ) : <ol className="list-decimal space-y-5 pl-6">
                {quiz.data.questions.map(row => (
                  <li key={row.id} className="space-y-2 pl-1">
                    <p className="text-xs text-muted-foreground">
                      {row.topic && <><strong>{row.topic}</strong> · </>}{row.bloom_level}
                    </p>
                    <p className="font-medium">{row.question}</p>
                    {row.options?.length === 4 && (
                      <fieldset className="space-y-2">
                        <legend className="sr-only">{row.question}</legend>
                        {row.options.map((option, index) => {
                          const selected = choices[row.id]
                          const graded = selected !== undefined && row.correct_option_index !== undefined
                          const correctOption = graded && index === row.correct_option_index
                          const wrongOption = graded && selected === index && !correctOption
                          const color = correctOption ? 'border-emerald-500 bg-emerald-500/15'
                            : wrongOption ? 'border-red-500 bg-red-500/15' : 'border-border'
                          return (
                          <label key={index} className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2 text-sm ${color}`}>
                            <input type="radio" name={row.id} className="mt-1"
                              checked={choices[row.id] === index}
                              onChange={() => {
                                setChoices(previous => ({ ...previous, [row.id]: index }))
                              }} />
                            <span>{option}</span>
                            {correctOption && <span className="ml-auto font-medium">Correct answer</span>}
                            {wrongOption && <span className="ml-auto font-medium">Incorrect</span>}
                          </label>
                          )
                        })}
                        {choices[row.id] !== undefined && row.correct_option_index !== undefined && (
                          <p role="status" className="text-sm">
                            {choices[row.id] === row.correct_option_index ? 'Correct' : 'Incorrect'}
                          </p>
                        )}
                      </fieldset>
                    )}
                    <details className="rounded-lg border border-border p-3 text-sm">
                      <summary className="cursor-pointer">Show answer</summary>
                      <p className="mt-2 whitespace-pre-wrap">{row.answer}</p>
                      <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{row.explanation}</p>
                      {(row.options?.length !== 4 || row.correct_option_index === undefined) && (
                        <label className="mt-3 flex flex-wrap items-center gap-2">
                          Self-assessment
                          <select value={selfGrades[row.id] ?? ''} className="rounded-md border border-border bg-card p-1"
                            onChange={event => {
                              const value = event.target.value
                              const grade = value === 'correct' || value === 'incorrect' ? value : null
                              setSelfGrades(previous => ({ ...previous, [row.id]: grade }))
                            }}>
                            <option value="">Ungraded</option>
                            <option value="correct">I got this right</option>
                            <option value="incorrect">I missed this question</option>
                          </select>
                        </label>
                      )}
                      {row.review_timestamps?.map(span => (
                        <button key={span.source_id + ':' + span.segment_id} type="button"
                          className="mr-3 mt-2 underline" onClick={() => {
                            onSeek(span.start)
                            setOpen(false)
                          }}>
                          Review at {timestamp(span.start)}
                        </button>
                      ))}
                      {row.topic && !row.review_timestamps?.length && (
                        <p className="mt-2 text-muted-foreground">No uniquely matched transcript timestamp.</p>
                      )}
                    </details>
                  </li>
                ))}
              </ol>}
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}

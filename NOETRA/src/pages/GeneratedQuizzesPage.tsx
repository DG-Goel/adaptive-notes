import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { VideoQuizDialog } from '@/components/quiz/VideoQuizDialog'

type QuizEntry = { video: string; question_count: number; status: string }

export function GeneratedQuizzesPage() {
  const navigate = useNavigate()
  const quizzes = useQuery({
    queryKey: ['generated-quiz-library'],
    retry: false,
    queryFn: async ({ signal }): Promise<QuizEntry[]> => {
      const response = await fetch('/api/video-notes/quizzes', { signal })
      if (!response.ok) throw new Error('Could not load quizzes.')
      return response.json()
    },
  })

  return (
    <section className="space-y-6">
      <h1 className="text-4xl">Quizzes</h1>
      {quizzes.isPending && <p role="status">Loading quizzes…</p>}
      {quizzes.isError && (
        <div role="alert" className="space-y-2">
          <p>Couldn’t load quizzes. Check that the video notes backend is running.</p>
          <button type="button" className="underline" onClick={() => void quizzes.refetch()}>Try again</button>
        </div>
      )}
      {quizzes.data?.length === 0 && (
        <p>Generate AI notes from <Link className="underline" to="/library">My Lectures</Link> to create a quiz.</p>
      )}
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {quizzes.data?.map(quiz => (
          <li key={quiz.video} className="space-y-3 rounded-xl border border-border bg-card p-4">
            <h2 className="break-words text-lg">{quiz.video}</h2>
            <p className="text-sm text-muted-foreground">
              {quiz.question_count} {quiz.question_count === 1 ? 'question' : 'questions'}
              {quiz.status === 'incomplete' && ' · Incomplete'}
            </p>
            <VideoQuizDialog video={quiz.video} buttonLabel="Open quiz"
              onSeek={seconds => navigate(`/learn/${encodeURIComponent('local:' + quiz.video)}?t=${seconds}`)} />
          </li>
        ))}
      </ul>
    </section>
  )
}

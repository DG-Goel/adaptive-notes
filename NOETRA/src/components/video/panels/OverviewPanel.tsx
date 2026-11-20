import { CheckCircle2, Clock, GraduationCap, Layers, MessageSquareQuote, Target, TriangleAlert } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { SectionHeader } from '@/components/common/SectionHeader'
import { cn } from '@/lib/utils'
import { formatTime } from '@/lib/format'
import type { VideoLecture } from '@/types/video'

export interface OverviewPanelProps {
  lecture: VideoLecture
  className?: string
  duration?: number
}

export function OverviewPanel({ lecture, className, duration }: OverviewPanelProps) {
  const localName = lecture.id.startsWith('local:') ? lecture.id.slice('local:'.length) : ''
  const overview = useQuery({
    queryKey: ['lecture-overview', localName],
    enabled: !!localName,
    retry: false,
    queryFn: async ({ signal }): Promise<{ topics: string[] }> => {
      const response = await fetch(`/api/videos/${encodeURIComponent(localName)}/overview`, { signal })
      if (!response.ok) throw new Error('Lecture topics unavailable.')
      return response.json()
    },
  })
  const topics = overview.data?.topics ?? []
  const objectives = lecture.objectives.length ? lecture.objectives
    : topics.slice(0, 5).map(topic => `Answer practice questions about ${topic}.`)
  const concepts = lecture.keyConcepts.length ? lecture.keyConcepts : topics
  const videoDuration = duration || lecture.duration
  const meta = [
    { icon: GraduationCap, label: 'Course', value: lecture.course },
    { icon: MessageSquareQuote, label: 'Instructor', value: lecture.instructor || 'Not listed' },
    { icon: Clock, label: 'Duration', value: videoDuration > 0 ? formatTime(videoDuration) : 'Unavailable' },
    { icon: Layers, label: 'Chapters', value: String(lecture.chapters.length) },
  ]

  return (
    <div className={cn('space-y-5', className)}>
      <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <SectionHeader title="About this lecture" />
        {lecture.description && <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{lecture.description}</p>}

        <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {meta.map(({ icon: Icon, label, value }) => (
            <div key={label} className="rounded-xl border border-border bg-muted/30 p-3">
              <dt className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                <Icon className="h-3 w-3" /> {label}
              </dt>
              <dd className="mt-1 truncate text-sm font-medium text-foreground" title={value}>
                {value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {lecture.isPlaybackDemo && lecture.playbackNote && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-500/[0.07] p-4">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div>
            <p className="text-sm font-medium text-foreground">Playback demonstration</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              {lecture.playbackNote}
            </p>
          </div>
        </div>
      )}

      <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <SectionHeader
          title="Learning objectives"
          description="What you should be able to do after this lecture"
        />
        <ul className="mt-4 space-y-2.5">
          {!objectives.length && <li className="text-sm text-muted-foreground">No learning objectives available yet.</li>}
          {objectives.map((objective) => (
            <li key={objective} className="flex items-start gap-2.5">
              <Target className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
              <span className="text-sm leading-relaxed text-foreground/85">{objective}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
        <SectionHeader title="Key concepts" description="Terms introduced in this lecture" />
        <div className="mt-4 flex flex-wrap gap-2">
          {!concepts.length && <p className="text-sm text-muted-foreground">No key concepts available yet.</p>}
          {concepts.map((concept) => (
            <span
              key={concept}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-accent/40 hover:text-foreground"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-accent/70" />
              {concept}
            </span>
          ))}
        </div>
      </section>
    </div>
  )
}

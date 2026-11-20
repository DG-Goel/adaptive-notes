import { useQuery } from '@tanstack/react-query'
import { MarkdownBlock } from '@/components/notes/MarkdownBlock'

type Visual = { id: string; title: string; markdown: string }

export function LocalVisualsPanel({ video }: { video: string }) {
  const visuals = useQuery({
    queryKey: ['local-video-visuals', video],
    refetchInterval: 10_000,
    queryFn: async ({ signal }): Promise<Visual[]> => {
      const response = await fetch(`/api/videos/${encodeURIComponent(video)}/visuals`, { signal })
      if (!response.ok) throw new Error('Could not load lecture visuals.')
      return response.json()
    },
  })

  if (visuals.isPending) return <p role="status">Loading visuals…</p>
  if (visuals.isError) return <p role="alert">{visuals.error.message}</p>
  if (!visuals.data.length) return <p>No visuals were saved for this run.</p>

  return (
    <div className="space-y-4">
      {visuals.data.map(visual => (
        <section key={visual.id} className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-medium">{visual.title}</h2>
          <MarkdownBlock content={visual.markdown} />
        </section>
      ))}
    </div>
  )
}

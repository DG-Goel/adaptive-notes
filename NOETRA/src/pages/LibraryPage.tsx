import { useQuery } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { Link } from 'react-router-dom'
import { listLocalVideos } from '@/services/api/videos'

export function LibraryPage() {
  const { data: videos, error, isPending, refetch } = useQuery({
    queryKey: ['local-video-library'],
    queryFn: ({ signal }) => listLocalVideos(signal),
    retry: false,
  })

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-4xl">My Lectures</h1>
        <p className="mt-2 text-muted-foreground">Open a video to watch it and generate AI notes.</p>
      </div>
      {isPending && <p role="status">Loading videos…</p>}
      {error && (
        <div role="alert" className="space-y-2">
          <p>Couldn’t load your videos. Check that the local video notes service is running.</p>
          <button type="button" className="underline" onClick={() => void refetch()}>Retry</button>
        </div>
      )}
      {videos?.length === 0 && <p>Add MP4 files to the backend video folder to see them here.</p>}
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {videos?.map(video => (
          <li key={video.id}>
            <Link
              to={`/learn/${encodeURIComponent(video.id)}`}
              className="group block overflow-hidden rounded-xl border bg-card hover:bg-accent"
            >
              <div className="relative aspect-video bg-muted">
                <video
                  src={video.source.url + '#t=1'}
                  preload="metadata"
                  muted
                  playsInline
                  aria-hidden="true"
                  className="pointer-events-none h-full w-full object-contain"
                />
                <span className="absolute bottom-3 right-3 rounded-full bg-black/65 p-2 text-white">
                  <Play className="size-4" aria-hidden="true" />
                </span>
              </div>
              <span className="block break-all p-4">{video.title}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

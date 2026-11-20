import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { MarkdownBlock } from '@/components/notes/MarkdownBlock'
import type { VideoLecture } from '@/types/video'

type Job = { video: string; state: string; stage: string; error?: string; quiz_available?: boolean; quiz_count?: number; quiz_status?: string }
type TrackedJob = { video: string; id: string; status?: Job }

function rememberJob(key: string, id: string) {
  try {
    if (id) localStorage.setItem(key, id)
    else localStorage.removeItem(key)
  } catch {
    // Browser storage is optional. Status polling uses React state.
  }
}

async function api<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, { cache: 'no-store', ...options })
  const data = await response.json().catch(() => null)
  if (!response.ok || !data) throw new Error(data?.detail || `Video notes request failed (${response.status}): ${url}`)
  return data as T
}

export function VideoNotesJob({ lecture }: { lecture: VideoLecture }) {
  const queryClient = useQueryClient()
  const storageKey = 'noetra:video-notes:' + lecture.id
  const localVideo = lecture.id.startsWith('local:') ? lecture.id.slice('local:'.length) : ''
  const localSource = !!localVideo
  const [files, setFiles] = useState<string[]>([])
  const [selectedVideo, setVideo] = useState('')
  const video = localVideo || selectedVideo
  const [allowed, setAllowed] = useState(false)
  const [trackedJob, setTrackedJob] = useState<TrackedJob>()
  const [starting, setStarting] = useState(false)
  const startPending = useRef(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (localSource) return
    const controller = new AbortController()
    api<string[]>('/api/videos', { signal: controller.signal }).then(names => {
      if (controller.signal.aborted) return
      setFiles(names)
      const url = new URL(lecture.source.url, window.location.origin)
      const filename = decodeURIComponent(url.pathname.split('/').pop() || '')
      if (!lecture.isPlaybackDemo && url.origin === window.location.origin && names.includes(filename)) setVideo(filename)
    }).catch(err => { if (!controller.signal.aborted) setError(err.message) })
    return () => controller.abort()
  }, [lecture.source.url, lecture.isPlaybackDemo, localSource])

  useEffect(() => {
    if (!video || starting) return
    const controller = new AbortController()
    const options = { signal: controller.signal }
    let timer: ReturnType<typeof setTimeout> | undefined
    let lastQuiz = ''
    const poll = async () => {
      let delay = 5000
      try {
        const { job_id: id } = await api<{ job_id: string }>(
          `/api/videos/${encodeURIComponent(video)}/notes-job`, options)
        if (controller.signal.aborted) return
        const status = id ? await api<Job>('/api/video-notes/' + id, options) : undefined
        if (controller.signal.aborted) return
        setTrackedJob({ video, id, status })
        rememberJob(storageKey, id)
        const quiz = status?.quiz_available ? `${id}:${status.quiz_count}:${status.quiz_status}` : ''
        if (quiz !== lastQuiz) {
          lastQuiz = quiz
          void queryClient.invalidateQueries({ queryKey: ['lecture-overview', video] })
        }
        setError('')
        if (status && ['queued', 'running'].includes(status.state)) delay = 3000
      } catch (err) {
        if (!controller.signal.aborted) setError((err as Error).message)
      } finally {
        if (!controller.signal.aborted) timer = setTimeout(poll, delay)
      }
    }
    void poll()
    return () => { controller.abort(); clearTimeout(timer) }
  }, [video, starting, storageKey, queryClient])

  async function start(regenerate = false) {
    if (startPending.current || busy || !video || !allowed) return
    startPending.current = true
    setStarting(true)
    setError('')
    try {
      const result = await api<{ job_id: string }>('/api/video-notes', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video, allow_groq: allowed, regenerate }),
      })
      setTrackedJob({ video, id: result.job_id })
      rememberJob(storageKey, result.job_id)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      startPending.current = false
      setStarting(false)
    }
  }

  const tracked = trackedJob?.video === video ? trackedJob : undefined
  const currentJob = tracked?.status
  const busy = starting || (!!tracked?.id && !currentJob && !error) ||
    ['queued', 'running'].includes(currentJob?.state || '')
  const output = `/api/video-notes/${tracked?.id ?? ''}`
  const filename = video.replace(/\.mp4$/i, '')
  const notesUrl = currentJob && ['complete', 'partial'].includes(currentJob.state)
    ? output + '/markdown' : ''
  const [preview, setPreview] = useState<{ url: string; content?: string }>({ url: '' })

  useEffect(() => {
    if (!notesUrl) return
    const controller = new AbortController()
    fetch(notesUrl, { signal: controller.signal }).then(response => {
      if (!response.ok || !response.headers.get('content-type')?.startsWith('text/plain')) {
        throw new Error('Notes preview unavailable')
      }
      return response.text()
    }).then(content => setPreview({ url: notesUrl, content })).catch(() => {
      if (!controller.signal.aborted) setPreview({ url: notesUrl })
    })
    return () => controller.abort()
  }, [notesUrl])
  return (
    <section className="mb-4 space-y-3 rounded-2xl border border-border bg-card p-5">
      <label className="block text-sm">
        Source video
        <select className="ml-3 rounded border bg-background p-1" value={video} disabled={busy || localSource}
          onChange={event => setVideo(event.target.value)}>
          {!localSource && <option value="">Choose the matching local MP4</option>}
          {(localSource ? [localVideo] : files).map(name => <option key={name}>{name}</option>)}
        </select>
      </label>
      <label className="flex gap-2 text-sm">
        <input type="checkbox" checked={allowed} onChange={event => setAllowed(event.target.checked)} />
        Allow Groq to process the transcript, OCR text, and notes for this video
      </label>
      <div className="flex flex-wrap gap-2">
        <PrimaryButton disabled={!video || !allowed || busy} onClick={() => void start()}>
          {busy ? 'Generating notes…' : 'Generate AI notes'}
        </PrimaryButton>
        <SecondaryButton disabled={!video || !allowed || busy} onClick={() => void start(true)}>
          Regenerate
        </SecondaryButton>
      </div>
      <div aria-live="polite" className="space-y-2 text-sm">
        {currentJob && <p>{currentJob.error || `${currentJob.stage} · ${currentJob.state}`}</p>}
        {error && <p role="alert">{error}</p>}
        {currentJob?.quiz_available && (
          <p><a className="underline" href={output + '/quiz'} download={filename + '-quiz.md'}>
            Download quiz with answers ({currentJob.quiz_count} questions)
          </a>{currentJob.quiz_status === 'incomplete' && ' · Incomplete: some chunks failed'}</p>
        )}
        {currentJob && ['complete', 'partial'].includes(currentJob.state) && (
          <>
            <div className="flex flex-wrap gap-4">
              <a className="underline" href={output + '/study'} download={filename + '-study-notes.pdf'}>Download study notes PDF</a>
              <a className="underline" href={output + '/reference'} download={filename + '-notes-with-evidence.pdf'}>Download notes with evidence PDF</a>
            </div>
            {preview.url !== notesUrl ? <p>Loading study notes…</p> : preview.content ? (
              <article aria-label={`Study notes for ${video}`} className="handwritten-notes">
                <MarkdownBlock content={preview.content} />
              </article>
            ) : <p role="alert">The notes preview is unavailable. Try the study notes download.</p>}
          </>
        )}
      </div>
    </section>
  )
}

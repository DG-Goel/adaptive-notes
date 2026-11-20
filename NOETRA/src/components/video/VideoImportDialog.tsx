import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CheckCircle2,
  FileVideo,
  Info,
  Link2,
  Play,
  TriangleAlert,
  Upload,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { cn } from '@/lib/utils'
import { formatFileSize } from '@/lib/format'
import { ApiErrorException } from '@/types/api'
import { USE_MOCK_API } from '@/config/endpoints'
import { importVideoByUrl, uploadVideo } from '@/services/api'
import type { VideoImportResult } from '@/types/video'

type Mode = 'upload' | 'url'

interface ProviderInfo {
  label: string
  supported: boolean
  note?: string
}

/** Best-effort provider detection — used only to inform the user, never to imply import support. */
function detectProvider(rawUrl: string): ProviderInfo | null {
  let parsed: URL
  try {
    parsed = new URL(rawUrl)
  } catch {
    return null
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null

  const host = parsed.hostname.replace(/^www\./, '').toLowerCase()
  if (host === 'youtu.be' || host.endsWith('youtube.com')) {
    return { label: 'YouTube', supported: true }
  }
  if (host.endsWith('vimeo.com')) {
    return { label: 'Vimeo', supported: true }
  }
  if (host.endsWith('drive.google.com')) {
    return {
      label: 'Google Drive',
      supported: false,
      note: 'Direct Google Drive links are not supported yet.',
    }
  }
  return {
    label: host,
    supported: false,
    note: 'This host is not on the supported provider list yet.',
  }
}

function toMessage(error: unknown): string {
  if (error instanceof ApiErrorException) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

export interface VideoImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function VideoImportDialog({ open, onOpenChange }: VideoImportDialogProps) {
  const [mode, setMode] = useState<Mode>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VideoImportResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const previewUrlRef = useRef<string | null>(null)

  /** Release the current local preview, if any. */
  const revokePreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setPreviewUrl(null)
  }, [])

  // Release the object URL if the dialog unmounts while a preview is live.
  useEffect(
    () => () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current)
    },
    [],
  )

  const reset = useCallback(() => {
    revokePreview()
    setFile(null)
    setUrl('')
    setError(null)
    setResult(null)
    setSubmitting(false)
  }, [revokePreview])

  const handleOpenChange = (next: boolean) => {
    if (!next) reset()
    onOpenChange(next)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null
    revokePreview()
    setError(null)
    setResult(null)
    if (!selected) {
      setFile(null)
      return
    }
    if (!selected.type.startsWith('video/')) {
      setFile(null)
      setError('That file is not a video. Choose an MP4, WebM, or MOV file.')
      return
    }
    setFile(selected)
    const objectUrl = URL.createObjectURL(selected)
    previewUrlRef.current = objectUrl
    setPreviewUrl(objectUrl)
  }

  const provider = mode === 'url' ? detectProvider(url.trim()) : null
  const urlEntered = url.trim().length > 0
  const canSubmit =
    !submitting && (mode === 'upload' ? Boolean(file) : urlEntered && Boolean(provider))

  const handleSubmit = async () => {
    setError(null)
    setResult(null)
    setSubmitting(true)
    try {
      if (mode === 'upload') {
        const formData = new FormData()
        formData.append('file', file as File)
        const response = await uploadVideo(formData)
        setResult(response)
      } else {
        const response = await importVideoByUrl({ url: url.trim() })
        setResult(response)
      }
    } catch (err) {
      setError(toMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Add a lecture</DialogTitle>
          <DialogDescription>
            Upload a video file or paste a link. Processing runs on the backend — nothing is marked
            as imported until the server confirms it.
          </DialogDescription>
        </DialogHeader>

        <div role="tablist" aria-label="Import method" className="inline-flex rounded-full border border-border bg-muted/40 p-0.5">
          {(
            [
              { value: 'upload', label: 'Upload file', icon: Upload },
              { value: 'url', label: 'Paste URL', icon: Link2 },
            ] as const
          ).map((tab) => {
            const Icon = tab.icon
            const active = mode === tab.value
            return (
              <button
                key={tab.value}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => {
                  setMode(tab.value)
                  setError(null)
                  setResult(null)
                }}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors',
                  active
                    ? 'bg-accent text-accent-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <Icon className="h-3.5 w-3.5" /> {tab.label}
              </button>
            )
          })}
        </div>

        {result ? (
          <div className="flex items-start gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/[0.07] p-4">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground">Import accepted</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                The backend accepted the request and is processing it. Lecture ID:{' '}
                <span className="font-mono text-foreground">{result.videoId}</span>
              </p>
            </div>
          </div>
        ) : mode === 'upload' ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-muted/30 px-4 py-8 text-center transition-colors hover:border-accent/40 hover:bg-muted/50"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-card text-accent">
                <FileVideo className="h-5 w-5" />
              </span>
              <span className="text-sm font-medium text-foreground">
                {file ? 'Choose a different file' : 'Choose a video file'}
              </span>
              <span className="text-xs text-muted-foreground">MP4, WebM, or MOV</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={handleFileChange}
            />

            {file && (
              <div className="rounded-xl border border-border bg-card p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                  </div>
                  <SecondaryButton
                    size="sm"
                    onClick={() => {
                      revokePreview()
                      setFile(null)
                    }}
                  >
                    Remove
                  </SecondaryButton>
                </div>
                {previewUrl && (
                  <video
                    src={previewUrl}
                    controls
                    className="mt-3 max-h-44 w-full rounded-lg bg-black"
                  />
                )}
                {USE_MOCK_API && (
                  <p className="mt-2 flex items-start gap-1.5 text-[11px] leading-relaxed text-muted-foreground">
                    <Info className="mt-0.5 h-3 w-3 shrink-0" />
                    Demo mode: the file previews locally, but no upload is sent to a backend.
                  </p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <label className="block text-xs font-medium text-muted-foreground" htmlFor="import-url">
              Video URL
            </label>
            <Input
              id="import-url"
              type="url"
              inputMode="url"
              placeholder="https://www.youtube.com/watch?v=…"
              value={url}
              onChange={(event) => {
                setUrl(event.target.value)
                setError(null)
                setResult(null)
              }}
            />

            {urlEntered && provider && (
              <div
                className={cn(
                  'flex items-start gap-2.5 rounded-xl border p-3',
                  provider.supported
                    ? 'border-border bg-muted/40'
                    : 'border-amber-500/30 bg-amber-500/[0.07]',
                )}
              >
                {provider.supported ? (
                  <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                ) : (
                  <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
                )}
                <div className="min-w-0">
                  <p className="text-xs font-medium text-foreground">
                    Source: {provider.label}
                    {!provider.supported && ' · unsupported provider'}
                  </p>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                    {provider.note ?? 'This provider is recognized. The backend decides whether it can be imported.'}
                  </p>
                </div>
              </div>
            )}

            {urlEntered && !provider && (
              <p className="text-xs text-amber-600">
                Enter a valid http(s) link to check whether it can be imported.
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2.5 rounded-xl border border-destructive/30 bg-destructive/[0.06] p-3">
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
            <p className="text-xs leading-relaxed text-foreground/85">{error}</p>
          </div>
        )}

        <DialogFooter className="gap-2">
          {result ? (
            <>
              <SecondaryButton onClick={() => handleOpenChange(false)}>Close</SecondaryButton>
              <Link to={`/learn/${result.videoId}`} onClick={() => handleOpenChange(false)}>
                <PrimaryButton>
                  <Play className="h-3.5 w-3.5" /> Open lecture
                </PrimaryButton>
              </Link>
            </>
          ) : (
            <>
              <SecondaryButton onClick={() => handleOpenChange(false)}>Cancel</SecondaryButton>
              <PrimaryButton loading={submitting} disabled={!canSubmit} onClick={() => void handleSubmit()}>
                {mode === 'upload' ? 'Upload lecture' : 'Import lecture'}
              </PrimaryButton>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

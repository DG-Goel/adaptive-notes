import { useState } from 'react'
import { Download, FileCode2, FileText, Loader2, TriangleAlert } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useNotesExportCapabilities } from '@/hooks/use-lecture-queries'
import { noteDocumentToHtml } from '@/lib/notes/html-export'
import { noteDocumentToMarkdown } from '@/lib/notes/markdown'
import { requestNotesExport } from '@/services/api'
import { cn } from '@/lib/utils'
import type { NoteDocument, NotesExportFormat } from '@/types/notes'

/**
 * Notes export.
 *
 * Markdown and sanitised HTML are produced on the client from the document the
 * reader is actually looking at, and downloaded for real. PDF and DOCX depend
 * on a server renderer: when the service reports they are unavailable the item
 * is disabled with the reason shown, and when a request is made the outcome is
 * whatever the API returned — a failure is reported as a failure.
 */

const CLIENT_FORMATS: readonly NotesExportFormat[] = ['markdown', 'html']

function triggerDownload(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

function safeFilename(title: string, extension: string): string {
  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
  return `${slug || 'notes'}.${extension}`
}

export interface NotesExportMenuProps {
  videoId: string
  document: NoteDocument
  className?: string
}

export function NotesExportMenu({ videoId, document, className }: NotesExportMenuProps) {
  const { data: capabilities, isError, error, refetch } = useNotesExportCapabilities(videoId)
  const [pending, setPending] = useState<NotesExportFormat | null>(null)
  const [message, setMessage] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null)

  const exportOnClient = (format: NotesExportFormat) => {
    if (format === 'markdown') {
      triggerDownload(safeFilename(document.title, 'md'), noteDocumentToMarkdown(document), 'text/markdown')
      setMessage({ tone: 'ok', text: 'Markdown downloaded from the notes on screen.' })
      return
    }
    triggerDownload(
      safeFilename(document.title, 'html'),
      noteDocumentToHtml(document),
      'text/html',
    )
    setMessage({ tone: 'ok', text: 'Sanitised HTML downloaded from the notes on screen.' })
  }

  const exportOnServer = async (format: NotesExportFormat) => {
    setPending(format)
    setMessage(null)
    try {
      const payload = format === 'html' ? noteDocumentToHtml(document) : noteDocumentToMarkdown(document)
      const result = await requestNotesExport(videoId, format, payload)
      if (result.downloadUrl) {
        window.open(result.downloadUrl, '_blank', 'noopener')
        setMessage({ tone: 'ok', text: `The service returned a ${format.toUpperCase()} download.` })
      } else if (result.content) {
        triggerDownload(result.filename ?? safeFilename(document.title, format), result.content, 'application/octet-stream')
        setMessage({ tone: 'ok', text: `The service returned a ${format.toUpperCase()} file.` })
      } else {
        setMessage({
          tone: 'error',
          text: `The service reported success for ${format.toUpperCase()} but returned no file.`,
        })
      }
    } catch (caught) {
      setMessage({
        tone: 'error',
        text: caught instanceof Error ? caught.message : `${format.toUpperCase()} export failed.`,
      })
    } finally {
      setPending(null)
    }
  }

  return (
    <div className={cn('flex flex-col items-end gap-1', className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border px-2.5 text-[12px] font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Download className="h-3.5 w-3.5" />
            Export
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-72">
          <DropdownMenuLabel className="text-[11px] uppercase tracking-wide text-muted-foreground">
            From the notes on screen
          </DropdownMenuLabel>
          <DropdownMenuItem
            onSelect={() => exportOnClient('markdown')}
            className="gap-2 text-[13px]"
          >
            <FileText className="h-3.5 w-3.5 text-accent" />
            Markdown (.md)
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => exportOnClient('html')} className="gap-2 text-[13px]">
            <FileCode2 className="h-3.5 w-3.5 text-accent" />
            Sanitised HTML (.html)
          </DropdownMenuItem>

          <DropdownMenuSeparator />
          <DropdownMenuLabel className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Server-rendered
          </DropdownMenuLabel>

          {isError && (
            <div className="px-2 py-2 text-[11px] leading-relaxed text-muted-foreground">
              {error instanceof Error
                ? error.message
                : 'Export capabilities could not be loaded from the API.'}{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium text-accent hover:underline"
              >
                Retry
              </button>
            </div>
          )}

          {!isError &&
            (capabilities ?? [])
              .filter((capability) => !CLIENT_FORMATS.includes(capability.format))
              .map((capability) => {
                const busy = pending === capability.format
                return (
                  <DropdownMenuItem
                    key={capability.format}
                    disabled={!capability.available || busy}
                    onSelect={(event) => {
                      if (!capability.available) {
                        event.preventDefault()
                        return
                      }
                      // Keep the menu open so the outcome is visible in place.
                      event.preventDefault()
                      void exportOnServer(capability.format)
                    }}
                    className="flex flex-col items-start gap-0.5 text-[13px]"
                  >
                    <span className="flex items-center gap-2">
                      {busy ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                      ) : capability.available ? (
                        <Download className="h-3.5 w-3.5 text-muted-foreground" />
                      ) : (
                        <TriangleAlert className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                      {capability.label}
                    </span>
                    {!capability.available && capability.reason && (
                      <span className="pl-5 text-[11px] text-muted-foreground">{capability.reason}</span>
                    )}
                  </DropdownMenuItem>
                )
              })}

          {!isError && !capabilities && (
            <div className="px-2 py-2 text-[11px] text-muted-foreground">
              Checking which formats the service supports…
            </div>
          )}

          {document.isDemonstration && (
            <>
              <DropdownMenuSeparator />
              <p className="px-2 py-1.5 text-[11px] leading-relaxed text-muted-foreground">
                Demonstrations are labelled in the exported file: these are hand-written sample notes, not
                generated output.
              </p>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {message && (
        <p
          role="status"
          className={cn(
            'max-w-xs text-right text-[11px] leading-relaxed',
            message.tone === 'error' ? 'text-destructive' : 'text-muted-foreground',
          )}
        >
          {message.text}
        </p>
      )}
    </div>
  )
}

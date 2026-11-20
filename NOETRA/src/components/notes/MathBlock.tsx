import { useMemo, useState } from 'react'
import { Check, Copy, Sigma } from 'lucide-react'
import { renderLatex } from '@/lib/notes/katex'
import { metaExtras } from '@/lib/notes/blocks'
import { cn } from '@/lib/utils'

/**
 * KaTeX equation renderer.
 *
 * Inline equations flow with the text; block equations get a framed card with
 * the LaTeX source available for copying. Malformed LaTeX falls back to the
 * source plus the parser message, so a bad equation never blanks the document.
 */
export interface MathBlockProps {
  latex: string
  displayMode: 'inline' | 'block'
  description?: string
  meta?: Record<string, unknown>
  className?: string
}

export function MathBlock({ latex, displayMode, description, meta, className }: MathBlockProps) {
  const display = displayMode === 'block'
  const { html, error } = useMemo(() => renderLatex(latex, display), [latex, display])
  const [copied, setCopied] = useState(false)
  const extras = useMemo(() => metaExtras(meta), [meta])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(latex)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  if (!display) {
    return (
      <p className={cn('my-2 text-sm leading-relaxed text-foreground/85', className)}>
        {error ? (
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-accent">
            {latex}
          </code>
        ) : (
          <span className="mx-0.5 inline-block align-middle" dangerouslySetInnerHTML={{ __html: html }} />
        )}
        {description && <span className="ml-2 text-xs text-muted-foreground">({description})</span>}
        {error && (
          <span className="ml-2 text-xs text-muted-foreground">Inline equation — {error}</span>
        )}
      </p>
    )
  }

  return (
    <figure className={cn('my-4 rounded-xl border border-border bg-card shadow-soft', className)}>
      <figcaption className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-2">
        <span className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Sigma className="h-3.5 w-3.5 text-accent" />
          Equation
        </span>
        <button
          type="button"
          onClick={() => void handleCopy()}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy LaTeX'}
        </button>
      </figcaption>

      <div className="px-4 py-4">
        {error ? (
          <div>
            <pre className="note-code overflow-x-auto rounded-lg border border-white/10 bg-sidebar px-3 py-2 font-mono text-[12.5px] text-sidebar-foreground">
              {latex}
            </pre>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              This expression could not be typeset: {error}
            </p>
          </div>
        ) : (
          <div
            className="overflow-x-auto text-center text-foreground"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        )}
      </div>

      {(description || extras.length > 0) && (
        <figcaption className="border-t border-border px-4 py-2.5">
          {description && <p className="text-xs leading-relaxed text-muted-foreground">{description}</p>}
          {extras.length > 0 && (
            <dl className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
              {extras.map((entry) => (
                <div key={entry.key} className="flex items-baseline gap-1.5">
                  <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">{entry.key}</dt>
                  <dd className="text-xs text-foreground/80">{entry.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </figcaption>
      )}
    </figure>
  )
}

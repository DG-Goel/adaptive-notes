import { useMemo } from 'react'
import { Check, Code2, Copy } from 'lucide-react'
import { highlightCode, normalizeLanguage, SUPPORTED_LANGUAGES } from '@/lib/notes/highlight'
import { metaExtras } from '@/lib/notes/blocks'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import { cn } from '@/lib/utils'

/**
 * Syntax-highlighted code block.
 *
 * Highlighting is computed once per (language, source) pair by the memoised
 * helper, so search highlighting and reading-mode changes never re-run the
 * grammar. Unknown languages fall back to escaped plain text with an explicit
 * label rather than silently pretending to highlight.
 */
export interface CodeBlockProps {
  code: string
  language?: string
  title?: string
  meta?: Record<string, unknown>
  className?: string
}

export function CodeBlock({ code, language, title, meta, className }: CodeBlockProps) {
  const { html, language: resolved } = useMemo(() => highlightCode(code, language), [code, language])
  const { copied, copy } = useCopyToClipboard()
  const extras = useMemo(() => metaExtras(meta), [meta])

  const requested = normalizeLanguage(language)
  const languageLabel = resolved
    ? resolved
    : language?.trim()
      ? `${language.trim()} · not highlighted`
      : 'Text'

  return (
    <figure
      className={cn(
        'note-code my-4 overflow-hidden rounded-xl border border-white/10 bg-sidebar shadow-soft',
        className,
      )}
    >
      <figcaption className="flex items-center justify-between gap-2 border-b border-white/10 px-3.5 py-2">
        <span className="flex min-w-0 items-center gap-2 text-[11px] font-medium text-sidebar-foreground/70">
          <Code2 className="h-3.5 w-3.5 text-accent" aria-hidden />
          <span className="truncate">{title ?? languageLabel}</span>
          {title && <span className="shrink-0 text-sidebar-foreground/45">· {languageLabel}</span>}
        </span>
        <button
          type="button"
          onClick={() => void copy(code)}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-sidebar-foreground/70 transition-colors hover:bg-white/10 hover:text-sidebar-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </figcaption>

      <pre className="overflow-x-auto px-4 py-3.5 font-mono text-[12.5px] leading-relaxed text-sidebar-foreground">
        <code dangerouslySetInnerHTML={{ __html: html }} />
      </pre>

      {(requested === null || extras.length > 0) && (
        <figcaption className="border-t border-white/10 px-3.5 py-2 text-[11px] leading-relaxed text-sidebar-foreground/55">
          {requested === null && (
            <p>
              This build highlights {SUPPORTED_LANGUAGES.join(', ')}. The source is shown unchanged.
            </p>
          )}
          {extras.length > 0 && (
            <dl className="flex flex-wrap gap-x-4 gap-y-1">
              {extras.map((entry) => (
                <div key={entry.key} className="flex items-baseline gap-1.5">
                  <dt className="uppercase tracking-wide text-sidebar-foreground/45">{entry.key}</dt>
                  <dd>{entry.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </figcaption>
      )}
    </figure>
  )
}

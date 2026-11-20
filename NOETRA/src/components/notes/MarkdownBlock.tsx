import { Children, isValidElement, memo } from 'react'
import type { ReactNode } from 'react'
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { CodeBlock } from './CodeBlock'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import { Check, Copy } from 'lucide-react'
import { TimestampTextNodes } from './InlineMarkdown'
import { cn } from '@/lib/utils'

/**
 * Markdown block.
 *
 * Rendered with react-markdown + remark-gfm, plus remark-math/rehype-katex for
 * LaTeX. Two properties matter here:
 *
 * - Raw HTML is never rendered as HTML. react-markdown has no `rehype-raw`
 *   plugin, so `<script>` in a note is displayed as literal text — nothing is
 *   injected, and nothing is silently dropped either.
 * - `[mm:ss]` markers anywhere in the prose become seekable timestamp chips.
 */

/** Pull the fenced block's language and source out of react-markdown's tree. */
function MarkdownCodeSurface({ children }: { children?: ReactNode }) {
  const [first] = Children.toArray(children)
  const className = isValidElement<{ className?: string }>(first) ? first.props.className : undefined
  const language = typeof className === 'string' ? className.replace('language-', '') : undefined
  const code = isValidElement<{ children?: ReactNode }>(first)
    ? String(first.props.children ?? '').replace(/\n$/, '')
    : ''
  return <CodeBlock code={code} language={language} />
}

function MarkdownTable({ children }: { children?: ReactNode }) {
  return (
    <div className="my-4 overflow-x-auto rounded-xl border border-border">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  )
}

const components: Components = {
  h1: ({ children }) => (
    <h1 className="mt-6 mb-3 font-serif text-2xl font-medium tracking-tight text-foreground">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-6 mb-2 font-serif text-xl font-medium tracking-tight text-foreground">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-5 mb-2 font-serif text-lg font-medium text-foreground">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="mt-4 mb-1.5 text-sm font-semibold text-foreground">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </h4>
  ),
  p: ({ children }) => (
    <p className="my-3 text-sm leading-relaxed text-foreground/85">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </p>
  ),
  ul: ({ children }) => <ul className="my-3 space-y-1.5 pl-1">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal space-y-1.5 pl-5">{children}</ol>,
  li: ({ children }) => (
    <li className="text-sm leading-relaxed text-foreground/85 marker:text-accent [ul>&]:flex [ul>&]:gap-2.5 [ul>&]:before:mt-[0.45rem] [ul>&]:before:h-1.5 [ul>&]:before:w-1.5 [ul>&]:before:shrink-0 [ul>&]:before:rounded-full [ul>&]:before:bg-accent/60 [ul>&]:before:content-['']">
      <div className="min-w-0"><TimestampTextNodes>{children}</TimestampTextNodes></div>
    </li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-4 rounded-r-xl border-l-2 border-accent/50 bg-accent/[0.05] py-2 pr-3 pl-4 text-sm text-foreground/80">
      {children}
    </blockquote>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-foreground">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </strong>
  ),
  em: ({ children }) => (
    <em className="italic">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </em>
  ),
  del: ({ children }) => <del className="text-muted-foreground line-through">{children}</del>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-6 border-border" />,
  img: ({ src, alt }) => (
    <img
      src={src}
      alt={alt ?? ''}
      loading="lazy"
      className="my-4 max-w-full rounded-xl border border-border"
    />
  ),
  table: ({ children }) => <MarkdownTable>{children}</MarkdownTable>,
  thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
  th: ({ children }) => (
    <th
      scope="col"
      className="border-b border-border px-3.5 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
    >
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </th>
  ),
  td: ({ children }) => (
    <td className="border-b border-border/60 px-3.5 py-2.5 align-top text-foreground/85 break-words">
      <TimestampTextNodes>{children}</TimestampTextNodes>
    </td>
  ),
  pre: ({ children }) => <MarkdownCodeSurface>{children}</MarkdownCodeSurface>,
  code: ({ children, className }) => {
    if (typeof className === 'string' && className.includes('language-')) return <>{children}</>
    return (
      <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-accent">
        {children}
      </code>
    )
  },
  input: ({ checked, type }) =>
    type === 'checkbox' ? (
      <input
        type="checkbox"
        checked={Boolean(checked)}
        readOnly
        aria-hidden
        tabIndex={-1}
        className="mr-2 h-3.5 w-3.5 shrink-0 translate-y-[2px] accent-[hsl(var(--accent))]"
      />
    ) : null,
}

/** Inline Markdown wrapped in copy-friendly styling, used where nesting is flat. */
function MarkdownSurface({ content, className }: { content: string; className?: string }) {
  const { copied, copy } = useCopyToClipboard()

  return (
    <div className={cn('group relative', className)}>
      <button
        type="button"
        onClick={() => void copy(content)}
        aria-label="Copy this block as Markdown"
        className="absolute -top-1 right-0 z-[1] inline-flex items-center gap-1 rounded-md border border-transparent px-1.5 py-1 text-[10px] font-medium text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover:opacity-100"
      >
        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      </button>
      <Markdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { strict: 'ignore' }]]}
        components={components}
      >
        {content}
      </Markdown>
    </div>
  )
}

export interface MarkdownBlockProps {
  content: string
  className?: string
}

/**
 * Memoised: a markdown block re-renders on every search highlight and reading
 * mode change, while its source does not change.
 */
export const MarkdownBlock = memo(function MarkdownBlock({ content, className }: MarkdownBlockProps) {
  return <MarkdownSurface content={content} className={className} />
})

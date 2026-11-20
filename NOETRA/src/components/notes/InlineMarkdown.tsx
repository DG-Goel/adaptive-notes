import type { ReactNode } from 'react'
import { TimestampChip } from '@/components/video/TimestampText'
import { parseTimestamp } from '@/lib/timestamps'
import { cn } from '@/lib/utils'

/**
 * Inline Markdown for note text.
 *
 * Note text is short and lives inside headings, list items, callouts and table
 * cells, so it is tokenised here instead of mounting a full Markdown renderer
 * per fragment. Because every token becomes a React element, raw HTML in the
 * source can never be injected — `<script>` in a note simply renders as text.
 *
 * `[mm:ss]` markers become real timestamp chips, which seek the shared player
 * when one is mounted and deep-link to the lecture when it is not.
 */

const INLINE_TOKEN =
  /(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`|\[[^\]\n]+\]\([^)\s]+\)|\[(?:\d{1,2}:)?\d{1,2}:\d{2}\])/g

/** Only link targets that cannot execute script are rendered as links. */
const SAFE_HREF = /^(?:https?:\/\/|mailto:|\/|#)/i

function renderToken(token: string, key: number): ReactNode {
  if (token.startsWith('**')) {
    return (
      <strong key={key} className="font-semibold text-foreground">
        {token.slice(2, -2)}
      </strong>
    )
  }

  if (token.startsWith('`')) {
    return (
      <code key={key} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-accent">
        {token.slice(1, -1)}
      </code>
    )
  }

  if (token.startsWith('[') && token.includes('](')) {
    const split = token.indexOf('](')
    const label = token.slice(1, split)
    const href = token.slice(split + 2, -1)
    if (!SAFE_HREF.test(href)) return <span key={key}>{label}</span>
    return (
      <a
        key={key}
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
      >
        {label}
      </a>
    )
  }

  if (token.startsWith('*')) {
    return (
      <em key={key} className="italic">
        {token.slice(1, -1)}
      </em>
    )
  }

  const seconds = parseTimestamp(token)
  if (seconds === null) return <span key={key}>{token}</span>
  return <TimestampChip key={key} seconds={seconds} label={token.slice(1, -1)} />
}

/** Replace `[mm:ss]` markers inside already-parsed React children with chips. */
function withTimestampNodes(children: ReactNode): ReactNode {
  if (typeof children === 'string') {
    const parts: ReactNode[] = []
    const pattern = new RegExp(INLINE_TOKEN.source, 'g')
    let cursor = 0
    let match = pattern.exec(children)
    while (match) {
      const token = match[0]
      const seconds = token.startsWith('[') && !token.includes('](') ? parseTimestamp(token) : null
      if (seconds === null) {
        match = pattern.exec(children)
        continue
      }
      if (match.index > cursor) parts.push(children.slice(cursor, match.index))
      parts.push(<TimestampChip key={match.index} seconds={seconds} label={token.slice(1, -1)} />)
      cursor = match.index + token.length
      match = pattern.exec(children)
    }
    if (parts.length === 0) return children
    if (cursor < children.length) parts.push(children.slice(cursor))
    return parts
  }

  if (Array.isArray(children)) return children.map((child) => withTimestampNodes(child))
  return children
}

export interface TimestampTextNodesProps {
  children?: ReactNode
}

/**
 * Children that a Markdown renderer has already parsed, with any `[mm:ss]`
 * marker inside their text turned into a seekable chip.
 */
export function TimestampTextNodes({ children }: TimestampTextNodesProps) {
  return <>{withTimestampNodes(children)}</>
}

export interface InlineMarkdownProps {
  text: string
  className?: string
}

export function InlineMarkdown({ text, className }: InlineMarkdownProps) {
  const pattern = new RegExp(INLINE_TOKEN.source, 'g')
  const parts: ReactNode[] = []
  let cursor = 0
  let match = pattern.exec(text)

  while (match) {
    if (match.index > cursor) parts.push(text.slice(cursor, match.index))
    parts.push(renderToken(match[0], match.index))
    cursor = match.index + match[0].length
    match = pattern.exec(text)
  }

  if (cursor < text.length) parts.push(text.slice(cursor))

  return <span className={cn(className)}>{parts.length > 0 ? parts : text}</span>
}

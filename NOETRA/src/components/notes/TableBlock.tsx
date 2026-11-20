import { useMemo } from 'react'
import { Check, Copy, Download, Table2 } from 'lucide-react'
import { CodeBlock } from './CodeBlock'
import { InlineMarkdown } from './InlineMarkdown'
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'
import { metaExtras } from '@/lib/notes/blocks'
import { tableBlockToCsv, tableBlockToMarkdown } from '@/lib/notes/markdown'
import { parseGfmTable, type CellAlign, type NormalisedTable } from '@/lib/notes/tables'
import { cn } from '@/lib/utils'
import type { NoteTableBlock } from '@/types/notes'

/**
 * Table block.
 *
 * Two source formats are supported, but only one renderer is used: GFM source
 * is parsed into the same structure the `structured` payload already has, so
 * alignment, wrapping, copy and CSV behave identically either way. Tables
 * scroll horizontally inside their own frame, which keeps a wide table from
 * forcing the page to overflow.
 */

function normalize(block: NoteTableBlock): NormalisedTable | null {
  if (block.format === 'markdown') {
    if (!block.markdown) return null
    return parseGfmTable(block.markdown)
  }

  const columns = block.columns ?? []
  if (columns.length === 0) return null
  const rows = block.rows ?? []
  return {
    headers: columns.map((column) => column.header),
    aligns: columns.map((column) => column.align ?? 'left'),
    rows: rows.map((row) => columns.map((_, index) => row.cells[index] ?? '')),
    rowIds: rows.map((row) => row.id),
  }
}

const ALIGN_CLASSES: Record<CellAlign, string> = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
}

function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

function safeFilename(title: string): string {
  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
  return `${slug || 'table'}.csv`
}

export interface TableBlockProps {
  block: NoteTableBlock
  className?: string
}

export function TableBlock({ block, className }: TableBlockProps) {
  const { copied, copy } = useCopyToClipboard()
  const extras = useMemo(() => metaExtras(block.meta), [block.meta])
  const table = useMemo(() => normalize(block), [block])
  const markdown = useMemo(() => tableBlockToMarkdown(block), [block])
  const csv = useMemo(() => tableBlockToCsv(block), [block])

  if (!table) {
    // Nothing renderable — show the source honestly instead of an empty frame.
    return block.markdown ? (
      <CodeBlock code={block.markdown} language="markdown" title={block.caption ?? 'Table source'} />
    ) : (
      <div className="my-4 rounded-xl border border-dashed border-border bg-muted/30 px-4 py-3 text-xs text-muted-foreground">
        This table artifact arrived without columns or Markdown source.
      </div>
    )
  }

  const title = block.caption ?? 'Table'
  const actions = (
    <div className="flex shrink-0 items-center gap-1">
      <button
        type="button"
        onClick={() => void copy(markdown)}
        className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        {copied ? 'Copied' : 'Copy'}
      </button>
      {csv && (
        <button
          type="button"
          onClick={() => downloadCsv(safeFilename(title), csv)}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Download className="h-3 w-3" />
          CSV
        </button>
      )}
    </div>
  )

  return (
    <figure className={cn('my-4 overflow-hidden rounded-xl border border-border bg-card shadow-soft', className)}>
      <figcaption className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-2">
        <span className="flex min-w-0 items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Table2 className="h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />
          <span className="truncate">{title}</span>
        </span>
        {actions}
      </figcaption>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[28rem] border-collapse text-sm">
          <thead className="bg-muted/50">
            <tr>
              {table.headers.map((header, index) => (
                <th
                  key={`${header}-${index}`}
                  scope="col"
                  className={cn(
                    'border-b border-border px-3.5 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground',
                    ALIGN_CLASSES[table.aligns[index] ?? 'left'],
                  )}
                >
                  <InlineMarkdown text={header} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr key={table.rowIds[rowIndex] ?? rowIndex} className="odd:bg-muted/20">
                {table.headers.map((_, cellIndex) => (
                  <td
                    key={cellIndex}
                    className={cn(
                      'max-w-[22rem] border-b border-border/60 px-3.5 py-2.5 align-top text-foreground/85 break-words',
                      ALIGN_CLASSES[table.aligns[cellIndex] ?? 'left'],
                    )}
                  >
                    <InlineMarkdown text={row[cellIndex] ?? ''} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(extras.length > 0 || block.sourceBlockId) && (
        <figcaption className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          <dl className="flex flex-wrap gap-x-4 gap-y-1">
            {block.sourceBlockId && (
              <div className="flex items-baseline gap-1.5">
                <dt className="uppercase tracking-wide">derived from</dt>
                <dd className="font-mono">{block.sourceBlockId}</dd>
              </div>
            )}
            {extras.map((entry) => (
              <div key={entry.key} className="flex items-baseline gap-1.5">
                <dt className="uppercase tracking-wide">{entry.key}</dt>
                <dd>{entry.value}</dd>
              </div>
            ))}
          </dl>
        </figcaption>
      )}
    </figure>
  )
}

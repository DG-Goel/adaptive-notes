/**
 * Client-side HTML export for a note document.
 *
 * Every string is escaped or produced by the escaping Markdown converter, so
 * the output contains no note-supplied markup — it is a sanitised
 * representation, not a dump of raw note HTML. Visual artifacts keep a
 * readable representation instead of being dropped (tables become real
 * tables, flowcharts and diagrams list their nodes and edges, equations keep
 * their LaTeX source).
 */

import { inlineMarkdownToHtml, markdownToHtml } from './markdown-html'
import { parseGfmTable } from './tables'
import { timestampLabel } from '@/lib/timestamps'
import type { NoteBlock, NoteDocument, NoteListItem, NoteSection } from '@/types/notes'

const ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"]/g, (character) => ESCAPES[character] ?? character)
}

function stamp(block: NoteBlock): string {
  return typeof block.startSeconds === 'number'
    ? ` <span class="ts">[${timestampLabel(block.startSeconds)}]</span>`
    : ''
}

function listItemsToHtml(items: NoteListItem[], ordered: boolean): string {
  const tag = ordered ? 'ol' : 'ul'
  const body = items
    .map((item) => {
      const nested = item.items && item.items.length > 0 ? listItemsToHtml(item.items, ordered) : ''
      return `<li>${inlineMarkdownToHtml(item.content)}${nested}</li>`
    })
    .join('')
  return `<${tag}>${body}</${tag}>`
}

function tableToHtml(block: Extract<NoteBlock, { type: 'table' }>): string {
  const parsed =
    block.format === 'markdown' && block.markdown
      ? parseGfmTable(block.markdown)
      : null

  const headers = parsed?.headers ?? (block.columns ?? []).map((column) => column.header)
  const rows =
    parsed?.rows ??
    (block.rows ?? []).map((row) => (block.columns ?? []).map((_, index) => row.cells[index] ?? ''))

  if (headers.length === 0) {
    return block.markdown
      ? `<pre class="source">${escapeHtml(block.markdown)}</pre>`
      : '<p class="empty">This table artifact arrived without columns or Markdown source.</p>'
  }

  const head = headers.map((header) => `<th>${inlineMarkdownToHtml(header)}</th>`).join('')
  const body = rows
    .map(
      (row) =>
        `<tr>${headers
          .map((_, index) => `<td>${inlineMarkdownToHtml(row[index] ?? '')}</td>`)
          .join('')}</tr>`,
    )
    .join('')

  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
}

function blockToHtml(block: NoteBlock): string {
  switch (block.type) {
    case 'markdown':
    case 'paragraph':
      return `${markdownToHtml(block.content)}${stamp(block)}`
    case 'heading': {
      const level = Math.min(6, block.level + 1)
      return `<h${level}>${inlineMarkdownToHtml(block.content)}${stamp(block)}</h${level}>`
    }
    case 'list':
      return `${listItemsToHtml(block.items, block.ordered)}${stamp(block)}`
    case 'quote':
      return `<blockquote>${markdownToHtml(block.content)}${
        block.attribution ? `<footer>— ${escapeHtml(block.attribution)}</footer>` : ''
      }</blockquote>${stamp(block)}`
    case 'callout':
      return `<aside class="callout"><p><strong>${escapeHtml(
        block.title ?? block.tone,
      )}</strong></p>${markdownToHtml(block.content)}</aside>${stamp(block)}`
    case 'code':
      return `<figure class="code">${
        block.title ? `<figcaption>${escapeHtml(block.title)}</figcaption>` : ''
      }<pre><code class="language-${escapeHtml(block.language ?? 'text')}">${escapeHtml(
        block.content,
      )}</code></pre></figure>${stamp(block)}`
    case 'math':
      return `<figure class="math"><pre>${escapeHtml(block.latex)}</pre><figcaption>${escapeHtml(
        block.description ?? 'LaTeX equation',
      )}</figcaption></figure>${stamp(block)}`
    case 'table':
      return `<figure class="table">${
        block.caption ? `<figcaption>${inlineMarkdownToHtml(block.caption)}</figcaption>` : ''
      }${tableToHtml(block)}</figure>${stamp(block)}`
    case 'flowchart': {
      const nodes = block.nodes.map((node) => escapeHtml(node.label)).join(' → ')
      const edges = block.edges
        .map((edge) => {
          const source = block.nodes.find((node) => node.id === edge.source)?.label ?? edge.source
          const target = block.nodes.find((node) => node.id === edge.target)?.label ?? edge.target
          return `${escapeHtml(source)} → ${escapeHtml(target)}${
            edge.label ? ` (${escapeHtml(edge.label)})` : ''
          }`
        })
        .join('; ')
      return `<figure class="diagram"><figcaption>${escapeHtml(
        block.caption ?? 'Flowchart',
      )} <em>(interactive flowchart)</em></figcaption><p>Steps: ${nodes}</p>${
        edges ? `<p>Links: ${edges}</p>` : ''
      }</figure>${stamp(block)}`
    }
    case 'diagram': {
      const caption = escapeHtml(block.caption ?? 'Diagram')
      if (block.format === 'image' && block.src) {
        return `<figure class="diagram"><img src="${escapeHtml(
          block.src,
        )}" alt="${caption}"><figcaption>${caption}</figcaption></figure>${stamp(block)}`
      }
      if (block.format === 'flow' && block.nodes && block.nodes.length > 0) {
        return `<figure class="diagram"><figcaption>${caption}</figcaption><p>Steps: ${block.nodes
          .map((node) => escapeHtml(node.label))
          .join(' → ')}</p></figure>${stamp(block)}`
      }
      if (block.source) {
        return `<figure class="diagram"><figcaption>${caption} (${escapeHtml(
          block.format,
        )} source)</figcaption><pre class="source">${escapeHtml(
          block.source,
        )}</pre></figure>${stamp(block)}`
      }
      return `<figure class="diagram"><figcaption>${caption}</figcaption><p class="empty">Diagram format “${escapeHtml(
        block.format,
      )}” is not supported by this export.</p></figure>${stamp(block)}`
    }
    case 'image':
      return `<figure><img src="${escapeHtml(block.src)}" alt="${escapeHtml(
        block.alt,
      )}">${block.caption ? `<figcaption>${escapeHtml(block.caption)}</figcaption>` : ''}</figure>${stamp(
        block,
      )}`
    case 'unknown':
      return `<aside class="unsupported">Unsupported artifact from the backend: <code>${escapeHtml(
        block.originalType,
      )}</code>. Its original payload is preserved in the note data.</aside>`
    default:
      return ''
  }
}

function sectionToHtml(section: NoteSection): string {
  const blocks = section.blocks.map(blockToHtml).filter(Boolean).join('\n')
  const stampText =
    typeof section.startSeconds === 'number'
      ? ` <span class="ts">[${timestampLabel(section.startSeconds)}]</span>`
      : ''
  return `<section id="${escapeHtml(section.id)}"><h2>${escapeHtml(section.title)}${stampText}</h2>\n${blocks}</section>`
}

const STYLES = `
  :root { color-scheme: light; }
  body { margin: 0 auto; max-width: 46rem; padding: 3rem 1.5rem 5rem; background: #F7F4EF; color: #252422;
    font: 16px/1.65 "DM Sans", system-ui, sans-serif; }
  h1, h2 { font-family: "Instrument Serif", Georgia, serif; font-weight: 500; letter-spacing: -0.01em; }
  h1 { font-size: 2.25rem; margin-bottom: 0.25rem; }
  h2 { font-size: 1.4rem; margin-top: 2.5rem; border-top: 1px solid #DED8D0; padding-top: 1.25rem; }
  h3, h4, h5, h6 { font-size: 1.05rem; margin-top: 1.5rem; }
  .subtitle { color: #817C75; margin-top: 0; }
  .notice { border: 1px solid #DED8D0; border-left: 3px solid #D65A16; background: #EEE9E2;
    padding: 0.75rem 1rem; border-radius: 0.5rem; color: #817C75; font-size: 0.85rem; }
  .ts { color: #D65A16; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8em; }
  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  th, td { border: 1px solid #DED8D0; padding: 0.5rem 0.7rem; text-align: left; vertical-align: top; }
  th { background: #EEE9E2; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.06em; }
  pre { background: #252525; color: #F1EDE7; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; }
  pre.source { background: #EEE9E2; color: #252422; }
  blockquote, aside { border-left: 3px solid #D65A16; background: #F1EDE7; margin: 1rem 0;
    padding: 0.75rem 1rem; border-radius: 0 0.5rem 0.5rem 0; }
  aside.unsupported { border-left-style: dashed; border-color: #817C75; }
  figure { margin: 1.25rem 0; }
  figcaption { color: #817C75; font-size: 0.8rem; margin-bottom: 0.35rem; }
  img { max-width: 100%; border-radius: 0.5rem; }
  .empty { color: #817C75; font-style: italic; }
  footer { color: #817C75; font-size: 0.85rem; }
`

/**
 * Render a note document as a standalone, self-contained HTML page.
 * The result contains no scripts and no note-supplied markup.
 */
export function noteDocumentToHtml(document: NoteDocument): string {
  const header = [
    `<h1>${escapeHtml(document.title)}</h1>`,
    document.subtitle ? `<p class="subtitle">${escapeHtml(document.subtitle)}</p>` : '',
    document.isDemonstration
      ? '<p class="notice">Demonstration notes. This document is deterministic sample content shipped with the demo build — it was not generated from the sample video.</p>'
      : '',
  ]
    .filter(Boolean)
    .join('\n')

  const unplaced = document.unplacedArtifacts ?? []
  const unplacedHtml =
    unplaced.length > 0
      ? `<section><h2>Unplaced visual artifacts</h2><p class="empty">These artifacts arrived without placement metadata, so they are listed here instead of being inserted at an estimated position.</p><ul>${unplaced
          .map(
            (artifact) =>
              `<li><strong>${escapeHtml(artifact.title)}</strong> (${escapeHtml(
                artifact.kind,
              )}) — ${escapeHtml(artifact.description)}</li>`,
          )
          .join('')}</ul></section>`
      : ''

  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${escapeHtml(document.title)}</title>`,
    `<style>${STYLES}</style>`,
    '</head>',
    '<body>',
    header,
    ...document.sections.map(sectionToHtml),
    unplacedHtml,
    '</body>',
    '</html>',
  ]
    .filter(Boolean)
    .join('\n')
}

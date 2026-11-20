/**
 * Bidirectional conversion between the Markdown subset stored in note blocks
 * and the HTML the rich-text editor produces.
 *
 * The scope is deliberately narrow — headings, paragraphs, bullet/numbered
 * lists (with nesting), blockquotes, fenced code and inline
 * emphasis/code/links. Heavier Markdown constructs live in dedicated block
 * types (table, math, code, flowchart), so this converter never has to guess
 * at them and can round-trip its own output exactly.
 */

import type {
  EditableNoteBlock,
  NoteBlock,
  NoteHeadingBlock,
  NoteListItem,
  NoteListBlock,
} from '@/types/notes'

/* ------------------------------------------------------------------ *
 * Inline level
 * ------------------------------------------------------------------ */

const INLINE_TOKEN = /(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`|\[[^\]\n]+\]\([^)\s]+\))/g

const HTML_ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"]/g, (character) => HTML_ESCAPES[character] ?? character)
}

/** Escape only the characters that would otherwise start an inline marker. */
function escapeMarkdown(text: string): string {
  return text.replace(/[*`]/g, '\\$&')
}

function unescapeMarkdown(text: string): string {
  return text.replace(/\\([*`])/g, '$1')
}

function inlineTokenToHtml(token: string): string {
  if (token.startsWith('**')) {
    return `<strong>${escapeHtml(unescapeMarkdown(token.slice(2, -2)))}</strong>`
  }
  if (token.startsWith('`')) {
    return `<code>${escapeHtml(unescapeMarkdown(token.slice(1, -1)))}</code>`
  }
  if (token.startsWith('[')) {
    const split = token.indexOf('](')
    const label = token.slice(1, split)
    const href = token.slice(split + 2, -1)
    return `<a href="${escapeHtml(href)}">${escapeHtml(unescapeMarkdown(label))}</a>`
  }
  return `<em>${escapeHtml(unescapeMarkdown(token.slice(1, -1)))}</em>`
}

/** Convert the inline Markdown subset of `text` into safe HTML. */
export function inlineMarkdownToHtml(text: string): string {
  const pattern = new RegExp(INLINE_TOKEN.source, 'g')
  let html = ''
  let cursor = 0
  let match = pattern.exec(text)
  while (match) {
    if (match.index > cursor) {
      html += escapeHtml(unescapeMarkdown(text.slice(cursor, match.index)))
    }
    html += inlineTokenToHtml(match[0])
    cursor = match.index + match[0].length
    match = pattern.exec(text)
  }
  if (cursor < text.length) html += escapeHtml(unescapeMarkdown(text.slice(cursor)))
  return html
}

function inlineHtmlToMarkdown(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) return escapeMarkdown(node.textContent ?? '')
  if (!(node instanceof HTMLElement)) return ''
  const inner = Array.from(node.childNodes).map(inlineHtmlToMarkdown).join('')
  const trimmed = inner.trim()
  switch (node.tagName) {
    case 'STRONG':
    case 'B':
      return trimmed ? `**${trimmed}**` : inner
    case 'EM':
    case 'I':
      return trimmed ? `*${trimmed}*` : inner
    case 'CODE':
      return trimmed ? `\`${trimmed}\`` : inner
    case 'A': {
      const href = node.getAttribute('href')
      return href && trimmed ? `[${trimmed}](${href})` : inner
    }
    case 'BR':
      return ' '
    default:
      return inner
  }
}

/* ------------------------------------------------------------------ *
 * Block level: Markdown -> HTML
 * ------------------------------------------------------------------ */

type DirectiveKind = 'heading' | 'paragraph' | 'quote' | 'bullet' | 'number'

interface Directive {
  kind: DirectiveKind
  /** Heading level, list marker count is irrelevant here. */
  level: number
  /** Leading-space depth, used to nest lists. */
  indent: number
  text: string
}

const HEADING_LINE = /^(#{1,4})\s+(.*)$/
const BULLET_LINE = /^(\s*)[-*+]\s+(.*)$/
const NUMBERED_LINE = /^(\s*)\d+[.)]\s+(.*)$/
const QUOTE_LINE = /^\s*>\s?(.*)$/

function parseDirectives(markdown: string): Directive[] {
  const directives: Directive[] = []
  let paragraph: string[] = []

  const flushParagraph = () => {
    if (paragraph.length > 0) {
      directives.push({ kind: 'paragraph', level: 0, indent: 0, text: paragraph.join(' ') })
      paragraph = []
    }
  }

  for (const rawLine of markdown.split('\n')) {
    const line = rawLine.replace(/\s+$/, '')
    if (!line.trim()) {
      flushParagraph()
      continue
    }

    const heading = HEADING_LINE.exec(line)
    if (heading) {
      flushParagraph()
      directives.push({
        kind: 'heading',
        level: heading[1]!.length,
        indent: 0,
        text: heading[2]!.trim(),
      })
      continue
    }

    const quote = QUOTE_LINE.exec(line)
    if (quote) {
      flushParagraph()
      const previous = directives[directives.length - 1]
      if (previous && previous.kind === 'quote') {
        previous.text = `${previous.text} ${quote[1]!.trim()}`.trim()
      } else {
        directives.push({ kind: 'quote', level: 0, indent: 0, text: quote[1]!.trim() })
      }
      continue
    }

    const bullet = BULLET_LINE.exec(line)
    if (bullet) {
      flushParagraph()
      directives.push({
        kind: 'bullet',
        level: 0,
        indent: bullet[1]!.length,
        text: bullet[2]!.trim(),
      })
      continue
    }

    const numbered = NUMBERED_LINE.exec(line)
    if (numbered) {
      flushParagraph()
      directives.push({
        kind: 'number',
        level: 0,
        indent: numbered[1]!.length,
        text: numbered[2]!.trim(),
      })
      continue
    }

    paragraph.push(line.trim())
  }

  flushParagraph()
  return directives
}

function isListItem(directive: Directive | undefined): boolean {
  return directive?.kind === 'bullet' || directive?.kind === 'number'
}

function renderList(
  directives: Directive[],
  start: number,
  indent: number,
  ordered: boolean,
): { html: string; next: number } {
  const tag = ordered ? 'ol' : 'ul'
  let html = `<${tag}>`
  let index = start

  while (index < directives.length) {
    const directive = directives[index]
    if (!isListItem(directive)) break
    if (directive!.indent !== indent || (directive!.kind === 'number') !== ordered) break

    html += `<li>${inlineMarkdownToHtml(directive!.text)}`
    index += 1

    const child = directives[index]
    if (isListItem(child) && child!.indent > indent) {
      const nested = renderList(directives, index, child!.indent, child!.kind === 'number')
      html += nested.html
      index = nested.next
    }
    html += '</li>'
  }

  html += `</${tag}>`
  return { html, next: index }
}

function renderDirectives(directives: Directive[], start: number): { html: string; next: number } {
  let html = ''
  let index = start
  while (index < directives.length) {
    const directive = directives[index]!
    if (isListItem(directive)) {
      const list = renderList(directives, index, directive.indent, directive.kind === 'number')
      html += list.html
      index = list.next
      continue
    }
    switch (directive.kind) {
      case 'heading':
        html += `<h${directive.level}>${inlineMarkdownToHtml(directive.text)}</h${directive.level}>`
        break
      case 'quote':
        html += `<blockquote><p>${inlineMarkdownToHtml(directive.text)}</p></blockquote>`
        break
      default:
        html += `<p>${inlineMarkdownToHtml(directive.text)}</p>`
        break
    }
    index += 1
  }
  return { html, next: index }
}

/** Convert block-level Markdown in the supported subset into HTML. */
export function markdownToHtml(markdown: string): string {
  const directives = parseDirectives(markdown)
  if (directives.length === 0) return '<p></p>'
  return renderDirectives(directives, 0).html
}

/* ------------------------------------------------------------------ *
 * Block level: HTML -> Markdown
 * ------------------------------------------------------------------ */

function parseHtmlBody(html: string): HTMLElement {
  const parsed = new DOMParser().parseFromString(`<body>${html}</body>`, 'text/html')
  return parsed.body
}

function listToMarkdown(list: Element, indent: number, ordered: boolean): string {
  const lines: string[] = []
  let counter = 1
  for (const child of Array.from(list.children)) {
    if (!(child instanceof HTMLElement) || child.tagName !== 'LI') continue
    const inlineParts: string[] = []
    const nestedLists: Element[] = []
    for (const node of Array.from(child.childNodes)) {
      if (node instanceof HTMLElement && (node.tagName === 'UL' || node.tagName === 'OL')) {
        nestedLists.push(node)
      } else {
        inlineParts.push(inlineHtmlToMarkdown(node))
      }
    }
    const marker = ordered ? `${counter}. ` : '- '
    lines.push(`${'  '.repeat(indent)}${marker}${inlineParts.join('').replace(/\s+/g, ' ').trim()}`)
    counter += 1
    for (const nested of nestedLists) {
      lines.push(listToMarkdown(nested, indent + 1, nested.tagName === 'OL'))
    }
  }
  return lines.join('\n')
}

function blockElementToMarkdown(element: Element): string {
  switch (element.tagName) {
    case 'H1':
    case 'H2':
    case 'H3':
    case 'H4': {
      const level = Number(element.tagName.slice(1))
      return `${'#'.repeat(level)} ${inlineHtmlToMarkdown(element).trim()}`
    }
    case 'UL':
      return listToMarkdown(element, 0, false)
    case 'OL':
      return listToMarkdown(element, 0, true)
    case 'BLOCKQUOTE': {
      const paragraphs = Array.from(element.children)
        .map((child) => inlineHtmlToMarkdown(child).replace(/\s+/g, ' ').trim())
        .filter(Boolean)
      return paragraphs.map((text) => `> ${text}`).join('\n')
    }
    case 'PRE': {
      const code = element.querySelector('code')
      const language = code?.className.match(/language-([\w-]+)/)?.[1] ?? ''
      return `\`\`\`${language}\n${(code ?? element).textContent ?? ''}\n\`\`\``
    }
    case 'HR':
      return '---'
    default:
      return inlineHtmlToMarkdown(element).replace(/\s+/g, ' ').trim()
  }
}

/** Convert editor HTML back into the supported Markdown subset. */
export function htmlToMarkdown(html: string): string {
  const body = parseHtmlBody(html)
  return Array.from(body.children)
    .map((child) => (child instanceof HTMLElement ? blockElementToMarkdown(child) : ''))
    .filter((text) => text.length > 0)
    .join('\n\n')
}

/** Inline Markdown for a single paragraph-ish element. */
function firstBlockMarkdown(body: HTMLElement): string {
  const first = body.firstElementChild
  if (!first) return inlineHtmlToMarkdown(body).replace(/\s+/g, ' ').trim()
  if (first.tagName === 'UL' || first.tagName === 'OL') return listToMarkdown(first, 0, first.tagName === 'OL')
  if (first.tagName === 'BLOCKQUOTE') return blockElementToMarkdown(first)
  return inlineHtmlToMarkdown(first).replace(/\s+/g, ' ').trim()
}

/* ------------------------------------------------------------------ *
 * Block <-> editor document
 * ------------------------------------------------------------------ */

function listBlockToHtml(block: NoteListBlock): string {
  const tag = block.ordered ? 'ol' : 'ul'
  const renderItems = (items: NoteListItem[]): string =>
    items
      .map((item) => {
        const children = item.items && item.items.length > 0 ? renderItems(item.items) : ''
        const nestedTag = block.ordered ? 'ol' : 'ul'
        const nested = children ? `<${nestedTag}>${children}</${nestedTag}>` : ''
        return `<li>${inlineMarkdownToHtml(item.content)}${nested}</li>`
      })
      .join('')
  return `<${tag}>${renderItems(block.items)}</${tag}>`
}

/** Seed the rich-text editor with the block's current content. */
export function blockToEditorHtml(block: EditableNoteBlock): string {
  switch (block.type) {
    case 'markdown':
      return markdownToHtml(block.content)
    case 'heading':
      return `<h${block.level}>${inlineMarkdownToHtml(block.content)}</h${block.level}>`
    case 'paragraph':
      return `<p>${inlineMarkdownToHtml(block.content)}</p>`
    case 'list':
      return listBlockToHtml(block)
    case 'callout':
      return `<p>${inlineMarkdownToHtml(block.content)}</p>`
    case 'quote':
      return `<blockquote><p>${inlineMarkdownToHtml(block.content)}</p></blockquote>`
    default:
      return '<p></p>'
  }
}

function parseListItems(
  list: Element,
  baseId: string,
  path: number[] = [],
): NoteListItem[] {
  const items: NoteListItem[] = []
  let index = 0
  for (const child of Array.from(list.children)) {
    if (!(child instanceof HTMLElement) || child.tagName !== 'LI') continue
    const inlineParts: string[] = []
    const nestedLists: Element[] = []
    for (const node of Array.from(child.childNodes)) {
      if (node instanceof HTMLElement && (node.tagName === 'UL' || node.tagName === 'OL')) {
        nestedLists.push(node)
      } else {
        inlineParts.push(inlineHtmlToMarkdown(node))
      }
    }
    const item: NoteListItem = {
      id: `${baseId}-${[...path, index].join('-')}`,
      content: inlineParts.join('').replace(/\s+/g, ' ').trim(),
    }
    const nested = nestedLists[0]
    if (nested) {
      const children = parseListItems(nested, baseId, [...path, index])
      if (children.length > 0) item.items = children
    }
    items.push(item)
    index += 1
  }
  return items
}

/**
 * Apply editor HTML back onto the original block, preserving its id, ordering
 * and timestamp metadata exactly.
 */
export function applyEditorHtml(block: EditableNoteBlock, html: string): NoteBlock {
  const body = parseHtmlBody(html)
  switch (block.type) {
    case 'markdown':
      return { ...block, content: htmlToMarkdown(html) }
    case 'heading': {
      const updated: NoteHeadingBlock = { ...block, content: firstBlockMarkdown(body) }
      return updated
    }
    case 'list': {
      const list = body.querySelector('ul, ol')
      return {
        ...block,
        ordered: list ? list.tagName === 'OL' : block.ordered,
        items: list ? parseListItems(list, block.id) : block.items,
      }
    }
    case 'callout':
      return { ...block, content: firstBlockMarkdown(body) }
    case 'quote':
      return { ...block, content: firstBlockMarkdown(body).replace(/^>\s?/, '') }
    case 'paragraph':
      return { ...block, content: firstBlockMarkdown(body) }
  }
  return block
}

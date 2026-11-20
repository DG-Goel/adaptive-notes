import type { EditableNoteBlock, NoteBlock, NoteListItem } from '@/types/notes'

/** True when a block carries in-place editable text content. */
export function isEditableBlock(block: NoteBlock): block is EditableNoteBlock {
  switch (block.type) {
    case 'markdown':
    case 'heading':
    case 'paragraph':
    case 'list':
    case 'callout':
    case 'quote':
      return true
    default:
      return false
  }
}

/** Human-readable label for every block type, used in badges and error states. */
export const BLOCK_TYPE_LABELS: Record<NoteBlock['type'], string> = {
  markdown: 'Markdown',
  heading: 'Heading',
  paragraph: 'Paragraph',
  list: 'List',
  code: 'Code',
  math: 'Equation',
  table: 'Table',
  flowchart: 'Flowchart',
  diagram: 'Diagram',
  image: 'Image',
  callout: 'Callout',
  quote: 'Quote',
  unknown: 'Unsupported',
}

/** Block types rendered as read-only artifacts rather than editable text. */
export const ARTIFACT_BLOCK_TYPES = [
  'table',
  'flowchart',
  'diagram',
  'image',
  'math',
  'code',
] as const

export function isArtifactBlock(block: NoteBlock): boolean {
  return (ARTIFACT_BLOCK_TYPES as readonly string[]).includes(block.type)
}

function listItemsText(items: NoteListItem[]): string {
  return items
    .map((item) => {
      const nested = item.items && item.items.length > 0 ? ` ${listItemsText(item.items)}` : ''
      return `${item.content}${nested}`
    })
    .join(' ')
}

/**
 * Flatten a block into searchable plain text. Visual artifacts contribute
 * their caption or description so search still finds them.
 */
export function blockPlainText(block: NoteBlock): string {
  switch (block.type) {
    case 'markdown':
    case 'paragraph':
    case 'heading':
    case 'callout':
    case 'quote':
      return block.content
    case 'list':
      return listItemsText(block.items)
    case 'code':
      return `${block.title ?? ''} ${block.content}`
    case 'math':
      return `${block.description ?? ''} ${block.latex}`
    case 'table':
      return [
        block.caption ?? '',
        (block.columns ?? []).map((column) => column.header).join(' '),
        (block.rows ?? []).map((row) => row.cells.join(' ')).join(' '),
        block.markdown ?? '',
      ].join(' ')
    case 'flowchart':
      return [block.caption ?? '', block.nodes.map((node) => node.label).join(' ')].join(' ')
    case 'diagram':
      return [block.caption ?? '', block.source ?? ''].join(' ')
    case 'image':
      return `${block.alt} ${block.caption ?? ''}`
    case 'unknown':
      return block.originalType
    default:
      return ''
  }
}

/** Stable, DOM-safe id for an anchor that points at a block. */
export function blockAnchorId(blockId: string): string {
  return `note-block-${blockId}`
}

/** Stable, DOM-safe id for an anchor that points at a section. */
export function sectionAnchorId(sectionId: string): string {
  return `note-section-${sectionId}`
}

/**
 * Keys the visual pass writes onto a block so the gallery can find it again.
 * They are plumbing rather than content, so they are kept out of the metadata
 * that gets shown to the reader.
 */
const INTERNAL_META_KEYS = new Set(['artifactId', 'artifactTitle', 'artifactDescription'])

function stringifyMetaValue(value: unknown): string {
  if (typeof value === 'string') return value
  if (value === null) return 'null'
  try {
    return JSON.stringify(value) ?? String(value)
  } catch {
    // Circular payloads cannot be serialised; the key is still reported so the
    // metadata is visibly preserved rather than silently dropped.
    return '[unserialisable value]'
  }
}

/**
 * Readable view of the metadata a backend attached to a block. Unknown fields
 * are surfaced instead of discarded, which is the whole point of keeping `meta`
 * on the block model in the first place.
 */
export function metaExtras(
  meta: Record<string, unknown> | undefined,
): { key: string; value: string }[] {
  if (!meta) return []
  return Object.entries(meta)
    .filter(([key, value]) => !INTERNAL_META_KEYS.has(key) && value !== undefined)
    .map(([key, value]) => ({ key, value: stringifyMetaValue(value) }))
}

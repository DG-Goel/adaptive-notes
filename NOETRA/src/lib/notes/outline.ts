import type { NoteDocument, NoteSection } from '@/types/notes'
import { blockPlainText, isArtifactBlock } from './blocks'

/** A single row in the document outline. */
export interface OutlineEntry {
  id: string
  title: string
  level: NoteSection['level']
  startSeconds?: number
  blockCount: number
  artifactCount: number
}

export function buildOutline(document: NoteDocument | undefined): OutlineEntry[] {
  if (!document) return []
  return document.sections.map((section) => ({
    id: section.id,
    title: section.title,
    level: section.level,
    startSeconds: section.startSeconds,
    blockCount: section.blocks.length,
    artifactCount: section.blocks.filter(isArtifactBlock).length,
  }))
}

/** Outline entry plus the entries nested beneath it. */
export interface OutlineNode {
  entry: OutlineEntry
  children: OutlineNode[]
}

/**
 * Nest flat outline entries by their section level.
 * Document order is preserved exactly; only the parent/child links are added.
 */
export function buildOutlineTree(entries: OutlineEntry[]): OutlineNode[] {
  const roots: OutlineNode[] = []
  const stack: OutlineNode[] = []

  for (const entry of entries) {
    const node: OutlineNode = { entry, children: [] }
    while (stack.length > 0 && stack[stack.length - 1]!.entry.level >= entry.level) stack.pop()
    if (stack.length === 0) roots.push(node)
    else stack[stack.length - 1]!.children.push(node)
    stack.push(node)
  }

  return roots
}

/** A single search hit inside the document. */
export interface NoteSearchMatch {
  blockId: string
  sectionId: string
  sectionTitle: string
  /** Full plain text of the block, used for the snippet. */
  text: string
  /** Character offset of the first match inside `text`. */
  index: number
}

export function searchNoteDocument(
  document: NoteDocument | undefined,
  query: string,
): NoteSearchMatch[] {
  const needle = query.trim().toLowerCase()
  if (!document || !needle) return []

  const matches: NoteSearchMatch[] = []
  for (const section of document.sections) {
    for (const block of section.blocks) {
      const text = blockPlainText(block).replace(/\s+/g, ' ').trim()
      const index = text.toLowerCase().indexOf(needle)
      if (index === -1) continue
      matches.push({
        blockId: block.id,
        sectionId: section.id,
        sectionTitle: section.title,
        text,
        index,
      })
    }
  }
  return matches
}

/** Text snippet around a match, with ellipses where it was trimmed. */
export function matchSnippet(match: NoteSearchMatch, radius = 60): string {
  const start = Math.max(0, match.index - radius)
  const end = Math.min(match.text.length, match.index + radius)
  const prefix = start > 0 ? '…' : ''
  const suffix = end < match.text.length ? '…' : ''
  return `${prefix}${match.text.slice(start, end)}${suffix}`
}

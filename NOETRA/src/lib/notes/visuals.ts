import type { NoteBlock, NoteBlockType, NoteDocument, VisualArtifact, VisualArtifactKind } from '@/types/notes'

/**
 * Visual-artifact placement.
 *
 * The second pipeline pass can return artifacts separately from the document.
 * Placement is resolved from explicit metadata only — `blockId`, or a
 * `sectionId` plus a numeric `sequence`. Anything without usable placement
 * metadata is surfaced in a clearly labelled "unplaced" area instead of being
 * inserted on a guess.
 */

const NOTE_BLOCK_TYPES: readonly NoteBlockType[] = [
  'markdown',
  'heading',
  'paragraph',
  'list',
  'code',
  'math',
  'table',
  'flowchart',
  'diagram',
  'image',
  'callout',
  'quote',
  'unknown',
]

function isNoteBlockType(value: unknown): value is NoteBlockType {
  return typeof value === 'string' && (NOTE_BLOCK_TYPES as readonly string[]).includes(value)
}

/** Map a block type onto the gallery's artifact category. */
export function artifactKindForBlock(block: NoteBlock): VisualArtifactKind | null {
  switch (block.type) {
    case 'table':
      return 'table'
    case 'flowchart':
      return 'flowchart'
    case 'diagram':
      return 'diagram'
    case 'math':
      return 'formula'
    case 'image':
      return 'image'
    default:
      return null
  }
}

function blockTitle(block: NoteBlock): string {
  switch (block.type) {
    case 'table':
      return block.caption ?? 'Table'
    case 'flowchart':
      return block.caption ?? 'Flowchart'
    case 'diagram':
      return block.caption ?? 'Diagram'
    case 'math':
      return block.description ?? 'Equation'
    case 'image':
      return block.caption ?? block.alt
    default:
      return 'Artifact'
  }
}

/** Build a minimal artifact descriptor for an inline artifact block. */
export function deriveArtifactFromBlock(block: NoteBlock): VisualArtifact | null {
  const kind = artifactKindForBlock(block)
  if (!kind) return null
  const meta = block.meta ?? {}
  const title = typeof meta.artifactTitle === 'string' ? meta.artifactTitle : blockTitle(block)
  const description = typeof meta.artifactDescription === 'string' ? meta.artifactDescription : ''
  return {
    id: typeof meta.artifactId === 'string' ? meta.artifactId : `artifact-${block.id}`,
    kind,
    title,
    description,
    timestamp: block.startSeconds,
    status: 'preview',
    blockId: block.id,
    sourceBlockId: block.sourceBlockId,
  }
}

/** Every inline artifact block in the document, in document order. */
export function collectDocumentArtifacts(document: NoteDocument | undefined): VisualArtifact[] {
  if (!document) return []
  const artifacts: VisualArtifact[] = []
  for (const section of document.sections) {
    for (const block of section.blocks) {
      const artifact = deriveArtifactFromBlock(block)
      if (artifact) artifacts.push(artifact)
    }
  }
  return artifacts
}

/**
 * The gallery's artifact list.
 *
 * Inline artifact blocks are the placement source of truth; metadata recorded
 * by the visual pass enriches them so the gallery and the inline notes always
 * reference the exact same underlying artifacts. Unplaced artifacts are
 * appended and clearly marked by the caller.
 */
export function galleryArtifacts(document: NoteDocument | undefined): VisualArtifact[] {
  if (!document) return []
  const placed = new Map(
    (document.visualArtifacts ?? [])
      .filter((artifact) => artifact.blockId !== undefined)
      .map((artifact) => [artifact.blockId as string, artifact]),
  )

  const derived = collectDocumentArtifacts(document).map((artifact) => {
    const recorded = artifact.blockId ? placed.get(artifact.blockId) : undefined
    if (!recorded) return artifact
    return {
      ...artifact,
      id: recorded.id,
      title: recorded.title,
      description: recorded.description || artifact.description,
      status: recorded.status,
    }
  })

  return [...derived, ...(document.unplacedArtifacts ?? [])]
}

export function findBlockById(document: NoteDocument | undefined, blockId: string): NoteBlock | undefined {
  if (!document) return undefined
  for (const section of document.sections) {
    const block = section.blocks.find((candidate) => candidate.id === blockId)
    if (block) return block
  }
  return undefined
}

function artifactToBlock(artifact: VisualArtifact): NoteBlock | null {
  const raw = (artifact.meta ?? {}).block
  if (!raw || typeof raw !== 'object') return null
  const candidate = raw as { id?: unknown; type?: unknown }
  if (typeof candidate.id !== 'string' || !isNoteBlockType(candidate.type)) return null
  return raw as NoteBlock
}

export interface VisualMergeResult {
  document: NoteDocument
  /** Artifacts without usable placement metadata. */
  unplaced: VisualArtifact[]
}

/**
 * Merge a separate artifact list into a document deterministically.
 *
 * - An artifact whose `blockId` matches an existing block is recorded as
 *   placed and its metadata is attached to that block.
 * - An artifact with a known `sectionId` and a numeric `sequence`, plus a
 *   block payload, is inserted at that explicit position.
 * - Everything else is returned as unplaced.
 */
export function mergeVisualArtifacts(
  document: NoteDocument,
  artifacts: VisualArtifact[],
): VisualMergeResult {
  // Shallow copies: the caller's document (often a cached query value) is never
  // mutated, while `meta` objects are replaced rather than edited in place.
  const sections = document.sections.map((section) => ({
    ...section,
    blocks: section.blocks.map((block) => ({ ...block })),
  }))
  const placed: VisualArtifact[] = []
  const unplaced: VisualArtifact[] = []

  for (const artifact of artifacts) {
    let matched = false
    if (artifact.blockId) {
      for (const section of sections) {
        const index = section.blocks.findIndex((block) => block.id === artifact.blockId)
        if (index === -1) continue
        const block = section.blocks[index]!
        section.blocks[index] = {
          ...block,
          meta: {
            ...block.meta,
            artifactId: artifact.id,
            artifactTitle: artifact.title,
            artifactDescription: artifact.description,
          },
        }
        placed.push({ ...artifact, sourceBlockId: block.sourceBlockId ?? artifact.sourceBlockId })
        matched = true
        break
      }
    }
    if (matched) continue

    const section = artifact.sectionId
      ? sections.find((candidate) => candidate.id === artifact.sectionId)
      : undefined
    const block = artifactToBlock(artifact)

    if (section && typeof artifact.sequence === 'number' && block) {
      const position = Math.max(0, Math.min(section.blocks.length, Math.floor(artifact.sequence)))
      section.blocks.splice(position, 0, block)
      placed.push({ ...artifact, blockId: block.id })
      continue
    }

    unplaced.push(artifact)
  }

  return {
    document: { ...document, sections, visualArtifacts: placed, unplacedArtifacts: unplaced },
    unplaced,
  }
}

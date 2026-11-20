/**
 * Serialise a structured note document back to Markdown.
 *
 * Used for the "copy" action and for Markdown export. Visual artifacts are
 * never dropped: each one is rendered as a Markdown representation (table,
 * fenced code, LaTeX, or a labelled description with its node/edge structure)
 * so exported notes keep their meaning.
 */

import type {
  NoteBlock,
  NoteDocument,
  NoteListItem,
  NoteSection,
  NoteTableBlock,
} from '@/types/notes'

function listItemsToMarkdown(items: NoteListItem[], ordered: boolean, depth = 0): string {
  return items
    .map((item, index) => {
      const marker = ordered ? `${index + 1}.` : '-'
      const line = `${'  '.repeat(depth)}${marker} ${item.content}`
      const children = item.items && item.items.length > 0 ? listItemsToMarkdown(item.items, ordered, depth + 1) : ''
      return children ? `${line}\n${children}` : line
    })
    .join('\n')
}

/** GFM table source for a table block, generated from columns/rows if needed. */
export function tableBlockToMarkdown(block: NoteTableBlock): string {
  if (block.format === 'markdown' && block.markdown) return block.markdown.trim()

  const columns = block.columns ?? []
  const rows = block.rows ?? []
  if (columns.length === 0) return ''

  const header = `| ${columns.map((column) => column.header).join(' | ')} |`
  const divider = `| ${columns
    .map((column) => {
      if (column.align === 'center') return ':---:'
      if (column.align === 'right') return '---:'
      return '---'
    })
    .join(' | ')} |`
  const body = rows.map((row) => {
    const cells = columns.map((_, index) => row.cells[index] ?? '')
    return `| ${cells.join(' | ')} |`
  })

  return [header, divider, ...body].join('\n')
}

/** CSV export for a table block, preferring its structured columns/rows. */
export function tableBlockToCsv(block: NoteTableBlock): string {
  const columns = block.columns ?? []
  const rows = block.rows ?? []
  const escapeCell = (value: string) => `"${value.replace(/"/g, '""')}"`

  if (columns.length > 0) {
    return [
      columns.map((column) => escapeCell(column.header)).join(','),
      ...rows.map((row) => columns.map((_, index) => escapeCell(row.cells[index] ?? '')).join(',')),
    ].join('\n')
  }

  if (block.markdown) {
    const lines = block.markdown
      .trim()
      .split('\n')
      .filter((line) => !/^\s*\|?[\s:|-]+\|?\s*$/.test(line))
    return lines
      .map((line) =>
        line
          .replace(/^\s*\|/, '')
          .replace(/\|\s*$/, '')
          .split('|')
          .map((cell) => escapeCell(cell.trim()))
          .join(','),
      )
      .join('\n')
  }

  return ''
}

/** Markdown representation of a single block, including visual artifacts. */
export function blockToMarkdown(block: NoteBlock): string {
  switch (block.type) {
    case 'markdown':
      return block.content.trim()
    case 'paragraph':
      return block.content.trim()
    case 'heading':
      return `${'#'.repeat(block.level)} ${block.content.trim()}`
    case 'list':
      return listItemsToMarkdown(block.items, block.ordered)
    case 'quote':
      return `> ${block.content.trim()}${block.attribution ? `\n>\n> — ${block.attribution}` : ''}`
    case 'callout': {
      const title = block.title ? `**${block.title}** ` : ''
      return `> ${title}${block.content.trim()}`
    }
    case 'code':
      return `${block.title ? `**${block.title}**\n\n` : ''}\`\`\`${block.language ?? ''}\n${block.content}\n\`\`\``
    case 'math':
      return block.displayMode === 'block'
        ? `$$\n${block.latex}\n$$`
        : `$${block.latex}$`
    case 'table': {
      const table = tableBlockToMarkdown(block)
      const caption = block.caption ? `**${block.caption}**\n\n` : ''
      return `${caption}${table}`
    }
    case 'flowchart': {
      const steps = block.nodes.map((node) => node.label).join(' → ')
      const edges = block.edges
        .map((edge) => {
          const source = block.nodes.find((node) => node.id === edge.source)?.label ?? edge.source
          const target = block.nodes.find((node) => node.id === edge.target)?.label ?? edge.target
          return `${source} → ${target}${edge.label ? ` (${edge.label})` : ''}`
        })
        .join('; ')
      return [
        `**${block.caption ?? 'Flowchart'}** _(interactive flowchart)_`,
        '',
        `Steps: ${steps}`,
        edges ? `Edges: ${edges}` : '',
      ]
        .filter(Boolean)
        .join('\n')
    }
    case 'diagram': {
      const header = `**${block.caption ?? 'Diagram'}** _(diagram · ${block.format})_`
      if (block.format === 'flow' && block.nodes && block.nodes.length > 0) {
        return `${header}\n\nSteps: ${block.nodes.map((node) => node.label).join(' → ')}`
      }
      if (block.format === 'mermaid' && block.source) {
        return `${header}\n\n\`\`\`mermaid\n${block.source.trim()}\n\`\`\``
      }
      if (block.format === 'image' && block.src) {
        return `${header}\n\n![${block.caption ?? 'Diagram'}](${block.src})`
      }
      return header
    }
    case 'image':
      return `![${block.alt}](${block.src})${block.caption ? `\n\n_${block.caption}_` : ''}`
    case 'unknown':
      return `> _Unsupported artifact from the backend: \`${block.originalType}\`. The original payload was preserved._`
    default:
      return ''
  }
}

export function sectionToMarkdown(section: NoteSection): string {
  const body = section.blocks.map(blockToMarkdown).filter(Boolean).join('\n\n')
  const timestamp = section.startSeconds !== undefined ? ` [${section.startSeconds}s]` : ''
  return `${'#'.repeat(section.level + 1)} ${section.title}${timestamp}${body ? `\n\n${body}` : ''}`
}

/** Markdown projection of the whole document, used for copy and export. */
export function noteDocumentToMarkdown(document: NoteDocument): string {
  const header = [`# ${document.title}`]
  if (document.subtitle) header.push(`_${document.subtitle}_`)
  if (document.isDemonstration) {
    header.push(
      '> Demonstration notes. This document is deterministic sample content shipped with the demo build — it was not generated from the sample video.',
    )
  }

  const sections = document.sections.map(sectionToMarkdown)
  const unplaced = document.unplacedArtifacts ?? []
  if (unplaced.length > 0) {
    sections.push(
      [
        '## Unplaced visual artifacts',
        '',
        'These artifacts arrived without placement metadata, so they are listed here instead of being inserted on a guess:',
        '',
        ...unplaced.map((artifact) => `- **${artifact.title}** (${artifact.kind}) — ${artifact.description}`),
      ].join('\n'),
    )
  }

  return `${header.join('\n\n')}\n\n${sections.join('\n\n')}`.replace(/\n{3,}/g, '\n\n').trim()
}

/** Markdown for a single section, used by the "copy section" action. */
export function sectionClipboardText(section: NoteSection): string {
  return section.blocks.map(blockToMarkdown).filter(Boolean).join('\n\n')
}

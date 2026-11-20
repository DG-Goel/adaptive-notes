/**
 * GFM table parsing.
 *
 * Kept separate from the table renderer so both the renderer and the export
 * helpers normalise a table in exactly the same way: GFM source is parsed into
 * the same shape the structured `columns`/`rows` payload already has.
 */

export type CellAlign = 'left' | 'center' | 'right'

export interface NormalisedTable {
  headers: string[]
  aligns: CellAlign[]
  rows: string[][]
  rowIds: string[]
}

const DIVIDER_CELL = /^:?-{1,}:?$/

function splitRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())
}

function alignmentOf(cell: string): CellAlign {
  const left = cell.startsWith(':')
  const right = cell.endsWith(':')
  if (left && right) return 'center'
  if (right) return 'right'
  return 'left'
}

/** Parse a GFM table into the structured shape, or null when it is not one. */
export function parseGfmTable(markdown: string): NormalisedTable | null {
  const lines = markdown
    .trim()
    .split('\n')
    .map((line) => line.replace(/\s+$/, ''))
    .filter((line) => line.trim().length > 0)

  if (lines.length < 2) return null
  const divider = splitRow(lines[1]!)
  if (!divider.every((cell) => DIVIDER_CELL.test(cell))) return null

  const headers = splitRow(lines[0]!)
  const aligns = divider.map(alignmentOf)
  const rows = lines.slice(2).map(splitRow)

  return {
    headers,
    aligns,
    rows,
    rowIds: rows.map((_, index) => `row-${index}`),
  }
}

/* AI notes, summaries, and visual-artifact domain types. */

export type SummaryDetail = 'concise' | 'balanced' | 'detailed'

export interface LectureSummary {
  videoId: string
  executive: string
  takeaways: string[]
  concepts: { term: string; definition: string }[]
  recap: string
  /** Alternate-length recaps for the view selectors. */
  variants: Record<SummaryDetail, string>
}

export type VisualArtifactKind = 'table' | 'flowchart' | 'diagram' | 'formula' | 'image'

export interface VisualArtifact {
  id: string
  kind: VisualArtifactKind
  title: string
  description: string
  /** Related lecture timestamp in seconds, when applicable. */
  timestamp?: number
  /** `preview` renders a real artifact; `reserved` marks a later phase. */
  status: 'preview' | 'reserved'
  /**
   * Id of the structured block that renders this artifact inline. When present
   * the gallery and the document share the exact same artifact.
   */
  blockId?: string
  /** Section the artifact belongs to, per the visual-enhancement pass. */
  sectionId?: string
  /** Explicit sequence position inside its section. */
  sequence?: number
  /** Block this artifact was derived from, when it replaces text. */
  sourceBlockId?: string
  /** Unknown backend metadata, preserved verbatim. */
  meta?: Record<string, unknown>
}

/* ------------------------------------------------------------------ *
 * Structured note document
 * ------------------------------------------------------------------ */

export type NoteBlockType =
  | 'markdown'
  | 'heading'
  | 'paragraph'
  | 'list'
  | 'code'
  | 'math'
  | 'table'
  | 'flowchart'
  | 'diagram'
  | 'image'
  | 'callout'
  | 'quote'
  | 'unknown'

export interface NoteBlockBase {
  id: string
  type: NoteBlockType
  /** Explicit document order inside the owning section. */
  order?: number
  /** Video timestamp this block was derived from. */
  startSeconds?: number
  endSeconds?: number
  /** Block this artifact replaced or enhanced, per the visual pass. */
  sourceBlockId?: string
  /** Unknown backend fields, preserved so nothing is silently dropped. */
  meta?: Record<string, unknown>
}

export interface NoteMarkdownBlock extends NoteBlockBase {
  type: 'markdown'
  /** Markdown source, rendered with react-markdown + remark-gfm. */
  content: string
}

export interface NoteHeadingBlock extends NoteBlockBase {
  type: 'heading'
  level: 1 | 2 | 3 | 4
  content: string
}

export interface NoteParagraphBlock extends NoteBlockBase {
  type: 'paragraph'
  content: string
}

export interface NoteListItem {
  id: string
  content: string
  /** Nested child items, for multi-level lists. */
  items?: NoteListItem[]
}

export interface NoteListBlock extends NoteBlockBase {
  type: 'list'
  ordered: boolean
  items: NoteListItem[]
}

export interface NoteCodeBlock extends NoteBlockBase {
  type: 'code'
  language?: string
  title?: string
  content: string
}

export interface NoteMathBlock extends NoteBlockBase {
  type: 'math'
  /** LaTeX source, without delimiters. */
  latex: string
  /** `inline` renders in the text flow, `block` renders centred. */
  displayMode: 'inline' | 'block'
  description?: string
}

export interface NoteTableColumn {
  id: string
  header: string
  align?: 'left' | 'center' | 'right'
}

export interface NoteTableRow {
  id: string
  cells: string[]
}

export interface NoteTableBlock extends NoteBlockBase {
  type: 'table'
  /** `markdown` keeps the original GFM source; `structured` uses columns/rows. */
  format: 'markdown' | 'structured'
  markdown?: string
  columns?: NoteTableColumn[]
  rows?: NoteTableRow[]
  caption?: string
}

export type NoteFlowchartNodeKind = 'start' | 'process' | 'decision' | 'end'

export interface NoteFlowchartNode {
  id: string
  label: string
  kind?: NoteFlowchartNodeKind
}

export interface NoteFlowchartEdge {
  id: string
  source: string
  target: string
  label?: string
}

export type NoteFlowLayoutDirection = 'TB' | 'LR'

export interface NoteFlowchartBlock extends NoteBlockBase {
  type: 'flowchart'
  nodes: NoteFlowchartNode[]
  edges: NoteFlowchartEdge[]
  direction: NoteFlowLayoutDirection
  caption?: string
}

export type NoteDiagramFormat = 'flow' | 'mermaid' | 'image' | 'unsupported'

export interface NoteDiagramBlock extends NoteBlockBase {
  type: 'diagram'
  /** Which renderer can display this diagram. */
  format: NoteDiagramFormat
  caption?: string
  /** Node/edge payload when `format === 'flow'`. */
  nodes?: NoteFlowchartNode[]
  edges?: NoteFlowchartEdge[]
  /** Mermaid source when `format === 'mermaid'`. */
  source?: string
  /** Image URL when `format === 'image'`. */
  src?: string
  /** Original artifact payload, preserved for the unsupported state. */
  payload?: unknown
}

export interface NoteImageBlock extends NoteBlockBase {
  type: 'image'
  src: string
  alt: string
  caption?: string
}

export type NoteCalloutTone = 'info' | 'tip' | 'warning' | 'important'

export interface NoteCalloutBlock extends NoteBlockBase {
  type: 'callout'
  tone: NoteCalloutTone
  title?: string
  content: string
}

export interface NoteQuoteBlock extends NoteBlockBase {
  type: 'quote'
  content: string
  attribution?: string
}

/**
 * Fallback for a backend block type this client does not render yet. The
 * original type and payload are kept so nothing is lost or invented.
 */
export interface NoteUnknownBlock extends NoteBlockBase {
  type: 'unknown'
  originalType: string
}

export type NoteBlock =
  | NoteMarkdownBlock
  | NoteHeadingBlock
  | NoteParagraphBlock
  | NoteListBlock
  | NoteCodeBlock
  | NoteMathBlock
  | NoteTableBlock
  | NoteFlowchartBlock
  | NoteDiagramBlock
  | NoteImageBlock
  | NoteCalloutBlock
  | NoteQuoteBlock
  | NoteUnknownBlock

/** Blocks whose text content can be edited in place. */
export type EditableNoteBlock =
  | NoteMarkdownBlock
  | NoteHeadingBlock
  | NoteParagraphBlock
  | NoteListBlock
  | NoteCalloutBlock
  | NoteQuoteBlock

export interface NoteSection {
  id: string
  title: string
  /** Outline depth, used for the hierarchical table of contents. */
  level: 1 | 2 | 3
  startSeconds?: number
  endSeconds?: number
  blocks: NoteBlock[]
}

export type NoteDocumentStatus = 'demo' | 'generated' | 'stale'

export interface NoteDocument {
  id: string
  videoId: string
  title: string
  subtitle?: string
  version: number
  status: NoteDocumentStatus
  /** ISO date string of the last update. */
  updatedAt: string
  /** True when the document is deterministic demonstration content. */
  isDemonstration: boolean
  sections: NoteSection[]
  /**
   * Artifacts placed inline in the document. Kept on the document so the
   * gallery and the inline notes reference the exact same artifact data.
   */
  visualArtifacts?: VisualArtifact[]
  /**
   * Artifacts returned by the visual pass without usable placement metadata.
   * They are shown in a clearly labelled area instead of being inserted on a
   * guess.
   */
  unplacedArtifacts?: VisualArtifact[]
  /** Unknown backend metadata, preserved verbatim. */
  meta?: Record<string, unknown>
}

/* ------------------------------------------------------------------ *
 * Notes generation & visual enhancement
 * ------------------------------------------------------------------ */

export type NotesDetailLevel = 'concise' | 'balanced' | 'detailed'

export type NotesEnhancement =
  | 'examples'
  | 'equations'
  | 'tables'
  | 'flowcharts'
  | 'diagrams'
  | 'timestamps'

export interface NotesGenerationOptions {
  videoId: string
  detail: NotesDetailLevel
  enhancements: NotesEnhancement[]
}

/**
 * Processing stages the backend may report. Progress is only ever shown when
 * the API supplies it — the client never invents a percentage.
 */
export type NotesProcessingStage =
  | 'queued'
  | 'extracting'
  | 'generating'
  | 'identifying-visuals'
  | 'rendering-visuals'
  | 'completed'
  | 'failed'

export interface NotesProcessingStatus {
  videoId: string
  /** Backend job identifier, when one was returned. */
  jobId?: string
  stage: NotesProcessingStage
  /** 0–1, only when the backend reports it. */
  progress?: number
  message?: string
  updatedAt: string
}

export interface NoteDocumentVersion {
  version: number
  createdAt: string
  label?: string
  isCurrent: boolean
}

/* ------------------------------------------------------------------ *
 * Editing, saving and export
 * ------------------------------------------------------------------ */

export interface SaveNoteDocumentRequest {
  documentId: string
  videoId: string
  /** Version the edit was based on, used for conflict detection. */
  version: number
  title: string
  sections: NoteSection[]
}

export interface SaveNoteDocumentResult {
  document: NoteDocument
  /** True when the server rejected the save because it holds a newer version. */
  conflict: boolean
}

export type NotesExportFormat = 'markdown' | 'html' | 'pdf' | 'docx'

export interface NotesExportCapability {
  format: NotesExportFormat
  label: string
  available: boolean
  /** Why the format is unavailable, when it is. */
  reason?: string
}

export interface NotesExportRequest {
  videoId: string
  format: NotesExportFormat
  /** Serialised document payload produced on the client. */
  payload?: string
}

/** Result of a server-side export. The client never fabricates this. */
export interface NotesExportResult {
  format: NotesExportFormat
  filename?: string
  /** Inline payload when the backend returns the file body directly. */
  content?: string
  downloadUrl?: string
}

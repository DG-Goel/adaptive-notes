/* Knowledge map and concept graph type definitions */

export type NodeType = 'main' | 'topic' | 'subtopic' | 'formula' | 'example' | 'application'

export type RelationshipType =
  | 'contains'
  | 'depends_on'
  | 'explains'
  | 'related_to'
  | 'applied_in'
  | 'prerequisite'

export interface KnowledgeNode {
  id: string
  label: string
  type: NodeType
  description?: string
  videoId?: string
  timestampSeconds?: number
  noteSectionId?: string
  importance?: number // 1-5 scale
  metadata?: Record<string, unknown>
  [key: string]: unknown // Index signature for React Flow compatibility
}

export interface KnowledgeEdge {
  id: string
  source: string
  target: string
  relationship?: RelationshipType
  label?: string
  strength?: number // 0-1 scale
  [key: string]: unknown // Index signature for React Flow compatibility
}

export interface KnowledgeGraph {
  videoId: string
  videoTitle?: string
  nodes: KnowledgeNode[]
  edges: KnowledgeEdge[]
  createdAt?: string
  isDemo?: boolean
}

export interface ConceptDetail {
  node: KnowledgeNode
  relatedConcepts: KnowledgeNode[]
  prerequisites: KnowledgeNode[]
  applications: KnowledgeNode[]
  relatedQuestions?: string[] // quiz question IDs
}

// React Flow compatible types
export interface FlowNode {
  id: string
  type: string
  data: Record<string, unknown> & KnowledgeNode & { selected?: boolean }
  position: { x: number; y: number }
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  type?: string
  label?: string
  data?: Record<string, unknown> & { edge?: KnowledgeEdge }
  animated?: boolean
}

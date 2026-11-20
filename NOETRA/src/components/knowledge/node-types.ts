import { KnowledgeNode } from './KnowledgeNode'

/**
 * React Flow node types registry.
 * Separated from component file to support Fast Refresh optimization.
 */
export const knowledgeNodeTypes = {
  knowledge: KnowledgeNode,
} as const

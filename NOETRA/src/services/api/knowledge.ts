import { apiClient } from './client'
import { delay } from './mock-support'
import { endpoints, USE_MOCK_API } from '@/config/endpoints'
import { mockKnowledgeGraph } from '@/mocks/knowledge'
import type { KnowledgeGraph, ConceptDetail } from '@/types/knowledge'

/**
 * Backend capability flags for knowledge map features.
 */
export const knowledgeCapabilities = {
  supportsGraphGeneration: false,
  supportsConceptDetails: false,
  supportsRelatedConcepts: false,
} as const

/**
 * Fetch knowledge graph for a video.
 *
 * Mock mode returns a deterministic Transformer concept graph.
 * Real mode calls the configured backend endpoint.
 */
export async function fetchKnowledgeGraph(
  videoId: string,
  signal?: AbortSignal,
): Promise<KnowledgeGraph> {
  if (USE_MOCK_API) {
    await delay(700)
    return { ...mockKnowledgeGraph, videoId }
  }

  return apiClient.get<KnowledgeGraph>(endpoints.knowledgeMap(videoId), { signal })
}

/**
 * Fetch detailed information about a concept node.
 *
 * Mock mode builds related concepts from the graph structure.
 * Real mode fetches from backend if supported.
 */
export async function fetchConceptDetail(
  conceptId: string,
  signal?: AbortSignal,
): Promise<ConceptDetail | null> {
  if (USE_MOCK_API) {
    await delay(300)

    const node = mockKnowledgeGraph.nodes.find((n) => n.id === conceptId)
    if (!node) return null

    // Find related nodes via edges
    const relatedIds = mockKnowledgeGraph.edges
      .filter((e) => e.source === conceptId || e.target === conceptId)
      .map((e) => (e.source === conceptId ? e.target : e.source))

    const relatedConcepts = mockKnowledgeGraph.nodes.filter((n) => relatedIds.includes(n.id))

    // Find prerequisites (nodes this depends on)
    const prerequisiteIds = mockKnowledgeGraph.edges
      .filter((e) => e.target === conceptId && e.relationship === 'depends_on')
      .map((e) => e.source)

    const prerequisites = mockKnowledgeGraph.nodes.filter((n) => prerequisiteIds.includes(n.id))

    // Find applications
    const applicationIds = mockKnowledgeGraph.edges
      .filter((e) => e.source === conceptId && e.relationship === 'applied_in')
      .map((e) => e.target)

    const applications = mockKnowledgeGraph.nodes.filter((n) => applicationIds.includes(n.id))

    return {
      node,
      relatedConcepts,
      prerequisites,
      applications,
    }
  }

  if (!knowledgeCapabilities.supportsConceptDetails) {
    return null
  }

  return apiClient.get<ConceptDetail>(endpoints.conceptDetail(conceptId), { signal })
}

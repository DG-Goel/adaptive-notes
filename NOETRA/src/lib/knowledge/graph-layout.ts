import type { KnowledgeGraph, FlowNode, FlowEdge, KnowledgeNode, KnowledgeEdge } from '@/types/knowledge'

/**
 * Convert knowledge graph to React Flow format with deterministic layout.
 *
 * Uses a simple hierarchical layout algorithm to position nodes. The layout is
 * deterministic so the same graph always produces the same positions.
 *
 * For a more sophisticated layout, ELK or Dagre could be used, but this keeps
 * the bundle size down and provides acceptable results for typical concept graphs.
 */

/**
 * Assign hierarchical levels to nodes based on edge relationships.
 */
function assignLevels(nodes: KnowledgeNode[], edges: KnowledgeEdge[]): Map<string, number> {
  const levels = new Map<string, number>()
  const adjacency = new Map<string, string[]>()

  // Build adjacency list
  for (const edge of edges) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, [])
    adjacency.get(edge.source)!.push(edge.target)
  }

  // Find root nodes (nodes with no incoming edges or marked as 'main')
  const inDegree = new Map<string, number>()
  for (const node of nodes) {
    inDegree.set(node.id, 0)
  }
  for (const edge of edges) {
    inDegree.set(edge.target, (inDegree.get(edge.target) ?? 0) + 1)
  }

  const roots = nodes.filter((n) => n.type === 'main' || inDegree.get(n.id) === 0)
  if (roots.length === 0 && nodes.length > 0) {
    // Fallback: use first node as root
    roots.push(nodes[0]!)
  }

  // BFS to assign levels
  const visited = new Set<string>()
  const queue: Array<{ id: string; level: number }> = roots.map((n) => ({ id: n.id, level: 0 }))

  while (queue.length > 0) {
    const current = queue.shift()!
    if (visited.has(current.id)) continue

    visited.add(current.id)
    levels.set(current.id, current.level)

    const children = adjacency.get(current.id) ?? []
    for (const child of children) {
      if (!visited.has(child)) {
        queue.push({ id: child, level: current.level + 1 })
      }
    }
  }

  // Assign remaining nodes to a default level
  for (const node of nodes) {
    if (!levels.has(node.id)) {
      levels.set(node.id, 999) // Place unconnected nodes at the bottom
    }
  }

  return levels
}

/**
 * Layout nodes in a hierarchical tree structure.
 */
export function layoutKnowledgeGraph(graph: KnowledgeGraph): {
  nodes: FlowNode[]
  edges: FlowEdge[]
} {
  const { nodes: graphNodes, edges: graphEdges } = graph

  if (graphNodes.length === 0) {
    return { nodes: [], edges: [] }
  }

  const levels = assignLevels(graphNodes, graphEdges)

  // Group nodes by level
  const nodesByLevel = new Map<number, KnowledgeNode[]>()
  for (const node of graphNodes) {
    const level = levels.get(node.id) ?? 0
    if (!nodesByLevel.has(level)) nodesByLevel.set(level, [])
    nodesByLevel.get(level)!.push(node)
  }

  // Sort levels
  const sortedLevels = Array.from(nodesByLevel.keys()).sort((a, b) => a - b)

  // Layout constants
  const HORIZONTAL_SPACING = 250
  const VERTICAL_SPACING = 120
  const START_Y = 50

  // Position nodes
  const flowNodes: FlowNode[] = []

  for (const level of sortedLevels) {
    const nodesAtLevel = nodesByLevel.get(level)!
    const levelWidth = (nodesAtLevel.length - 1) * HORIZONTAL_SPACING
    const startX = -levelWidth / 2

    nodesAtLevel.forEach((node, index) => {
      const x = startX + index * HORIZONTAL_SPACING
      const y = START_Y + level * VERTICAL_SPACING

      flowNodes.push({
        id: node.id,
        type: 'knowledge',
        data: node,
        position: { x, y },
      })
    })
  }

  // Convert edges
  const flowEdges: FlowEdge[] = graphEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    type: 'smoothstep',
    data: edge,
    animated: edge.relationship === 'depends_on',
  }))

  return { nodes: flowNodes, edges: flowEdges }
}

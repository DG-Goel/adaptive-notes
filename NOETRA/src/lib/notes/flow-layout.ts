import type { NoteFlowLayoutDirection, NoteFlowchartEdge, NoteFlowchartNode } from '@/types/notes'

/**
 * Deterministic layered layout for flowchart artifacts.
 *
 * No layout engine is required: nodes are grouped into depth layers by
 * relaxing the edge list a bounded number of times, then spaced on a fixed
 * grid. The same input always produces the same coordinates, so React Flow's
 * canvas never jitters between renders.
 */

export const FLOW_NODE_WIDTH = 184
export const FLOW_NODE_HEIGHT = 54
export const FLOW_GAP_X = 64
export const FLOW_GAP_Y = 40

export interface FlowPoint {
  x: number
  y: number
}

export interface FlowLayout {
  positions: Record<string, FlowPoint>
  /** Bounding size of the laid-out graph, in pixels. */
  width: number
  height: number
  /** Depth layer assigned to each node, useful for ordering. */
  layers: Record<string, number>
}

function computeLayers(
  nodes: NoteFlowchartNode[],
  edges: NoteFlowchartEdge[],
): Record<string, number> {
  const layers: Record<string, number> = {}
  for (const node of nodes) layers[node.id] = 0

  // Bounded relaxation: safe against cycles and independent of edge order.
  for (let pass = 0; pass < nodes.length; pass += 1) {
    let changed = false
    for (const edge of edges) {
      if (!(edge.source in layers) || !(edge.target in layers)) continue
      const candidate = layers[edge.source]! + 1
      if (candidate > layers[edge.target]!) {
        layers[edge.target] = candidate
        changed = true
      }
    }
    if (!changed) break
  }

  return layers
}

export function layoutFlowchart(
  nodes: NoteFlowchartNode[],
  edges: NoteFlowchartEdge[],
  direction: NoteFlowLayoutDirection,
): FlowLayout {
  if (nodes.length === 0) {
    return { positions: {}, width: 0, height: 0, layers: {} }
  }

  const layers = computeLayers(nodes, edges)
  const grouped = new Map<number, string[]>()
  for (const node of nodes) {
    const layer = layers[node.id] ?? 0
    const bucket = grouped.get(layer)
    if (bucket) bucket.push(node.id)
    else grouped.set(layer, [node.id])
  }

  const orderedLayers = Array.from(grouped.keys()).sort((a, b) => a - b)
  const positions: Record<string, FlowPoint> = {}
  let maxLane = 0

  for (const layer of orderedLayers) {
    const ids = grouped.get(layer)!
    maxLane = Math.max(maxLane, ids.length)
    ids.forEach((id, index) => {
      positions[id] =
        direction === 'LR'
          ? { x: layer * (FLOW_NODE_WIDTH + FLOW_GAP_X), y: index * (FLOW_NODE_HEIGHT + FLOW_GAP_Y) }
          : { x: index * (FLOW_NODE_WIDTH + FLOW_GAP_X), y: layer * (FLOW_NODE_HEIGHT + FLOW_GAP_Y) }
    })
  }

  const laneCount = Math.max(1, maxLane)
  const depthCount = Math.max(1, orderedLayers.length)
  const width =
    direction === 'LR'
      ? depthCount * FLOW_NODE_WIDTH + (depthCount - 1) * FLOW_GAP_X
      : laneCount * FLOW_NODE_WIDTH + (laneCount - 1) * FLOW_GAP_X
  const height =
    direction === 'LR'
      ? laneCount * FLOW_NODE_HEIGHT + (laneCount - 1) * FLOW_GAP_Y
      : depthCount * FLOW_NODE_HEIGHT + (depthCount - 1) * FLOW_GAP_Y

  return { positions, width, height, layers }
}

import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { knowledgeNodeTypes } from './node-types'
import { layoutKnowledgeGraph } from '@/lib/knowledge/graph-layout'
import type { KnowledgeGraph as KnowledgeGraphData } from '@/types/knowledge'

export interface KnowledgeGraphProps {
  graph: KnowledgeGraphData
  selectedNodeId?: string
  onNodeSelect?: (nodeId: string | null) => void
  className?: string
}

/**
 * Interactive knowledge graph visualization.
 *
 * Uses React Flow for rendering and interaction. Provides pan, zoom, node
 * selection, and minimap. Layout is deterministic using the hierarchical
 * layout algorithm.
 */
export function KnowledgeGraph({
  graph,
  selectedNodeId,
  onNodeSelect,
  className,
}: KnowledgeGraphProps) {
  const { fitView } = useReactFlow()

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => layoutKnowledgeGraph(graph),
    [graph],
  )

  // Mark selected node
  const nodes = useMemo(() => {
    return initialNodes.map((node) => ({
      ...node,
      data: { ...node.data, selected: node.id === selectedNodeId },
    }))
  }, [initialNodes, selectedNodeId])

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeSelect?.(node.id)
    },
    [onNodeSelect],
  )

  const handlePaneClick = useCallback(() => {
    onNodeSelect?.(null)
  }, [onNodeSelect])

  // Fit view on mount
  const onInit = useCallback(() => {
    window.setTimeout(() => {
      fitView({ padding: 0.2, duration: 200 })
    }, 50)
  }, [fitView])

  return (
    <div className={className}>
      <ReactFlow
        nodes={nodes}
        edges={initialEdges}
        nodeTypes={knowledgeNodeTypes}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        onInit={onInit}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
        defaultEdgeOptions={{
          type: 'smoothstep',
          style: { stroke: '#D65A16', strokeWidth: 2 },
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="#E5E0D8"
        />
        <Controls
          showInteractive={false}
          className="!shadow-soft !rounded-lg !border !border-border"
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.data.type === 'main') return '#D65A16'
            if (node.data.type === 'formula') return '#3B82F6'
            if (node.data.type === 'example') return '#F59E0B'
            if (node.data.type === 'application') return '#10B981'
            return '#F7F4EF'
          }}
          maskColor="rgba(247, 244, 239, 0.7)"
          className="!shadow-soft !rounded-lg !border !border-border"
        />
      </ReactFlow>
    </div>
  )
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Maximize2, Minimize2, Workflow } from 'lucide-react'
import { metaExtras } from '@/lib/notes/blocks'
import { layoutFlowchart } from '@/lib/notes/flow-layout'
import { cn } from '@/lib/utils'
import type {
  NoteFlowLayoutDirection,
  NoteFlowchartEdge,
  NoteFlowchartNode,
  NoteFlowchartNodeKind,
} from '@/types/notes'

/**
 * Interactive flowchart artifact.
 *
 * This reuses the React Flow architecture already present in the project. The
 * layout comes from the project's deterministic layered helper, so the same
 * artifact always produces the same coordinates — React Flow is never asked to
 * run a layout, and panning/zooming is all it has to do.
 */

interface FlowNodeData extends Record<string, unknown> {
  label: string
  kind?: NoteFlowchartNodeKind
  direction: NoteFlowLayoutDirection
}

type FlowNodeType = Node<FlowNodeData, 'noteFlow'>

const NODE_STYLES: Record<NoteFlowchartNodeKind, string> = {
  start: 'border-accent/50 bg-accent/[0.09]',
  process: 'border-border bg-card',
  decision: 'border-accent/35 bg-background',
  end: 'border-accent/60 bg-accent/[0.13]',
}

const HANDLE_CLASSES = '!h-1.5 !w-1.5 !border-0 !bg-accent/70'

function NoteFlowNode({ data }: NodeProps<FlowNodeType>) {
  const vertical = data.direction === 'TB'
  return (
    <div
      className={cn(
        'flex h-[54px] w-[184px] items-center justify-center rounded-lg border px-3 text-center text-[12px] font-medium leading-snug text-foreground shadow-soft',
        NODE_STYLES[data.kind ?? 'process'],
      )}
    >
      <Handle
        type="target"
        position={vertical ? Position.Top : Position.Left}
        className={HANDLE_CLASSES}
      />
      <span className="line-clamp-2">{data.label}</span>
      <Handle
        type="source"
        position={vertical ? Position.Bottom : Position.Right}
        className={HANDLE_CLASSES}
      />
    </div>
  )
}

/** Stable identity: recreating this each render would remount every node. */
const NODE_TYPES = { noteFlow: NoteFlowNode } as unknown as NodeTypes

export interface FlowchartBlockProps {
  nodes: NoteFlowchartNode[]
  edges: NoteFlowchartEdge[]
  direction: NoteFlowLayoutDirection
  caption?: string
  meta?: Record<string, unknown>
  /** Renders inside a smaller frame, used by the visuals gallery. */
  compact?: boolean
  className?: string
}

export function FlowchartBlock({
  nodes,
  edges,
  direction,
  caption,
  meta,
  compact = false,
  className,
}: FlowchartBlockProps) {
  const layout = useMemo(() => layoutFlowchart(nodes, edges, direction), [nodes, edges, direction])
  const extras = useMemo(() => metaExtras(meta), [meta])
  const frameRef = useRef<HTMLElement | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const flowNodes = useMemo<FlowNodeType[]>(
    () =>
      nodes.map((node) => ({
        id: node.id,
        type: 'noteFlow',
        position: layout.positions[node.id] ?? { x: 0, y: 0 },
        data: { label: node.label, kind: node.kind, direction },
        draggable: false,
        selectable: false,
      })),
    [nodes, layout.positions, direction],
  )

  const flowEdges = useMemo<Edge[]>(
    () =>
      edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        label: edge.label,
        labelStyle: { fill: 'hsl(var(--muted-foreground))', fontSize: 10 },
        labelBgStyle: { fill: 'hsl(var(--card))' },
        labelBgPadding: [4, 2] as [number, number],
        style: { stroke: 'hsl(var(--border))', strokeWidth: 1.4 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 16,
          height: 16,
          color: 'hsl(var(--muted-foreground))',
        },
      })),
    [edges],
  )

  useEffect(() => {
    const handleChange = () => setIsFullscreen(document.fullscreenElement === frameRef.current)
    document.addEventListener('fullscreenchange', handleChange)
    return () => document.removeEventListener('fullscreenchange', handleChange)
  }, [])

  const toggleFullscreen = useCallback(() => {
    const frame = frameRef.current
    if (!frame) return
    if (document.fullscreenElement === frame) void document.exitFullscreen()
    else void frame.requestFullscreen().catch(() => undefined)
  }, [])

  const chartHeight = compact
    ? 220
    : Math.min(460, Math.max(230, Math.round(layout.height) + 56))

  return (
    <figure
      ref={frameRef}
      className={cn(
        'note-flow my-4 overflow-hidden rounded-xl border border-border bg-card shadow-soft',
        isFullscreen && 'flex h-screen w-screen flex-col rounded-none',
        className,
      )}
    >
      <figcaption className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-2">
        <span className="flex min-w-0 items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Workflow className="h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />
          <span className="truncate">{caption ?? 'Flowchart'}</span>
        </span>
        <div className="flex shrink-0 items-center gap-2">
          <span className="hidden text-[11px] text-muted-foreground sm:inline">
            {nodes.length} nodes · {edges.length} links
          </span>
          <button
            type="button"
            onClick={toggleFullscreen}
            aria-label={isFullscreen ? 'Exit fullscreen diagram' : 'View diagram fullscreen'}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {isFullscreen ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
            {isFullscreen ? 'Exit' : 'Fullscreen'}
          </button>
        </div>
      </figcaption>

      {nodes.length === 0 ? (
        <div className="px-4 py-6 text-xs text-muted-foreground">
          This flowchart artifact arrived without any nodes.
        </div>
      ) : (
        <div
          className="relative bg-muted/20"
          style={{ height: isFullscreen ? undefined : chartHeight, flex: isFullscreen ? 1 : undefined }}
        >
          <ReactFlow
            // Remounting on fullscreen is the cheapest way to re-run `fitView`
            // against the new frame size without a layout pass.
            key={isFullscreen ? 'fullscreen' : 'inline'}
            nodes={flowNodes}
            edges={flowEdges}
            nodeTypes={NODE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
            minZoom={0.3}
            maxZoom={1.8}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={18}
              size={1}
              color="hsl(var(--border))"
            />
            <Controls showInteractive={false} className="!shadow-soft" />
          </ReactFlow>
        </div>
      )}

      {extras.length > 0 && (
        <figcaption className="border-t border-border px-4 py-2">
          <dl className="flex flex-wrap gap-x-4 gap-y-1">
            {extras.map((entry) => (
              <div key={entry.key} className="flex items-baseline gap-1.5">
                <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {entry.key}
                </dt>
                <dd className="text-[11px] text-foreground/75">{entry.value}</dd>
              </div>
            ))}
          </dl>
        </figcaption>
      )}
    </figure>
  )
}

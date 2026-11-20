import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ReactFlowProvider } from '@xyflow/react'
import { ArrowLeft, Map, TriangleAlert, RefreshCw } from 'lucide-react'
import { PageTransition } from '@/components/common/PageTransition'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { KnowledgeGraph } from '@/components/knowledge/KnowledgeGraph'
import { KnowledgeMapControls } from '@/components/knowledge/KnowledgeMapControls'
import { ConceptDetailPanel } from '@/components/knowledge/ConceptDetailPanel'
import { useLecture } from '@/hooks/use-lecture-queries'
import { fetchKnowledgeGraph, fetchConceptDetail } from '@/services/api/knowledge'

/**
 * Knowledge Map page.
 *
 * Interactive concept graph visualization showing relationships between ideas
 * in a lecture. Supports pan, zoom, search, node selection, and detailed
 * concept exploration.
 */
function KnowledgeMapContent() {
  const { videoId } = useParams()
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [fullscreen, setFullscreen] = useState(false)

  const { data: lecture, isPending: lecturePending, isError: lectureError } = useLecture(videoId)

  const {
    data: graph,
    isPending: graphPending,
    isError: graphError,
    error: graphErrorObj,
    refetch: refetchGraph,
  } = useQuery({
    queryKey: ['knowledge-graph', videoId],
    queryFn: ({ signal }) => fetchKnowledgeGraph(videoId ?? '', signal),
    enabled: Boolean(videoId),
    staleTime: 5 * 60 * 1000,
  })

  const {
    data: conceptDetail,
    isPending: detailPending,
  } = useQuery({
    queryKey: ['concept-detail', selectedNodeId],
    queryFn: ({ signal }) => fetchConceptDetail(selectedNodeId ?? '', signal),
    enabled: Boolean(selectedNodeId),
    staleTime: 5 * 60 * 1000,
  })

  const handleNodeSelect = (nodeId: string | null) => {
    setSelectedNodeId(nodeId)
  }

  const handleNavigateToNode = (nodeId: string) => {
    setSelectedNodeId(nodeId)
    // Optionally center the node in view
  }

  if (!videoId) {
    return (
      <EmptyState
        icon={<TriangleAlert className="h-5 w-5" />}
        title="No lecture selected"
        description="Choose a lecture from your library to view its knowledge map."
        action={
          <Link to="/library">
            <PrimaryButton>
              <ArrowLeft className="h-4 w-4" /> Back to library
            </PrimaryButton>
          </Link>
        }
      />
    )
  }

  if (lecturePending || graphPending) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton variant="text" className="max-w-md" />
        <LoadingSkeleton variant="card" className="h-[600px]" />
      </div>
    )
  }

  if (lectureError || !lecture) {
    return (
      <EmptyState
        icon={<TriangleAlert className="h-5 w-5" />}
        title="Lecture unavailable"
        description="This lecture could not be loaded."
        action={
          <Link to="/library">
            <SecondaryButton>
              <ArrowLeft className="h-4 w-4" /> Back to library
            </SecondaryButton>
          </Link>
        }
      />
    )
  }

  if (graphError || !graph) {
    return (
      <EmptyState
        icon={<TriangleAlert className="h-5 w-5" />}
        title="Knowledge map unavailable"
        description={
          graphErrorObj instanceof Error
            ? graphErrorObj.message
            : 'The knowledge map could not be loaded for this lecture.'
        }
        action={
          <div className="flex items-center gap-2">
            <SecondaryButton onClick={() => void refetchGraph()}>
              <RefreshCw className="h-3.5 w-3.5" /> Try again
            </SecondaryButton>
            <Link to={`/learn/${videoId}`}>
              <PrimaryButton variant="outline">
                <ArrowLeft className="h-4 w-4" /> Back to lecture
              </PrimaryButton>
            </Link>
          </div>
        }
      />
    )
  }

  // Fullscreen mode
  if (fullscreen) {
    return (
      <div className="-mx-4 -my-6 flex h-screen flex-col sm:-mx-6 lg:-mx-8 lg:-my-8">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-border bg-background px-4 sm:px-6 lg:px-8">
          <div className="min-w-0 flex-1">
            <h1 className="truncate font-serif text-lg font-medium text-foreground">
              {lecture.title}
            </h1>
            <p className="truncate text-xs text-muted-foreground">
              Knowledge Map
              {graph.isDemo && ' · Demo Graph'}
            </p>
          </div>
          <KnowledgeMapControls
            nodes={graph.nodes}
            onNodeSelect={handleNodeSelect}
            fullscreen={fullscreen}
            onToggleFullscreen={() => setFullscreen(false)}
          />
        </header>

        {/* Graph + Detail Panel */}
        <div className="flex flex-1 overflow-hidden">
          <KnowledgeGraph
            graph={graph}
            selectedNodeId={selectedNodeId ?? undefined}
            onNodeSelect={handleNodeSelect}
            className="flex-1"
          />
          {selectedNodeId && conceptDetail && !detailPending && (
            <ConceptDetailPanel
              detail={conceptDetail}
              onClose={() => setSelectedNodeId(null)}
              onNavigateToNode={handleNavigateToNode}
              className="w-80"
            />
          )}
        </div>
      </div>
    )
  }

  // Normal mode
  return (
    <div className="space-y-6">
      {/* Header */}
      <header>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-accent">
              Knowledge Map
            </p>
            <h1 className="mt-1 font-serif text-2xl font-medium tracking-tight text-foreground">
              {lecture.title}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Explore how concepts in this lecture connect and build upon each other.
            </p>
            {graph.isDemo && (
              <p className="mt-1 text-xs text-amber-700">
                This is a demonstration graph for the Transformer architecture lecture.
              </p>
            )}
          </div>
          <Link to={`/learn/${videoId}`}>
            <SecondaryButton>
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Back to lecture</span>
            </SecondaryButton>
          </Link>
        </div>
      </header>

      {/* Controls */}
      <KnowledgeMapControls
        nodes={graph.nodes}
        onNodeSelect={handleNodeSelect}
        fullscreen={fullscreen}
        onToggleFullscreen={() => setFullscreen(true)}
      />

      {/* Graph Container */}
      <div className="flex items-start gap-6">
        <div className="flex-1">
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <KnowledgeGraph
              graph={graph}
              selectedNodeId={selectedNodeId ?? undefined}
              onNodeSelect={handleNodeSelect}
              className="h-[700px]"
            />
          </div>

          {/* Graph stats */}
          <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <span>
              <strong className="text-foreground">{graph.nodes.length}</strong> concepts
            </span>
            <span>
              <strong className="text-foreground">{graph.edges.length}</strong> connections
            </span>
            <span className="ml-auto text-xs">
              Click a node to view details · Drag to pan · Scroll to zoom
            </span>
          </div>
        </div>

        {/* Detail Panel (desktop) */}
        {selectedNodeId && conceptDetail && !detailPending && (
          <div className="hidden w-80 shrink-0 lg:block">
            <div className="sticky top-6 overflow-hidden rounded-2xl shadow-soft">
              <ConceptDetailPanel
                detail={conceptDetail}
                onClose={() => setSelectedNodeId(null)}
                onNavigateToNode={handleNavigateToNode}
              />
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="mb-3 flex items-center gap-2">
          <Map className="h-4 w-4 text-accent" />
          <h2 className="font-serif text-base font-medium text-foreground">Node Types</h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-accent bg-accent/10" />
            <span className="text-sm text-foreground">Main Concept</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-border bg-card" />
            <span className="text-sm text-foreground">Topic / Subtopic</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-blue-200 bg-blue-50" />
            <span className="text-sm text-foreground">Formula</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-amber-200 bg-amber-50" />
            <span className="text-sm text-foreground">Example</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full border-2 border-green-200 bg-green-50" />
            <span className="text-sm text-foreground">Application</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-8 rounded-full bg-accent" />
            <span className="text-sm text-foreground">Relationship</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function KnowledgeMapPage() {
  return (
    <PageTransition>
      <ReactFlowProvider>
        <KnowledgeMapContent />
      </ReactFlowProvider>
    </PageTransition>
  )
}

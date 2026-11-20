import { useState } from 'react'
import { Search, Maximize, Minimize, ZoomIn, ZoomOut, Locate } from 'lucide-react'
import { useReactFlow } from '@xyflow/react'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { cn } from '@/lib/utils'
import type { KnowledgeNode } from '@/types/knowledge'

export interface KnowledgeMapControlsProps {
  nodes: KnowledgeNode[]
  onNodeSelect: (nodeId: string) => void
  fullscreen: boolean
  onToggleFullscreen: () => void
  className?: string
}

/**
 * Knowledge map search and view controls.
 *
 * Provides concept search, zoom controls, fit view, and fullscreen toggle.
 */
export function KnowledgeMapControls({
  nodes,
  onNodeSelect,
  fullscreen,
  onToggleFullscreen,
  className,
}: KnowledgeMapControlsProps) {
  const [query, setQuery] = useState('')
  const [showResults, setShowResults] = useState(false)
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  const filtered = query.trim()
    ? nodes.filter((node) => node.label.toLowerCase().includes(query.toLowerCase()))
    : []

  const handleSelectNode = (nodeId: string) => {
    onNodeSelect(nodeId)
    setQuery('')
    setShowResults(false)
  }

  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      {/* Search */}
      <div className="relative flex-1 sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowResults(e.target.value.trim().length > 0)
          }}
          onFocus={() => setShowResults(query.trim().length > 0)}
          onBlur={() => window.setTimeout(() => setShowResults(false), 200)}
          placeholder="Search concepts..."
          className="w-full rounded-lg border border-input bg-background py-2 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-accent/50 focus-visible:ring-2 focus-visible:ring-ring/30"
        />

        {/* Search results dropdown */}
        {showResults && filtered.length > 0 && (
          <div className="absolute left-0 top-full z-50 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
            {filtered.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => handleSelectNode(node.id)}
                className="flex w-full items-center gap-2 border-b border-border px-3 py-2 text-left transition-colors last:border-0 hover:bg-muted"
              >
                <span className="inline-block rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                  {node.type}
                </span>
                <span className="flex-1 text-sm text-foreground">{node.label}</span>
              </button>
            ))}
          </div>
        )}

        {showResults && filtered.length === 0 && query.trim() && (
          <div className="absolute left-0 top-full z-50 mt-2 w-full rounded-lg border border-border bg-popover p-3 text-center text-sm text-muted-foreground shadow-lg">
            No concepts found
          </div>
        )}
      </div>

      {/* View controls */}
      <div className="flex items-center gap-1">
        <SecondaryButton
          size="sm"
          onClick={() => zoomIn()}
          aria-label="Zoom in"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </SecondaryButton>
        <SecondaryButton
          size="sm"
          onClick={() => zoomOut()}
          aria-label="Zoom out"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </SecondaryButton>
        <SecondaryButton
          size="sm"
          onClick={() => fitView({ padding: 0.2, duration: 200 })}
          aria-label="Fit view"
        >
          <Locate className="h-3.5 w-3.5" />
        </SecondaryButton>
        <SecondaryButton
          size="sm"
          onClick={onToggleFullscreen}
          aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {fullscreen ? <Minimize className="h-3.5 w-3.5" /> : <Maximize className="h-3.5 w-3.5" />}
        </SecondaryButton>
      </div>
    </div>
  )
}

import { useNavigate } from 'react-router-dom'
import { X, Video, BookOpen, Lightbulb, Link as LinkIcon, ArrowRight } from 'lucide-react'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { TimestampChip } from '@/components/video/TimestampText'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ConceptDetail, KnowledgeNode } from '@/types/knowledge'

export interface ConceptDetailPanelProps {
  detail: ConceptDetail
  onClose: () => void
  onNavigateToNode: (nodeId: string) => void
  className?: string
}

/**
 * Concept detail sidebar.
 *
 * Shows full information about a selected concept: description, related
 * concepts, prerequisites, applications, and navigation links to video
 * timestamps and notes.
 */
export function ConceptDetailPanel({
  detail,
  onClose,
  onNavigateToNode,
  className,
}: ConceptDetailPanelProps) {
  const navigate = useNavigate()
  const { node, relatedConcepts, prerequisites, applications } = detail

  const handleNodeClick = (clickedNode: KnowledgeNode) => {
    onNavigateToNode(clickedNode.id)
  }

  return (
    <div className={cn('flex h-full flex-col border-l border-border bg-card', className)}>
      {/* Header */}
      <div className="flex items-start gap-3 border-b border-border p-4">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <Badge variant="outline" className="text-[10px]">
              {node.type}
            </Badge>
            {node.importance !== undefined && (
              <div className="flex gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      'h-1.5 w-1.5 rounded-full',
                      i < (node.importance ?? 0) ? 'bg-accent' : 'bg-muted',
                    )}
                  />
                ))}
              </div>
            )}
          </div>
          <h2 className="font-serif text-lg font-medium text-foreground">{node.label}</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close detail panel"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6">
          {/* Description */}
          {node.description && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-foreground">About</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{node.description}</p>
            </div>
          )}

          {/* Source links */}
          {(node.timestampSeconds !== undefined || node.noteSectionId) && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-foreground">Learn More</h3>
              <div className="flex flex-wrap gap-2">
                {node.timestampSeconds !== undefined && node.videoId && (
                  <TimestampChip
                    seconds={node.timestampSeconds}
                    label="Watch in lecture"
                  />
                )}
                {node.noteSectionId && node.videoId && (
                  <SecondaryButton
                    size="sm"
                    onClick={() => navigate(`/notes/${node.videoId}`)}
                  >
                    <BookOpen className="h-3 w-3" />
                    Related notes
                  </SecondaryButton>
                )}
              </div>
            </div>
          )}

          {/* Prerequisites */}
          {prerequisites.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground">
                <Lightbulb className="h-3.5 w-3.5 text-blue-600" />
                Prerequisites
              </h3>
              <div className="space-y-2">
                {prerequisites.map((prereq) => (
                  <button
                    key={prereq.id}
                    type="button"
                    onClick={() => handleNodeClick(prereq)}
                    className="flex w-full items-center justify-between rounded-lg border border-border bg-background p-2 text-left transition-colors hover:border-accent/40 hover:bg-muted"
                  >
                    <span className="text-sm text-foreground">{prereq.label}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Related concepts */}
          {relatedConcepts.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground">
                <LinkIcon className="h-3.5 w-3.5 text-accent" />
                Related Concepts
              </h3>
              <div className="space-y-2">
                {relatedConcepts.slice(0, 5).map((related) => (
                  <button
                    key={related.id}
                    type="button"
                    onClick={() => handleNodeClick(related)}
                    className="flex w-full items-center justify-between rounded-lg border border-border bg-background p-2 text-left transition-colors hover:border-accent/40 hover:bg-muted"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[9px]">
                        {related.type}
                      </Badge>
                      <span className="text-sm text-foreground">{related.label}</span>
                    </div>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Applications */}
          {applications.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground">
                <Video className="h-3.5 w-3.5 text-green-600" />
                Applications
              </h3>
              <div className="space-y-2">
                {applications.map((app) => (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => handleNodeClick(app)}
                    className="flex w-full items-center justify-between rounded-lg border border-border bg-background p-2 text-left transition-colors hover:border-accent/40 hover:bg-muted"
                  >
                    <span className="text-sm text-foreground">{app.label}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

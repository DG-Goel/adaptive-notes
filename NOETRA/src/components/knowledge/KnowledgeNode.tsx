import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Lightbulb, BookOpen, Calculator, Zap, Rocket, Box } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { KnowledgeNode as KnowledgeNodeData, NodeType } from '@/types/knowledge'

/**
 * Custom React Flow node for knowledge graph concepts.
 *
 * Uses NOETRA's design system: warm whites, thin borders, burnt-orange
 * highlights, and elegant typography. Different node types have distinct
 * visual treatments.
 */

const NODE_TYPE_CONFIG: Record<
  NodeType,
  { icon: typeof BookOpen; bgColor: string; borderColor: string; textColor: string }
> = {
  main: {
    icon: Rocket,
    bgColor: 'bg-accent/10',
    borderColor: 'border-accent',
    textColor: 'text-accent',
  },
  topic: {
    icon: BookOpen,
    bgColor: 'bg-card',
    borderColor: 'border-border',
    textColor: 'text-foreground',
  },
  subtopic: {
    icon: Box,
    bgColor: 'bg-card',
    borderColor: 'border-border',
    textColor: 'text-foreground',
  },
  formula: {
    icon: Calculator,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
  },
  example: {
    icon: Lightbulb,
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-700',
  },
  application: {
    icon: Zap,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
  },
}

export interface KnowledgeNodeProps extends NodeProps {
  data: KnowledgeNodeData & { selected?: boolean }
}

export const KnowledgeNode = memo(function KnowledgeNode({
  data,
  selected,
}: KnowledgeNodeProps) {
  const config = NODE_TYPE_CONFIG[data.type]
  const Icon = config.icon
  const isMainConcept = data.type === 'main'

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-2 rounded-xl border-2 p-3 shadow-soft transition-all',
        config.bgColor,
        config.borderColor,
        selected && 'ring-2 ring-accent/30',
        isMainConcept ? 'min-w-[200px]' : 'min-w-[160px]',
      )}
    >
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-0 !bg-accent/70"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-0 !bg-accent/70"
      />

      {/* Content */}
      <div className="flex items-start gap-2">
        <Icon className={cn('h-4 w-4 shrink-0', config.textColor)} />
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              'text-sm font-medium leading-tight',
              isMainConcept ? 'font-serif text-base' : '',
              config.textColor,
            )}
          >
            {data.label}
          </p>
          {data.importance !== undefined && (
            <div className="mt-1 flex gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'h-1 w-1 rounded-full',
                    i < (data.importance ?? 0) ? 'bg-accent' : 'bg-muted',
                  )}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Description (on hover for non-main nodes) */}
      {data.description && !isMainConcept && (
        <div className="invisible absolute left-0 top-full z-50 mt-2 w-64 rounded-lg border border-border bg-popover p-3 text-xs leading-relaxed text-popover-foreground shadow-lg group-hover:visible">
          {data.description}
        </div>
      )}
    </div>
  )
})

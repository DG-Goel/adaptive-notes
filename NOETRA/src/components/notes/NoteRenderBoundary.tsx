import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { TriangleAlert } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface NoteRenderBoundaryProps {
  /** Human-readable name of the surface that failed, e.g. "Flowchart". */
  label: string
  className?: string
  children: ReactNode
}

interface NoteRenderBoundaryState {
  error: Error | null
}

/**
 * Keeps one broken artifact from taking down the whole notes document.
 *
 * Markdown, table, and diagram renderers run third-party pipelines over
 * backend-supplied content, so a single malformed artifact should degrade to a
 * readable message instead of a blank page. The block keeps its position and
 * the surrounding document keeps rendering.
 */
export class NoteRenderBoundary extends Component<
  NoteRenderBoundaryProps,
  NoteRenderBoundaryState
> {
  state: NoteRenderBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): NoteRenderBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Also logged so the failure is diagnosable outside the rendered output.
    console.error(`[notes] ${this.props.label} renderer failed`, error, info.componentStack)
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div
        role="alert"
        className={cn(
          'my-3 rounded-xl border border-destructive/30 bg-destructive/[0.05] px-4 py-3',
          this.props.className,
        )}
      >
        <p className="flex items-center gap-2 text-sm font-medium text-foreground">
          <TriangleAlert className="h-4 w-4 text-destructive" />
          {this.props.label} could not be rendered
        </p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          The rest of the document is unaffected. Reported error: {error.message}
        </p>
      </div>
    )
  }
}

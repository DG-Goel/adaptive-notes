import { GitBranch, Grid3x3, Image, Network, Sigma } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { VisualArtifactKind } from '@/types/notes'

/** Presentation metadata for each kind of visual artifact an API can return. */
export const ARTIFACT_KIND_META: Record<VisualArtifactKind, { icon: LucideIcon; label: string }> = {
  table: { icon: Grid3x3, label: 'Table' },
  flowchart: { icon: GitBranch, label: 'Flowchart' },
  diagram: { icon: Network, label: 'Diagram' },
  formula: { icon: Sigma, label: 'Formula' },
  image: { icon: Image, label: 'Image' },
}

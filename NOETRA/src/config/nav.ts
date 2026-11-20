import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  Sparkles,
  BrainCircuit,
  Map,
  Library,
  Settings,
} from 'lucide-react'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  badge?: string | number
}

export const primaryNav: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'My Lectures', to: '/library', icon: BookOpen },
  // The Notes Studio is a real document view from Phase 4 onward, so the entry
  // points at the one bundled demonstration lecture instead of a placeholder id.
  { label: 'Notes Studio', to: '/notes/demo-transformers', icon: FileText },
  { label: 'AI Tutor', to: '/tutor', icon: Sparkles },
  { label: 'Quizzes', to: '/quizzes', icon: BrainCircuit },
  { label: 'Knowledge Map', to: '/knowledge/sample', icon: Map },
  { label: 'Library', to: '/library', icon: Library },
]

export const secondaryNav: NavItem[] = [
  { label: 'Settings', to: '/settings', icon: Settings },
]

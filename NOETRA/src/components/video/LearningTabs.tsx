import { useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { Captions, FileText, LayoutList, LineChart, Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { NotesPanel } from '@/components/video/panels/NotesPanel'
import { VideoNotesJob } from '@/components/video/VideoNotesJob'
import { SummaryPanel } from '@/components/video/panels/SummaryPanel'
import { TranscriptPanel } from '@/components/video/TranscriptPanel'
import { VisualsPanel } from '@/components/video/panels/VisualsPanel'
import { LocalVisualsPanel } from '@/components/video/panels/LocalVisualsPanel'
import { ResourcesPanel } from '@/components/video/panels/ResourcesPanel'
import type { VideoLecture } from '@/types/video'

interface TabDefinition {
  id: string
  label: string
  icon: LucideIcon
  /** Heavy panels mount only after the tab is first opened. */
  lazy: boolean
}

export interface LearningTabsProps {
  lecture: VideoLecture
  videoId: string
  /** Sticky offset for the tab bar when it sits below another sticky header. */
  stickyTopClassName?: string
  className?: string
}

export function LearningTabs({
  lecture,
  videoId,
  stickyTopClassName = 'top-0',
  className,
}: LearningTabsProps) {
  const tabs = useMemo<TabDefinition[]>(() => {
    const base: TabDefinition[] = [
      { id: 'notes', label: 'AI Notes', icon: Sparkles, lazy: true },
      { id: 'summary', label: 'Summary', icon: LayoutList, lazy: true },
      { id: 'transcript', label: 'Transcript', icon: Captions, lazy: true },
      { id: 'visuals', label: 'Visuals', icon: LineChart, lazy: true },
    ]
    if (lecture.resources.length > 0) {
      base.push({ id: 'resources', label: 'Resources', icon: FileText, lazy: true })
    }
    return base
  }, [lecture.resources.length])

  const [activeId, setActiveId] = useState(tabs[0].id)
  const [visited, setVisited] = useState<Set<string>>(() => new Set([tabs[0].id]))

  const select = (id: string) => {
    setActiveId(id)
    setVisited((prev) => (prev.has(id) ? prev : new Set(prev).add(id)))
  }

  const renderPanel = (id: string) => {
    switch (id) {
      case 'notes':
        return <><VideoNotesJob key={videoId} lecture={lecture} />{!videoId.startsWith('local:') && <NotesPanel videoId={videoId} />}</>
      case 'summary':
        return <SummaryPanel videoId={videoId} />
      case 'transcript':
        return <TranscriptPanel videoId={videoId} />
      case 'visuals':
        return videoId.startsWith('local:')
          ? <LocalVisualsPanel video={videoId.slice('local:'.length)} />
          : <VisualsPanel videoId={videoId} />
      case 'resources':
        return <ResourcesPanel lecture={lecture} />
      default:
        return null
    }
  }

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-label="Lecture content"
        className={cn(
          'sticky z-10 -mx-1 flex gap-1 overflow-x-auto border-b border-border bg-background/85 px-1 backdrop-blur supports-[backdrop-filter]:bg-background/70',
          stickyTopClassName,
        )}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const active = tab.id === activeId
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`tab-${tab.id}`}
              aria-selected={active}
              aria-controls={`panel-${tab.id}`}
              onClick={() => select(tab.id)}
              className={cn(
                'relative flex shrink-0 items-center gap-2 px-3.5 py-3 text-sm font-medium transition-colors',
                active ? 'text-accent' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
              {active && (
                <motion.span
                  layoutId="learning-tab-indicator"
                  className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent"
                  transition={{ type: 'spring', stiffness: 420, damping: 34 }}
                />
              )}
            </button>
          )
        })}
      </div>

      <div className="pt-5">
        {tabs.map((tab) =>
          visited.has(tab.id) ? (
            <div
              key={tab.id}
              role="tabpanel"
              id={`panel-${tab.id}`}
              aria-labelledby={`tab-${tab.id}`}
              hidden={tab.id !== activeId}
            >
              {renderPanel(tab.id)}
            </div>
          ) : null,
        )}
      </div>
    </div>
  )
}

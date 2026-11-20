import { ExternalLink, FileText, Link2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SectionHeader } from '@/components/common/SectionHeader'
import type { VideoLecture } from '@/types/video'

export interface ResourcesPanelProps {
  lecture: VideoLecture
  className?: string
}

export function ResourcesPanel({ lecture, className }: ResourcesPanelProps) {
  return (
    <section className={cn('rounded-2xl border border-border bg-card p-5 shadow-soft', className)}>
      <SectionHeader
        title="Resources"
        description="Supplementary material referenced in this lecture"
      />
      <ul className="mt-4 divide-y divide-border">
        {lecture.resources.map((resource) => {
          const Icon = resource.kind === 'file' ? FileText : Link2
          const disabled = !resource.url
          return (
            <li key={resource.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Icon className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground">{resource.label}</p>
                {resource.description && (
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                    {resource.description}
                  </p>
                )}
              </div>
              {disabled ? (
                <span className="shrink-0 rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground">
                  Unavailable
                </span>
              ) : (
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                >
                  Open <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

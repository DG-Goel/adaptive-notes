import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  Clock,
  FileText,
  Flame,
  Map,
  Play,
  Plus,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { PageTransition } from '@/components/common/PageTransition'
import { PremiumCard } from '@/components/common/PremiumCard'
import { SectionHeader } from '@/components/common/SectionHeader'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { VideoImportDialog } from '@/components/video/VideoImportDialog'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/* ---------------------------------------------------------------- */
/*  Static demo data (Phase 1 foundation — wired to API later)      */
/* ---------------------------------------------------------------- */

interface Stat {
  label: string
  value: string
  delta: string
  icon: LucideIcon
}

const stats: Stat[] = [
  { label: 'Lectures processed', value: '24', delta: '+3 this week', icon: BookOpen },
  { label: 'Notes generated', value: '186', delta: '+12 this week', icon: FileText },
  { label: 'Study hours', value: '41.5', delta: '+2.4h this week', icon: Clock },
  { label: 'Quiz accuracy', value: '88%', delta: '+5% this week', icon: BrainCircuit },
]

interface Lecture {
  title: string
  course: string
  duration: string
  status: 'ready' | 'processing' | 'new'
}

const recentLectures: Lecture[] = [
  { title: 'Attention Is All You Need', course: 'Deep Learning Specialization', duration: '24 min', status: 'ready' },
  { title: 'Backpropagation & Gradients', course: 'Neural Networks', duration: '38 min', status: 'ready' },
  { title: 'Probabilistic Graphical Models', course: 'Advanced ML', duration: '52 min', status: 'processing' },
  { title: 'Linear Algebra Refresher', course: 'Foundations', duration: '17 min', status: 'new' },
]

const statusStyles: Record<Lecture['status'], { label: string; className: string }> = {
  ready: { label: 'Ready', className: 'bg-emerald-500/10 text-emerald-600' },
  processing: { label: 'Processing', className: 'bg-amber-500/10 text-amber-600' },
  new: { label: 'New', className: 'bg-accent/10 text-accent' },
}

const activity = [
  { day: 'M', minutes: 42 },
  { day: 'T', minutes: 68 },
  { day: 'W', minutes: 30 },
  { day: 'T', minutes: 84 },
  { day: 'F', minutes: 55 },
  { day: 'S', minutes: 20 },
  { day: 'S', minutes: 46 },
]

const concepts = [
  'Attention',
  'Transformers',
  'Gradient descent',
  'Embeddings',
  'Backpropagation',
  'Regularisation',
  'Convolutions',
  'Tokenisation',
]

/* ---------------------------------------------------------------- */
/*  Small local primitives                                          */
/* ---------------------------------------------------------------- */

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${value}%` }} />
    </div>
  )
}

function StatCard({ stat, index }: { stat: Stat; index: number }) {
  const { icon: Icon } = stat
  return (
    <PremiumCard
      hoverable
      className="p-5"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
          <Icon className="h-5 w-5" />
        </div>
        <TrendingUp className="h-4 w-4 text-emerald-500" />
      </div>
      <p className="mt-4 font-serif text-3xl font-medium text-foreground">{stat.value}</p>
      <p className="mt-0.5 text-sm text-muted-foreground">{stat.label}</p>
      <p className="mt-2 text-xs font-medium text-emerald-600">{stat.delta}</p>
    </PremiumCard>
  )
}

/* ---------------------------------------------------------------- */
/*  Dashboard page                                                  */
/* ---------------------------------------------------------------- */

export function DashboardPage() {
  const peak = Math.max(...activity.map((a) => a.minutes))
  const [importOpen, setImportOpen] = useState(false)

  return (
    <PageTransition>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Overview"
          title="Dashboard"
          description="Your personal learning command center — lectures, notes, quizzes, and progress, all in one refined space."
          actions={
            <PrimaryButton onClick={() => setImportOpen(true)}>
              <Plus className="h-4 w-4" /> New lecture
            </PrimaryButton>
          }
        />

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat, i) => (
            <StatCard key={stat.label} stat={stat} index={i} />
          ))}
        </div>

        {/* Continue learning + AI tutor */}
        <div className="grid gap-4 lg:grid-cols-3">
          <PremiumCard className="lg:col-span-2 overflow-hidden p-0">
            <div className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center">
              <div className="relative flex h-28 w-full shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-sidebar via-[#2a2a2a] to-sidebar sm:w-48">
                <div className="absolute inset-0 opacity-30">
                  <Play className="absolute left-1/2 top-1/2 h-10 w-10 -translate-x-1/2 -translate-y-1/2 text-white" />
                </div>
                <span className="relative inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-[11px] font-medium text-white backdrop-blur">
                  <Play className="h-3 w-3" /> Resume
                </span>
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-accent">
                  Continue learning
                </p>
                <h3 className="mt-1.5 font-serif text-xl text-foreground">
                  Neural Networks: Backpropagation
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Deep Learning Specialization · Lecture 4 of 7
                </p>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>68% complete</span>
                    <span>16 min left</span>
                  </div>
                  <ProgressBar value={68} />
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {/* The only bundled lecture, so the resume/notes actions open a
                      document that actually resolves rather than a placeholder id. */}
                  <Link to="/learn/demo-transformers">
                    <PrimaryButton size="sm">
                      <Play className="h-3.5 w-3.5" /> Resume lecture
                    </PrimaryButton>
                  </Link>
                  <Link to="/notes/demo-transformers">
                    <PrimaryButton variant="outline" size="sm">
                      <FileText className="h-3.5 w-3.5" /> Open notes
                    </PrimaryButton>
                  </Link>
                </div>
              </div>
            </div>
          </PremiumCard>

          <PremiumCard className="flex flex-col justify-between p-6">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
                  <Sparkles className="h-5 w-5" />
                </div>
                <Badge variant="accent">Beta</Badge>
              </div>
              <h3 className="mt-4 font-serif text-lg text-foreground">Ask the AI tutor</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Get grounded answers tied directly to your lectures.
              </p>
            </div>

            <div className="mt-5 space-y-2">
              <div className="rounded-xl border border-dashed border-border bg-muted/30 px-3 py-2.5 text-sm text-muted-foreground">
                Why does attention scale by √dₖ?
              </div>
              <Link to="/tutor" className="block">
                <PrimaryButton variant="outline" size="sm" className="w-full justify-between">
                  Open tutor <ArrowUpRight className="h-3.5 w-3.5" />
                </PrimaryButton>
              </Link>
            </div>
          </PremiumCard>
        </div>

        {/* Recent lectures + activity */}
        <div className="grid gap-4 lg:grid-cols-3">
          <PremiumCard className="lg:col-span-2 p-6">
            <SectionHeader
              title="Recent lectures"
              action={
                <Link
                  to="/library"
                  className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-accent"
                >
                  View all <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              }
            />
            <ul className="mt-4 divide-y divide-border">
              {recentLectures.map((lecture) => {
                const s = statusStyles[lecture.status]
                return (
                  <li key={lecture.title} className="flex items-center gap-4 py-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                      <Play className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">{lecture.title}</p>
                      <p className="truncate text-xs text-muted-foreground">{lecture.course}</p>
                    </div>
                    <span className="hidden text-xs text-muted-foreground sm:block">
                      {lecture.duration}
                    </span>
                    <span
                      className={cn(
                        'inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-[11px] font-medium',
                        s.className,
                      )}
                    >
                      {s.label}
                    </span>
                  </li>
                )
              })}
            </ul>
          </PremiumCard>

          <PremiumCard className="flex flex-col p-6">
            <SectionHeader title="This week" description="Study minutes" />
            <div className="mt-6 flex flex-1 items-end justify-between gap-2">
              {activity.map((a, i) => (
                <div key={i} className="flex flex-1 flex-col items-center gap-2">
                  <div className="flex h-32 w-full items-end">
                    <div
                      className="w-full rounded-t-md bg-accent/80 transition-all duration-500 hover:bg-accent"
                      style={{ height: `${(a.minutes / peak) * 100}%` }}
                    />
                  </div>
                  <span className="text-[11px] text-muted-foreground">{a.day}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 flex items-center justify-between rounded-xl border border-border bg-muted/30 px-3 py-2.5">
              <span className="inline-flex items-center gap-2 text-sm text-foreground">
                <Flame className="h-4 w-4 text-accent" /> 6-day streak
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> On track
              </span>
            </div>
          </PremiumCard>
        </div>

        {/* Knowledge map strip */}
        <PremiumCard className="p-6">
          <SectionHeader
            title="Knowledge map"
            description="Concepts connected across your lectures"
            action={
              <Link to="/knowledge/sample">
                <PrimaryButton variant="outline" size="sm">
                  <Map className="h-3.5 w-3.5" /> Open map
                </PrimaryButton>
              </Link>
            }
          />
          <div className="mt-5 flex flex-wrap gap-2">
            {concepts.map((concept) => (
              <span
                key={concept}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-accent/40 hover:text-foreground"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-accent/70" />
                {concept}
              </span>
            ))}
          </div>
        </PremiumCard>
      </div>

      <VideoImportDialog open={importOpen} onOpenChange={setImportOpen} />
    </PageTransition>
  )
}

import { useState } from 'react'
import { ArrowRight, BookOpen, Sparkles, Search, Star } from 'lucide-react'
import { Logo } from '@/components/common/Logo'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { PremiumCard } from '@/components/common/PremiumCard'
import { GlassCard } from '@/components/common/GlassCard'
import { SectionHeader } from '@/components/common/SectionHeader'
import { SearchField } from '@/components/common/SearchField'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { StatusIndicator } from '@/components/common/StatusIndicator'
import { PageTransition } from '@/components/common/PageTransition'
import { GlassSculpture } from '@/components/three/GlassSculpture'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { PageHeader } from '@/components/common/PageHeader'

const palette = [
  { name: 'Background', value: '#F7F4EF', text: 'text-foreground' },
  { name: 'Sidebar', value: '#252525', text: 'text-white' },
  { name: 'Primary text', value: '#252422', text: 'text-white' },
  { name: 'Brand accent', value: '#D65A16', text: 'text-white' },
  { name: 'Accent hover', value: '#B94A10', text: 'text-white' },
  { name: 'Card surfaces', value: '#FFFFFF', text: 'text-foreground' },
  { name: 'Muted background', value: '#EEE9E2', text: 'text-foreground' },
  { name: 'Borders', value: '#DED8D0', text: 'text-foreground' },
  { name: 'Secondary text', value: '#817C75', text: 'text-white' },
]

export function DesignSystemPage() {
  const [loading, setLoading] = useState(false)

  const handleLoading = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 1800)
  }

  return (
    <PageTransition>
      <div className="space-y-12">
        <PageHeader
          eyebrow="Design System"
          title="NOETRA Visual Identity"
          description="The complete design language — warm editorial materials, refined components, and the signature glass sculpture that defines the product."
        />

        {/* Brand + sculpture */}
        <section className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <PremiumCard className="flex flex-col justify-between gap-6 p-8">
            <div className="space-y-3">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-accent">Wordmark</p>
              <div className="flex items-center gap-3">
                <Logo textClassName="text-foreground" />
              </div>
              <p className="max-w-md text-sm text-muted-foreground">
                NOETRA in uppercase with subtle letter-spacing, paired with an abstract intertwined
                knot mark representing connected knowledge and structured learning.
              </p>
            </div>
            <div className="flex gap-6">
              <div>
                <p className="text-xs text-muted-foreground">Headings</p>
                <p className="font-serif text-3xl">Instrument Serif</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interface</p>
                <p className="text-3xl font-semibold">DM Sans</p>
              </div>
            </div>
          </PremiumCard>

          <PremiumCard className="overflow-hidden p-0">
            <div className="relative h-[320px] w-full bg-gradient-to-br from-sidebar via-[#2a2a2a] to-sidebar">
              <GlassSculpture variant="hero" />
            </div>
            <div className="flex items-center justify-between p-5">
              <div>
                <p className="font-serif text-lg text-foreground">Signature Glass Sculpture</p>
                <p className="text-sm text-muted-foreground">Interactive 3D · React Three Fiber</p>
              </div>
              <div className="flex items-center gap-2">
                <StatusIndicator status="online" pulse label="Rendering" />
              </div>
            </div>
          </PremiumCard>
        </section>

        {/* Color palette */}
        <section className="space-y-4">
          <SectionHeader title="Color Palette" description="Warm ivory, charcoal, and burnt orange — a refined, natural material palette." />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {palette.map((c) => (
              <div key={c.name} className="overflow-hidden rounded-xl border border-border shadow-soft">
                <div className="flex h-20 items-end p-3" style={{ backgroundColor: c.value }}>
                  <span className={`font-mono text-[10px] ${c.text}`}>{c.value}</span>
                </div>
                <div className="bg-card p-3">
                  <p className="text-xs font-medium text-foreground">{c.name}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Typography */}
        <section className="space-y-4">
          <SectionHeader title="Typography" description="Editorial serif headings paired with a clean geometric sans." />
          <PremiumCard className="space-y-6 p-8">
            <div>
              <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Display · 72px</p>
              <h1 className="font-serif text-6xl leading-none tracking-tight">Watch. Learn. Understand.</h1>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Heading · 36px</p>
              <h2 className="font-serif text-4xl leading-tight tracking-tight">Transform lectures into knowledge</h2>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Body · 16px</p>
              <p className="max-w-2xl text-base leading-relaxed text-foreground">
                NOETRA turns every educational video into beautifully structured notes, summaries,
                visual diagrams, quizzes, and an interactive AI tutor — all within a calm, focused
                learning environment.
              </p>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Caption · 14px</p>
              <p className="text-sm text-muted-foreground">Designed for deep work. Built for curious minds.</p>
            </div>
          </PremiumCard>
        </section>

        {/* Buttons */}
        <section className="space-y-4">
          <SectionHeader title="Buttons" description="Primary burnt-orange actions with subtle scale and shadow feedback." />
          <PremiumCard className="space-y-4 p-8">
            <div className="flex flex-wrap items-center gap-3">
              <PrimaryButton>Primary action</PrimaryButton>
              <SecondaryButton>Secondary</SecondaryButton>
              <PrimaryButton variant="outline">Outline</PrimaryButton>
              <PrimaryButton variant="ghost">Ghost</PrimaryButton>
              <PrimaryButton disabled>Disabled</PrimaryButton>
              <PrimaryButton loading={loading} onClick={handleLoading}>
                {loading ? 'Saving…' : 'Click to load'}
              </PrimaryButton>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <PrimaryButton size="sm">Small</PrimaryButton>
              <PrimaryButton size="default">Default</PrimaryButton>
              <PrimaryButton size="lg">Large <ArrowRight className="h-4 w-4" /></PrimaryButton>
              <PrimaryButton size="icon" aria-label="Star"><Star className="h-4 w-4" /></PrimaryButton>
            </div>
          </PremiumCard>
        </section>

        {/* Cards */}
        <section className="space-y-4">
          <SectionHeader title="Cards & Surfaces" description="Premium layered cards and frosted-glass surfaces." />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <PremiumCard hoverable className="p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <Sparkles className="h-5 w-5" />
              </div>
              <h3 className="font-serif text-xl">Premium Card</h3>
              <p className="mt-1 text-sm text-muted-foreground">Soft shadow, rounded corners, and a gentle lift on hover.</p>
            </PremiumCard>

            <GlassCard className="p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/80 text-accent">
                <BookOpen className="h-5 w-5" />
              </div>
              <h3 className="font-serif text-xl">Glass Card</h3>
              <p className="mt-1 text-sm text-muted-foreground">Frosted backdrop with a subtle inner highlight.</p>
            </GlassCard>

            <div className="relative overflow-hidden rounded-2xl p-6" style={{ backgroundColor: '#252525' }}>
              <div className="absolute inset-0 opacity-30">
                <GlassSculpture variant="mini" />
              </div>
              <div className="relative">
                <h3 className="font-serif text-xl text-white">Dark Surface</h3>
                <p className="mt-1 text-sm text-white/60">Charcoal canvas for the signature sculpture.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Form fields */}
        <section className="space-y-4">
          <SectionHeader title="Form Fields" description="Restrained inputs with warm focus states." />
          <PremiumCard className="grid gap-4 p-8 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Search field</label>
              <SearchField placeholder="Search your lectures, notes, or ask anything…" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Text input</label>
              <Input placeholder="Enter a title…" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">With value</label>
              <Input defaultValue="Introduction to Transformers" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Disabled</label>
              <Input disabled placeholder="Disabled state" />
            </div>
          </PremiumCard>
        </section>

        {/* Badges, status, avatar */}
        <section className="space-y-4">
          <SectionHeader title="Status & Indicators" description="Badges, status dots, and avatars." />
          <PremiumCard className="flex flex-wrap items-center gap-6 p-8">
            <div className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="accent">Accent</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Destructive</Badge>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <StatusIndicator status="online" pulse label="Online" />
              <StatusIndicator status="away" label="Away" />
              <StatusIndicator status="busy" label="Busy" />
              <StatusIndicator status="success" label="Success" />
              <StatusIndicator status="warning" label="Warning" />
              <StatusIndicator status="error" label="Error" />
            </div>
            <div className="flex items-center gap-3">
              <Avatar><AvatarFallback>JD</AvatarFallback></Avatar>
              <Avatar><AvatarFallback className="bg-accent text-accent-foreground">A</AvatarFallback></Avatar>
              <Avatar className="ring-2 ring-accent"><AvatarFallback>MK</AvatarFallback></Avatar>
            </div>
          </PremiumCard>
        </section>

        {/* Loading & empty states */}
        <section className="space-y-4">
          <SectionHeader title="Loading & Empty States" description="Skeletons and graceful empty states." />
          <div className="grid gap-4 md:grid-cols-2">
            <PremiumCard className="p-6">
              <p className="mb-4 text-sm font-medium text-foreground">Card skeleton</p>
              <LoadingSkeleton variant="card" />
            </PremiumCard>
            <PremiumCard className="p-6">
              <p className="mb-4 text-sm font-medium text-foreground">List skeleton</p>
              <LoadingSkeleton variant="list" />
            </PremiumCard>
          </div>
          <EmptyState
            icon={<Search className="h-5 w-5" />}
            title="No results found"
            description="Try adjusting your search or browse the full library of lectures."
          />
        </section>

        {/* Mini sculpture showcase */}
        <section className="space-y-4">
          <SectionHeader title="Sculpture Variants" description="Hero and compact mini variants." />
          <div className="grid gap-4 md:grid-cols-[1.5fr_1fr]">
            <PremiumCard className="overflow-hidden p-0">
              <div className="relative h-[280px] w-full bg-muted/40">
                <GlassSculpture variant="hero" />
              </div>
              <p className="p-4 text-sm text-muted-foreground">Hero variant — large, full presence.</p>
            </PremiumCard>
            <PremiumCard className="flex flex-col items-center justify-center gap-4 p-8">
              <GlassSculpture variant="mini" />
              <p className="text-center text-sm text-muted-foreground">Mini variant — sidebar accent.</p>
            </PremiumCard>
          </div>
        </section>
      </div>
    </PageTransition>
  )
}

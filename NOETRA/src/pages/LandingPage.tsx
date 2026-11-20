import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import {
  ArrowRight,
  BookOpen,
  BrainCircuit,
  Check,
  FileText,
  Layers,
  Map,
  Play,
  Plus,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { Logo } from '@/components/common/Logo'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { PremiumCard } from '@/components/common/PremiumCard'
import { GlassCard } from '@/components/common/GlassCard'
import { GlassSculpture } from '@/components/three/GlassSculpture'

/* Resolved once at module scope — avoids an impure call during render */
const COPYRIGHT_YEAR = new Date().getFullYear()

/* ------------------------------------------------------------------ */
/*  Scroll-reveal wrapper — respects reduced-motion preferences        */
/* ------------------------------------------------------------------ */

function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode
  delay?: number
  className?: string
}) {
  const reduceMotion = useReducedMotion()
  return (
    <motion.div
      className={className}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
      whileInView={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

const features = [
  {
    icon: BookOpen,
    title: 'Structured summaries',
    description:
      'Condense hour-long lectures into crisp, organised summaries you can read in minutes.',
  },
  {
    icon: FileText,
    title: 'Notes that write themselves',
    description:
      'Beautiful, formatted notes generated as you watch — tagged, linked, and searchable.',
  },
  {
    icon: Map,
    title: 'Visual diagrams',
    description:
      'Concept maps and diagrams that reveal exactly how every idea connects to the next.',
  },
  {
    icon: Sparkles,
    title: 'Grounded AI tutor',
    description:
      'Ask anything about your material and get answers tied directly to the source video.',
  },
  {
    icon: BrainCircuit,
    title: 'Adaptive quizzes',
    description:
      'Practice generated from your own lectures, tuned to the topics you find hardest.',
  },
  {
    icon: Layers,
    title: 'Knowledge map',
    description:
      'Watch your understanding grow across every subject in one connected, living graph.',
  },
]

const steps = [
  {
    title: 'Bring your lecture',
    description: 'Drop in any video link or upload a file — a full course or a single clip.',
  },
  {
    title: 'Watch NOETRA understand',
    description:
      'It transcribes, segments, and reasons across every moment, building structure as it goes.',
  },
  {
    title: 'Study smarter',
    description: 'Read refined notes, quiz yourself, and ask the tutor — all in one calm space.',
  },
]

const stats = [
  { value: '12k+', label: 'Lectures understood' },
  { value: '480k', label: 'Notes generated' },
  { value: '3.4×', label: 'Faster revision' },
  { value: '4.9/5', label: 'Learner rating' },
]

export function LandingPage() {
  const reduceMotion = useReducedMotion()

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-background">
      {/* Nav — preserved Phase 1 navigation design */}
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <Logo />
        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#features" className="transition-colors hover:text-foreground">Features</a>
          <a href="#" className="transition-colors hover:text-foreground">Pricing</a>
          <a href="#" className="transition-colors hover:text-foreground">About</a>
        </nav>
        <Link to="/dashboard">
          <PrimaryButton size="sm">Open Studio</PrimaryButton>
        </Link>
      </header>

      {/* Hero */}
      <main className="relative flex flex-1 flex-col items-center px-6 pt-10 text-center sm:px-10">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/4 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-accent/10 blur-[120px]" />
          <div className="absolute left-1/4 top-1/2 h-[360px] w-[360px] -translate-x-1/2 rounded-full bg-accent/[0.06] blur-[100px]" />
        </div>

        <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center gap-6">
          <motion.span
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs font-medium text-muted-foreground shadow-soft"
          >
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            AI-powered video learning
          </motion.span>

          <motion.h1
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.05, ease: [0.22, 1, 0.36, 1] }}
            className="font-serif text-5xl font-medium leading-[1.05] tracking-tight text-foreground sm:text-6xl md:text-7xl"
          >
            Watch. Learn.<br />
            <span className="italic text-accent">Understand.</span>
          </motion.h1>

          <motion.p
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-xl text-pretty text-base text-muted-foreground sm:text-lg"
          >
            NOETRA transforms educational videos into beautiful structured notes, summaries,
            diagrams, and interactive AI tutoring — so every lecture becomes lasting knowledge.
          </motion.p>

          <motion.div
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-wrap items-center justify-center gap-3 pt-2"
          >
            <Link to="/dashboard">
              <PrimaryButton size="lg">
                Get started free <ArrowRight className="h-4 w-4" />
              </PrimaryButton>
            </Link>
            <a href="#how">
              <PrimaryButton variant="outline" size="lg">
                <Play className="h-4 w-4" /> See how it works
              </PrimaryButton>
            </a>
          </motion.div>
        </div>

        {/* Hero sculpture — cinematic stage */}
        <motion.div
          initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 40, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 1.1, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-0 mt-12 h-[360px] w-full max-w-2xl sm:h-[460px]"
        >
          <div className="pointer-events-none absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/[0.07] blur-[80px] sm:h-[420px] sm:w-[420px]" />
          <GlassSculpture variant="hero" />
        </motion.div>
      </main>

      {/* Stats */}
      <section id="about" className="relative z-10 border-y border-border bg-card/60">
        <div className="mx-auto grid max-w-5xl grid-cols-2 gap-px px-6 py-10 sm:px-10 md:grid-cols-4">
          {stats.map((stat, i) => (
            <Reveal key={stat.label} delay={i * 0.06} className="px-2 text-center">
              <p className="font-serif text-3xl font-medium text-foreground sm:text-4xl">
                {stat.value}
              </p>
              <p className="mt-1 text-xs uppercase tracking-[0.14em] text-muted-foreground">
                {stat.label}
              </p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <Reveal className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-accent">
              Everything in one place
            </p>
            <h2 className="mt-3 font-serif text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
              From raw video to real understanding
            </h2>
            <p className="mt-3 text-pretty text-muted-foreground">
              Six connected tools that turn passive watching into active, lasting knowledge.
            </p>
          </Reveal>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, i) => (
              <Reveal key={feature.title} delay={(i % 3) * 0.08}>
                <PremiumCard hoverable className="h-full p-6">
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent">
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-serif text-xl text-foreground">{feature.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground">{feature.description}</p>
                </PremiumCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="relative z-10 bg-muted/50 px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <Reveal>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-accent">
                Three calm steps
              </p>
              <h2 className="mt-3 font-serif text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
                A quieter way to study
              </h2>
              <p className="mt-3 max-w-md text-pretty text-muted-foreground">
                No cluttered timelines, no disconnected tools. NOETRA keeps you in one focused flow
                from the first minute of a lecture to the last revision.
              </p>

              <ol className="mt-8 space-y-6">
                {steps.map((step, i) => (
                  <Reveal key={step.title} delay={i * 0.1}>
                    <li className="flex gap-4">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-card font-serif text-sm text-accent shadow-soft">
                        {i + 1}
                      </span>
                      <div>
                        <p className="font-medium text-foreground">{step.title}</p>
                        <p className="mt-0.5 text-sm text-muted-foreground">{step.description}</p>
                      </div>
                    </li>
                  </Reveal>
                ))}
              </ol>
            </Reveal>

            {/* Product preview mock */}
            <Reveal delay={0.1}>
              <GlassCard className="p-3 shadow-premium-lg">
                <div className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
                        <Play className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          Attention is All You Need
                        </p>
                        <p className="text-xs text-muted-foreground">Lecture · processed · 24 min</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-600">
                      <Check className="h-3 w-3" /> Ready
                    </span>
                  </div>

                  <div className="mt-5 space-y-3">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Summary</span>
                      <span className="inline-flex items-center gap-1 text-accent">
                        <Sparkles className="h-3 w-3" /> Generated
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-2.5 w-full rounded-full bg-muted" />
                      <div className="h-2.5 w-[92%] rounded-full bg-muted" />
                      <div className="h-2.5 w-[78%] rounded-full bg-muted" />
                      <div className="h-2.5 w-[64%] rounded-full bg-muted" />
                    </div>
                  </div>

                  <div className="mt-5 grid grid-cols-3 gap-3">
                    {[
                      { label: 'Notes', value: '18' },
                      { label: 'Concepts', value: '42' },
                      { label: 'Quiz', value: '12' },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="rounded-lg border border-border bg-muted/40 p-3 text-center"
                      >
                        <p className="font-serif text-xl text-foreground">{item.value}</p>
                        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                          {item.label}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-border bg-muted/30 px-3 py-2.5 text-xs text-muted-foreground">
                    <Sparkles className="h-3.5 w-3.5 text-accent" />
                    Ask the tutor anything about this lecture…
                  </div>
                </div>
              </GlassCard>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative z-10 px-6 py-20 sm:px-10 sm:py-28">
        <Reveal className="mx-auto max-w-4xl">
          <div className="relative overflow-hidden rounded-3xl border border-border bg-card px-8 py-14 text-center shadow-premium sm:px-16">
            <div className="pointer-events-none absolute left-1/2 top-0 h-[300px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/[0.08] blur-[90px]" />
            <div className="relative">
              <div className="mx-auto mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <TrendingUp className="h-5 w-5" />
              </div>
              <h2 className="font-serif text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
                Turn your next lecture into knowledge
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-pretty text-muted-foreground">
                Start free — no credit card, no setup. Bring a lecture and watch it become notes,
                diagrams, and a tutor that actually knows your course.
              </p>
              <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
                <Link to="/dashboard">
                  <PrimaryButton size="lg">
                    <Plus className="h-4 w-4" /> Open Studio
                  </PrimaryButton>
                </Link>
                <Link to="/design-system">
                  <PrimaryButton variant="outline" size="lg">
                    View design system
                  </PrimaryButton>
                </Link>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <footer className="px-6 py-6 text-center text-xs text-muted-foreground sm:px-10">
        © {COPYRIGHT_YEAR} NOETRA. Crafted for learners.
      </footer>
    </div>
  )
}

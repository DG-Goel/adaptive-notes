import { Suspense, lazy, useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { cn } from '@/lib/utils'

/* three.js lives behind this dynamic import, so it is never part of the
   initial bundle — the scene loads asynchronously only when it is shown. */
const SculptureScene = lazy(() => import('./SculptureScene'))

/* ------------------------------------------------------------------ */
/*  Static fallback shown while the 3D canvas loads or if WebGL fails  */
/* ------------------------------------------------------------------ */

function SculptureFallback({
  variant = 'hero',
  className,
}: {
  variant?: 'hero' | 'mini'
  className?: string
}) {
  const isMini = variant === 'mini'
  return (
    <div
      aria-hidden="true"
      className={cn(
        'relative flex items-center justify-center overflow-hidden rounded-full',
        isMini ? 'h-24 w-24' : 'h-full w-full',
        className,
      )}
      style={{
        background:
          'radial-gradient(circle at 30% 25%, rgba(232,116,48,0.18), transparent 55%), radial-gradient(circle at 70% 75%, rgba(214,90,22,0.12), transparent 55%), #252525',
      }}
    >
      <svg
        viewBox="0 0 200 200"
        className={cn('opacity-80', isMini ? 'h-16 w-16' : 'h-2/3 w-2/3')}
        fill="none"
      >
        <defs>
          <linearGradient id="fallback-ribbon" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#F7E7C8" />
            <stop offset="0.5" stopColor="#E8A86A" />
            <stop offset="1" stopColor="#C84A10" />
          </linearGradient>
        </defs>
        <path
          d="M100 30c40 0 60 30 60 70s-20 70-60 70-60-30-60-70 20-70 60-70Z"
          stroke="url(#fallback-ribbon)"
          strokeWidth="10"
          strokeLinecap="round"
          opacity="0.9"
        />
        <path
          d="M100 170c-40 0-60-30-60-70s20-70 60-70 60 30 60 70-20 70-60 70Z"
          stroke="#F7F4EF"
          strokeWidth="10"
          strokeLinecap="round"
          opacity="0.55"
        />
      </svg>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  One-time, browser-safe WebGL capability check                      */
/*  Resolved at module scope so no state is set synchronously from     */
/*  inside an effect (and it stays safe when there is no DOM).         */
/* ------------------------------------------------------------------ */

const webglSupported: boolean = (() => {
  if (typeof window === 'undefined' || typeof document === 'undefined') return false
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    const lose = gl?.getExtension('WEBGL_lose_context')
    if (lose) lose.loseContext()
    return !!gl
  } catch {
    return false
  }
})()

/* ------------------------------------------------------------------ */
/*  Public GlassSculpture component                                    */
/* ------------------------------------------------------------------ */

export type GlassSculptureProps = {
  variant?: 'hero' | 'mini'
  className?: string
  style?: CSSProperties
}

export function GlassSculpture({ variant = 'hero', className, style }: GlassSculptureProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [inView, setInView] = useState(true)

  // Pause rendering when offscreen (setState happens in the async observer
  // callback, not synchronously in the effect body)
  useEffect(() => {
    const el = containerRef.current
    if (!el || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver(
      ([entry]) => setInView(entry.isIntersecting),
      { threshold: 0 },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const containerClass = cn(
    'relative overflow-hidden',
    variant === 'mini' ? 'h-24 w-24' : 'h-full w-full min-h-[300px]',
    className,
  )

  if (!webglSupported) {
    return <SculptureFallback variant={variant} className={className} />
  }

  return (
    <div ref={containerRef} className={containerClass} style={style}>
      <Suspense fallback={<SculptureFallback variant={variant} className="absolute inset-0" />}>
        {inView ? (
          <SculptureScene variant={variant} inView={inView} />
        ) : (
          <SculptureFallback variant={variant} className="absolute inset-0" />
        )}
      </Suspense>
    </div>
  )
}

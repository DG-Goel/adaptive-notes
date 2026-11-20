import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  dark?: boolean
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, dark = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl backdrop-blur-xl transition-all duration-300',
        dark
          ? 'bg-sidebar/70 border border-white/10 text-sidebar-foreground'
          : 'bg-white/60 border border-white/60 text-foreground shadow-glass',
        className,
      )}
      {...props}
    />
  ),
)
GlassCard.displayName = 'GlassCard'

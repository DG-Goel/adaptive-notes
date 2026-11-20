import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface PremiumCardProps extends HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean
}

export const PremiumCard = forwardRef<HTMLDivElement, PremiumCardProps>(
  ({ className, hoverable = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-border bg-card text-card-foreground shadow-soft transition-all duration-300',
        hoverable && 'hover:-translate-y-0.5 hover:shadow-premium cursor-pointer',
        className,
      )}
      {...props}
    />
  ),
)
PremiumCard.displayName = 'PremiumCard'

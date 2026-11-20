import { cn } from '@/lib/utils'

export type Status = 'online' | 'away' | 'busy' | 'offline' | 'success' | 'warning' | 'error' | 'neutral'

const statusColors: Record<Status, string> = {
  online: 'bg-emerald-500',
  away: 'bg-amber-400',
  busy: 'bg-rose-500',
  offline: 'bg-muted-foreground',
  success: 'bg-emerald-500',
  warning: 'bg-amber-400',
  error: 'bg-rose-500',
  neutral: 'bg-muted-foreground',
}

export interface StatusIndicatorProps {
  status: Status
  label?: string
  size?: 'sm' | 'md' | 'lg'
  pulse?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2.5 w-2.5',
  lg: 'h-3.5 w-3.5',
}

export function StatusIndicator({
  status,
  label,
  size = 'md',
  pulse = false,
  className,
}: StatusIndicatorProps) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <span className="relative flex">
        {pulse && (status === 'online' || status === 'success') && (
          <span
            className={cn(
              'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
              statusColors[status],
            )}
          />
        )}
        <span
          className={cn(
            'relative inline-flex rounded-full ring-2 ring-background',
            statusColors[status],
            sizeClasses[size],
          )}
        />
      </span>
      {label && <span className="text-xs font-medium text-muted-foreground">{label}</span>}
    </span>
  )
}

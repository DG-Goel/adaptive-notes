import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'
import { Button, type ButtonProps } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost'
type Size = NonNullable<ButtonProps['size']>

export interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-accent text-accent-foreground hover:bg-accent-hover shadow-sm hover:shadow-md active:scale-[0.98]',
  secondary:
    'bg-secondary text-secondary-foreground hover:bg-secondary/80 active:scale-[0.98]',
  outline:
    'border border-border bg-transparent hover:bg-muted text-foreground active:scale-[0.98]',
  ghost: 'bg-transparent hover:bg-muted text-foreground',
}

export const PrimaryButton = forwardRef<HTMLButtonElement, PrimaryButtonProps>(
  ({ variant = 'primary', size = 'default', loading, className, children, disabled, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || loading}
        size={size}
        className={cn(variantClasses[variant], className)}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </Button>
    )
  },
)
PrimaryButton.displayName = 'PrimaryButton'

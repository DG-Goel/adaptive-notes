import { forwardRef, type InputHTMLAttributes } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export interface SearchFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string
}

export const SearchField = forwardRef<HTMLInputElement, SearchFieldProps>(
  ({ className, containerClassName, ...props }, ref) => (
    <div className={cn('relative w-full', containerClassName)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={ref}
        className={cn('pl-10 pr-4 h-11 rounded-full bg-muted/40 border-transparent focus-visible:bg-background', className)}
        {...props}
      />
    </div>
  ),
)
SearchField.displayName = 'SearchField'

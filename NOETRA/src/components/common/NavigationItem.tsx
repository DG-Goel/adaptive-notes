import { NavLink } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface NavigationItemProps {
  to: string
  label: string
  icon: LucideIcon
  collapsed?: boolean
  badge?: string | number
}

export function NavigationItem({ to, label, icon: Icon, collapsed = false, badge }: NavigationItemProps) {
  return (
    <NavLink
      to={to}
      end={to === '/dashboard'}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
          'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground',
          isActive &&
            'bg-sidebar-accent text-sidebar-foreground shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]',
          collapsed && 'justify-center px-2',
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-accent" />
          )}
          <Icon className={cn('h-[18px] w-[18px] shrink-0 transition-transform duration-200', 'group-hover:scale-110')} />
          {!collapsed && <span className="flex-1 truncate">{label}</span>}
          {!collapsed && badge !== undefined && (
            <span className="rounded-full bg-accent/90 px-1.5 py-0.5 text-[10px] font-semibold text-accent-foreground">
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

import { Link, useLocation } from 'react-router-dom'
import { Bell, ChevronRight, Menu, Search } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { SearchField } from '@/components/common/SearchField'
import { cn } from '@/lib/utils'

interface TopNavProps {
  onMobileMenuClick: () => void
}

const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  library: 'Library',
  learn: 'Video Workspace',
  notes: 'Notes Studio',
  tutor: 'AI Tutor',
  quiz: 'Quiz Studio',
  knowledge: 'Knowledge Map',
  settings: 'Settings',
  'design-system': 'Design System',
}

export function TopNav({ onMobileMenuClick }: TopNavProps) {
  const location = useLocation()
  const segments = location.pathname.split('/').filter(Boolean)

  const breadcrumbs = segments.map((seg, i) => {
    const path = '/' + segments.slice(0, i + 1).join('/')
    const label = routeLabels[seg] ?? seg.charAt(0).toUpperCase() + seg.slice(1)
    return { path, label }
  })

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
        <button
          type="button"
          onClick={onMobileMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Breadcrumbs */}
        <nav className="hidden items-center gap-1 text-sm md:flex" aria-label="Breadcrumb">
          <Link
            to="/dashboard"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Home
          </Link>
          {breadcrumbs.map((crumb, i) => (
            <span key={crumb.path} className="flex items-center gap-1">
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
              <Link
                to={crumb.path}
                className={cn(
                  'transition-colors',
                  i === breadcrumbs.length - 1
                    ? 'font-medium text-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {crumb.label}
              </Link>
            </span>
          ))}
        </nav>

        {/* Search (centered on desktop) */}
        <div className="flex-1 md:max-w-md md:mx-auto">
          <SearchField
            placeholder="Search your lectures, notes, or ask anything…"
            className="hidden sm:block"
          />
          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:hidden"
            aria-label="Search"
          >
            <Search className="h-5 w-5" />
          </button>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className="relative flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Notifications"
          >
            <Bell className="h-[18px] w-[18px]" />
            <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-accent ring-2 ring-background" />
          </button>

          <Avatar className="ml-1 h-9 w-9 ring-2 ring-border">
            <AvatarFallback className="bg-sidebar text-sidebar-foreground">D</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}

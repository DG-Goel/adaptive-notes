import { PanelLeftClose, PanelLeftOpen, X } from 'lucide-react'
import { Logo } from '@/components/common/Logo'
import { NavigationItem } from '@/components/common/NavigationItem'
import { GlassSculpture } from '@/components/three/GlassSculpture'
import { primaryNav, secondaryNav } from '@/config/nav'
import { cn } from '@/lib/utils'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  mobileOpen: boolean
  onMobileClose: () => void
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }: SidebarProps) {
  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const navContent = (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center justify-between px-4 py-5">
        <Logo
          markOnly={collapsed}
          textClassName="text-sidebar-foreground"
          className={cn('transition-opacity duration-200', collapsed ? 'opacity-0' : 'opacity-100')}
        />
        <button
          type="button"
          onClick={onToggle}
          className="hidden h-8 w-8 items-center justify-center rounded-lg text-sidebar-foreground/50 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground md:flex"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        {primaryNav.map((item) => (
          <NavigationItem
            key={item.label}
            to={item.to}
            label={item.label}
            icon={item.icon}
            collapsed={collapsed}
            badge={item.badge}
          />
        ))}
      </nav>

      {/* Mini sculpture + tagline */}
      <div className="mt-auto border-t border-sidebar-border px-3 py-4">
        <div
          className={cn(
            'flex flex-col items-center gap-3 rounded-xl bg-gradient-to-b from-sidebar-accent/40 to-transparent p-4',
          )}
        >
          <GlassSculpture variant="mini" />
          {!collapsed && (
            <div className="text-center">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-sidebar-foreground/40">
                Your AI learning space
              </p>
              <p className="mt-1 font-serif text-base leading-tight text-sidebar-foreground">
                Watch.<br />Learn. Note.<br />Understand.
              </p>
            </div>
          )}
        </div>

        <div className="mt-2">
          {secondaryNav.map((item) => (
            <NavigationItem
              key={item.label}
              to={item.to}
              label={item.label}
              icon={item.icon}
              collapsed={collapsed}
            />
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-300 md:flex',
          reduceMotion ? 'transition-none' : '',
          collapsed ? 'w-[72px]' : 'w-[248px]',
        )}
      >
        {navContent}
      </aside>

      {/* Mobile drawer */}
      <Dialog open={mobileOpen} onOpenChange={(open) => !open && onMobileClose()}>
        <DialogContent
          className="left-0 top-0 h-screen max-w-[280px] translate-x-0 translate-y-0 rounded-none border-sidebar-border bg-sidebar p-0"
          showCloseButton={false}
        >
          <DialogTitle className="sr-only">Navigation</DialogTitle>
          <DialogDescription className="sr-only">Main navigation menu</DialogDescription>
          <button
            type="button"
            onClick={onMobileClose}
            className="absolute right-4 top-5 z-10 flex h-8 w-8 items-center justify-center rounded-lg text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
          <div className="h-screen overflow-y-auto">{navContent}</div>
        </DialogContent>
      </Dialog>
    </>
  )
}

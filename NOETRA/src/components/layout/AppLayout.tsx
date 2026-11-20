import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'motion/react'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { TutorConversationProvider } from '@/context/tutor-conversation-context.tsx'

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  return (
    <TutorConversationProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((c) => !c)}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <TopNav onMobileMenuClick={() => setMobileOpen(true)} />

          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-[1400px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
              <AnimatePresence mode="wait">
                <div key={location.pathname}>
                  <Outlet />
                </div>
              </AnimatePresence>
            </div>
          </main>
        </div>
      </div>
    </TutorConversationProvider>
  )
}

import type { ReactNode } from 'react'
import { PageHeader } from '@/components/common/PageHeader'
import { PremiumCard } from '@/components/common/PremiumCard'
import { PageTransition } from '@/components/common/PageTransition'

export interface PlaceholderPageProps {
  title: string
  description: string
  eyebrow?: string
  icon?: ReactNode
  children?: ReactNode
}

export function PlaceholderPage({ title, description, eyebrow, icon, children }: PlaceholderPageProps) {
  return (
    <PageTransition>
      <div className="space-y-6">
        <PageHeader title={title} description={description} eyebrow={eyebrow} />
        <PremiumCard className="p-8">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            {icon && (
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                {icon}
              </div>
            )}
            <div>
              <h2 className="font-serif text-2xl font-medium text-foreground">Coming soon</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                This section is part of the NOETRA foundation. The full experience will be built in
                upcoming phases.
              </p>
            </div>
            {children}
          </div>
        </PremiumCard>
      </div>
    </PageTransition>
  )
}

import { Settings } from 'lucide-react'
import { PlaceholderPage } from './PlaceholderPage'

export function SettingsPage() {
  return (
    <PlaceholderPage
      eyebrow="Preferences"
      title="Settings"
      description="Manage your account, appearance, notifications, and learning preferences."
      icon={<Settings className="h-6 w-6" />}
    />
  )
}

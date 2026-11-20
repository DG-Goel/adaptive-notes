import { TutorWorkspace } from '@/components/tutor/TutorWorkspace'

/**
 * Full AI Tutor workspace.
 *
 * The conversation state lives in the shared `TutorConversationProvider`
 * (mounted in `AppLayout`), so the same conversation is visible from both this
 * full page and the compact sidebar inside the video workspace.
 */
export function TutorPage() {
  return (
    <div className="-mx-4 -my-6 h-[calc(100vh-7rem)] sm:-mx-6 lg:-mx-8 lg:-my-8">
      <TutorWorkspace />
    </div>
  )
}

import { createContext, useContext } from 'react'
import type { ExplanationPreferences, TutorContext, TutorConversation } from '@/types/tutor'
import type { tutorCapabilities } from '@/services/api/tutor'

export interface TutorConversationState {
  conversations: TutorConversation[]
  activeConversationId: string | null
  draft: string
  context: TutorContext
  preferences: ExplanationPreferences
  isSending: boolean
  error: string | null
}

export interface TutorConversationActions {
  newConversation: (context?: TutorContext, title?: string) => string
  selectConversation: (id: string) => void
  deleteConversation: (id: string) => void
  renameConversation: (id: string, title: string) => void
  setDraft: (draft: string) => void
  setContext: (context: TutorContext) => void
  setPreferences: (preferences: ExplanationPreferences) => void
  sendMessage: (question: string) => void
  retry: () => void
  regenerate: () => void
  stop: () => void
}

export type TutorConversationValue = TutorConversationState &
  TutorConversationActions & {
    activeConversation: TutorConversation | null
    capabilities: typeof tutorCapabilities
  }

export const TutorConversationContext = createContext<TutorConversationValue | null>(null)

export function useTutorConversation(): TutorConversationValue {
  const ctx = useContext(TutorConversationContext)
  if (!ctx) {
    throw new Error('useTutorConversation must be used within a TutorConversationProvider')
  }
  return ctx
}

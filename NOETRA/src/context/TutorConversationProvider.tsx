import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  askTutor,
  conversationStorage,
  tutorCapabilities,
} from '@/services/api/tutor'
import { mockTutorConversation } from '@/mocks/tutor'
import { USE_MOCK_API } from '@/config/endpoints'
import {
  TutorConversationContext,
  type TutorConversationValue,
} from './tutor-conversation-context'
import type {
  ExplanationPreferences,
  TutorContext,
  TutorConversation,
  TutorMessage,
} from '@/types/tutor'

let messageSequence = 0
function createMessageId(): string {
  messageSequence += 1
  return `tutor-msg-${Date.now()}-${messageSequence}`
}

let conversationSequence = 0
function createConversationId(): string {
  conversationSequence += 1
  return `tutor-conv-${Date.now()}-${conversationSequence}`
}

function seedConversations(): TutorConversation[] {
  if (!USE_MOCK_API) return []
  try {
    const raw = conversationStorage.list()
    const parsed = JSON.parse(raw) as TutorConversation[]
    if (Array.isArray(parsed) && parsed.length > 0) return parsed
  } catch {
    // ignore corrupted storage
  }
  return [mockTutorConversation]
}

function persistConversations(conversations: TutorConversation[]): void {
  try {
    conversationStorage.save(JSON.stringify(conversations))
  } catch {
    // storage may be unavailable; session-only is acceptable
  }
}

export function TutorConversationProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<TutorConversation[]>(seedConversations)
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    () => seedConversations()[0]?.id ?? null,
  )
  const [draft, setDraft] = useState('')
  const [context, setContext] = useState<TutorContext>({ type: 'general' })
  const [preferences, setPreferences] = useState<ExplanationPreferences>({ mode: 'detailed' })
  const [error, setError] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)
  const lastQuestionRef = useRef<string | null>(null)

  useEffect(() => {
    persistConversations(conversations)
  }, [conversations])

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConversationId) ?? null,
    [conversations, activeConversationId],
  )

  const mutation = useMutation({
    mutationFn: (variables: {
      question: string
      history: { role: TutorMessage['role']; content: string }[]
    }) => {
      const controller = new AbortController()
      abortRef.current = controller
      return askTutor({
        question: variables.question,
        history: variables.history,
        videoId: activeConversation?.videoId,
        context,
        preferences,
        signal: controller.signal,
      })
    },
    onSuccess: (response) => {
      setConversations((previous) =>
        previous.map((conversation) => {
          if (conversation.id !== activeConversationId) return conversation
          const assistant: TutorMessage = {
            id: createMessageId(),
            role: 'assistant',
            content: response.answer,
            createdAt: new Date().toISOString(),
            citations: response.citations,
            isDemo: response.isDemo,
          }
          return {
            ...conversation,
            messages: [...conversation.messages, assistant],
            updatedAt: assistant.createdAt,
          }
        }),
      )
      setError(null)
    },
    onError: (err) => {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setError(null)
        return
      }
      const message = err instanceof Error ? err.message : 'The tutor could not answer right now.'
      setError(message)
      setConversations((previous) =>
        previous.map((conversation) => {
          if (conversation.id !== activeConversationId) return conversation
          const failed: TutorMessage = {
            id: createMessageId(),
            role: 'assistant',
            content: '',
            createdAt: new Date().toISOString(),
            error: message,
          }
          return {
            ...conversation,
            messages: [...conversation.messages, failed],
            updatedAt: failed.createdAt,
          }
        }),
      )
    },
    onSettled: () => {
      abortRef.current = null
    },
  })

  const ensureConversation = useCallback((): string => {
    if (activeConversationId) return activeConversationId
    const id = createConversationId()
    const now = new Date().toISOString()
    const newConversation: TutorConversation = {
      id,
      title: 'New conversation',
      context,
      messages: [],
      createdAt: now,
      updatedAt: now,
      isDemo: false,
    }
    setConversations((previous) => [newConversation, ...previous])
    setActiveConversationId(id)
    return id
  }, [activeConversationId, context])

  const newConversation = useCallback(
    (ctx?: TutorContext, title?: string): string => {
      const id = createConversationId()
      const now = new Date().toISOString()
      const conversation: TutorConversation = {
        id,
        title: title ?? 'New conversation',
        videoId: ctx && 'videoId' in ctx ? ctx.videoId : undefined,
        context: ctx ?? context,
        messages: [],
        createdAt: now,
        updatedAt: now,
        isDemo: false,
      }
      setConversations((previous) => [conversation, ...previous])
      setActiveConversationId(id)
      setError(null)
      if (ctx) setContext(ctx)
      return id
    },
    [context],
  )

  const selectConversation = useCallback((id: string) => {
    setActiveConversationId(id)
    setError(null)
  }, [])

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((previous) => {
        const next = previous.filter((c) => c.id !== id)
        if (activeConversationId === id) {
          setActiveConversationId(next[0]?.id ?? null)
        }
        return next
      })
    },
    [activeConversationId],
  )

  const renameConversation = useCallback((id: string, title: string) => {
    setConversations((previous) =>
      previous.map((c) => (c.id === id ? { ...c, title } : c)),
    )
  }, [])

  const buildHistory = useCallback(
    (conversation: TutorConversation): { role: TutorMessage['role']; content: string }[] =>
      conversation.messages
        .filter((m) => !m.error && !m.isDemo)
        .map((m) => ({ role: m.role, content: m.content })),
    [],
  )

  const sendMessage = useCallback(
    (question: string) => {
      const trimmed = question.trim()
      if (!trimmed || mutation.isPending) return
      const id = ensureConversation()
      lastQuestionRef.current = trimmed

      const userMessage: TutorMessage = {
        id: createMessageId(),
        role: 'user',
        content: trimmed,
        createdAt: new Date().toISOString(),
      }

      setConversations((previous) =>
        previous.map((c) =>
          c.id === id
            ? {
                ...c,
                messages: [...c.messages, userMessage],
                title: c.messages.length === 0 ? trimmed.slice(0, 60) : c.title,
                updatedAt: userMessage.createdAt,
              }
            : c,
        ),
      )
      setDraft('')

      const conversation = conversations.find((c) => c.id === id)
      const history = conversation ? buildHistory(conversation) : []
      mutation.mutate({ question: trimmed, history })
    },
    [ensureConversation, mutation, conversations, buildHistory],
  )

  const retry = useCallback(() => {
    if (!lastQuestionRef.current || mutation.isPending) return
    const conversation = activeConversation
    const history = conversation ? buildHistory(conversation) : []
    setConversations((previous) =>
      previous.map((c) => {
        if (c.id !== activeConversationId) return c
        const messages = [...c.messages]
        if (
          messages.length > 0 &&
          messages[messages.length - 1]!.role === 'assistant' &&
          messages[messages.length - 1]!.error
        ) {
          messages.pop()
        }
        return { ...c, messages }
      }),
    )
    mutation.mutate({ question: lastQuestionRef.current, history })
  }, [activeConversation, activeConversationId, buildHistory, mutation])

  const regenerate = useCallback(() => {
    const conversation = activeConversation
    if (!conversation || mutation.isPending) return
    const lastUser = [...conversation.messages].reverse().find((m) => m.role === 'user')
    if (!lastUser) return
    lastQuestionRef.current = lastUser.content
    setConversations((previous) =>
      previous.map((c) => {
        if (c.id !== activeConversationId) return c
        const messages = [...c.messages]
        if (messages.length > 0 && messages[messages.length - 1]!.role === 'assistant') {
          messages.pop()
        }
        return { ...c, messages }
      }),
    )
    const history = buildHistory({
      ...conversation,
      messages: conversation.messages.slice(0, -1),
    })
    mutation.mutate({ question: lastUser.content, history })
  }, [activeConversation, activeConversationId, buildHistory, mutation])

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const value = useMemo<TutorConversationValue>(
    () => ({
      conversations,
      activeConversationId,
      activeConversation,
      draft,
      context,
      preferences,
      isSending: mutation.isPending,
      error,
      capabilities: tutorCapabilities,
      newConversation,
      selectConversation,
      deleteConversation,
      renameConversation,
      setDraft,
      setContext,
      setPreferences,
      sendMessage,
      retry,
      regenerate,
      stop,
    }),
    [
      conversations,
      activeConversationId,
      activeConversation,
      draft,
      context,
      preferences,
      mutation.isPending,
      error,
      newConversation,
      selectConversation,
      deleteConversation,
      renameConversation,
      sendMessage,
      retry,
      regenerate,
      stop,
    ],
  )

  return (
    <TutorConversationContext.Provider value={value}>{children}</TutorConversationContext.Provider>
  )
}

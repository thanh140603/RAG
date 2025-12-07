import { create } from 'zustand'
import { ChatSession, ChatMessage } from '../../domain/entities/ChatMessage'
import { ChatService } from '../../application/services/ChatService'
import { chatApi } from '../../infrastructure/api/ChatApi'

interface ChatState {
  sessions: ChatSession[]
  currentSession: ChatSession | null
  messages: ChatMessage[]
  isLoading: boolean
  isSending: boolean
  error: string | null
  fetchSessions: () => Promise<void>
  createSession: (title?: string) => Promise<ChatSession>
  selectSession: (sessionId: string) => Promise<void>
  sendMessage: (query: string, groupId?: string | null) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  updateSessionTitle: (id: string, title: string) => Promise<void>
  setError: (error: string | null) => void
}

const chatService = new ChatService(chatApi)

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  isLoading: false,
  isSending: false,
  error: null,

  fetchSessions: async () => {
    set({ isLoading: true, error: null })
    try {
      const sessions = await chatService.getSessions()
      set({ sessions, isLoading: false })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch sessions',
        isLoading: false,
      })
    }
  },

  createSession: async (title?: string) => {
    set({ isLoading: true, error: null })
    try {
      const session = await chatService.createSession(title)
      set((state) => ({
        sessions: [session, ...state.sessions],
        currentSession: session,
        messages: session.messages || [],
        isLoading: false,
      }))
      return session
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to create session',
        isLoading: false,
      })
      throw error
    }
  },

  selectSession: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      const session = await chatService.getSession(sessionId)
      set({
        currentSession: session,
        messages: session.messages || [],
        isLoading: false,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to load session',
        isLoading: false,
      })
    }
  },

  sendMessage: async (query: string, groupId?: string | null) => {
    if (!query.trim()) return

    const currentSession = get().currentSession
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSession?.id || '',
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    }

    // Add user message immediately
    set((state) => ({
      messages: [...state.messages, userMessage],
      isSending: true,
      error: null,
    }))

    try {
      const response = await chatService.sendMessage(
        query,
        currentSession?.id,
        groupId
      )

      // Build assistant message locally from backend response text
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        session_id: currentSession?.id || '',
        role: 'assistant',
        content: response.message,
        created_at: new Date().toISOString(),
      }

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isSending: false,
      }))

      // Refresh sessions to get updated title (auto-generated after first message)
      if (currentSession) {
        await get().fetchSessions()
        // Update current session if title changed
        const updatedSessions = await chatService.getSessions()
        const updatedSession = updatedSessions.find((s) => s.id === currentSession.id)
        if (updatedSession && updatedSession.title !== currentSession.title) {
          set({
            currentSession: updatedSession,
          })
        }
      }
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to send message',
        isSending: false,
        messages: get().messages.filter((m) => m.id !== userMessage.id),
      })
    }
  },

  deleteSession: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await chatService.deleteSession(id)
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        currentSession:
          state.currentSession?.id === id ? null : state.currentSession,
        messages: state.currentSession?.id === id ? [] : state.messages,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete session',
        isLoading: false,
      })
    }
  },

  updateSessionTitle: async (id: string, title: string) => {
    set({ isLoading: true, error: null })
    try {
      const updatedSession = await chatService.updateSessionTitle(id, title)
      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? updatedSession : s
        ),
        currentSession:
          state.currentSession?.id === id
            ? updatedSession
            : state.currentSession,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to update title',
        isLoading: false,
      })
    }
  },

  setError: (error) => set({ error }),
}))


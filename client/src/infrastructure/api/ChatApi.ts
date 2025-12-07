import { apiClient } from './apiClient'
import { ChatMessage, ChatSession } from '../../domain/entities/ChatMessage'

export interface ChatQueryRequest {
  query: string
  chat_id?: string
  use_multi_query?: boolean
  use_step_back?: boolean
  group_id?: string | null
}

// Backend /api/rag/query currently returns a simple shape:
// { message: string, sources: string[], metadata: object }
export interface ChatQueryResponse {
  message: string
  sources: string[]
  metadata: Record<string, any>
}

// Backend /api/chats/{chat_id}/messages response format
interface SendMessageResponse {
  assistant_message: ChatMessage
  sources: string[]
  metadata: Record<string, any>
}

export class ChatApi {
  async query(request: ChatQueryRequest): Promise<ChatQueryResponse> {
    // Use /api/chats/{chat_id}/messages endpoint to save messages and auto-generate title
    if (request.chat_id) {
      const response = await apiClient.post<SendMessageResponse>(
        `/api/chats/${request.chat_id}/messages`,
        {
          content: request.query,
          use_multi_query: request.use_multi_query,
          use_step_back: request.use_step_back,
          group_id: request.group_id || null,  // Pass group_id to filter documents
        }
      )
      // Convert SendMessageResponse to ChatQueryResponse format
      return {
        message: response.data.assistant_message.content,
        sources: response.data.sources,
        metadata: response.data.metadata,
      }
    } else {
      // Fallback to /api/rag/query if no chat_id (shouldn't happen in normal flow)
      const response = await apiClient.post<ChatQueryResponse>(
        '/api/rag/query',
        request
      )
      return response.data
    }
  }

  async getSessions(): Promise<ChatSession[]> {
    // Backend routes: GET /api/chats/ (note trailing slash, redirect_slashes=False on backend)
    const response = await apiClient.get<ChatSession[]>('/api/chats/')
    return response.data
  }

  async getSession(id: string): Promise<ChatSession> {
    // Backend routes: GET /api/chats/{chat_id}
    const response = await apiClient.get<ChatSession>(`/api/chats/${id}`)
    return response.data
  }

  async createSession(title?: string): Promise<ChatSession> {
    // Backend routes: POST /api/chats/ (note trailing slash)
    const response = await apiClient.post<ChatSession>('/api/chats/', {
      title,
    })
    return response.data
  }

  async deleteSession(id: string): Promise<void> {
    // Backend routes: DELETE /api/chats/{chat_id} (not yet implemented on backend)
    await apiClient.delete(`/api/chats/${id}`)
  }

  async updateSessionTitle(id: string, title: string): Promise<ChatSession> {
    // Backend routes: PATCH /api/chats/{chat_id}
    const response = await apiClient.patch<ChatSession>(`/api/chats/${id}`, {
      title,
    })
    return response.data
  }
}

export const chatApi = new ChatApi()


import { ChatApi, ChatQueryRequest, ChatQueryResponse } from '../../infrastructure/api/ChatApi'
import { ChatSession, ChatMessage } from '../../domain/entities/ChatMessage'

export class ChatService {
  constructor(private chatApi: ChatApi) {}

  async sendMessage(
    query: string,
    sessionId?: string,
    groupId?: string | null
  ): Promise<ChatQueryResponse> {
    const request: ChatQueryRequest = {
      query,
      chat_id: sessionId,
      use_multi_query: true,
      use_step_back: false,
      group_id: groupId || null,
    }
    return await this.chatApi.query(request)
  }

  async getSessions(): Promise<ChatSession[]> {
    return await this.chatApi.getSessions()
  }

  async getSession(id: string): Promise<ChatSession> {
    return await this.chatApi.getSession(id)
  }

  async createSession(title?: string): Promise<ChatSession> {
    return await this.chatApi.createSession(title)
  }

  async deleteSession(id: string): Promise<void> {
    await this.chatApi.deleteSession(id)
  }

  async updateSessionTitle(id: string, title: string): Promise<ChatSession> {
    return await this.chatApi.updateSessionTitle(id, title)
  }
}


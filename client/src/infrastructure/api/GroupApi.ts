import { apiClient } from './apiClient'
import { DocumentGroup, CreateGroupRequest, UpdateGroupRequest } from '../../domain/entities/DocumentGroup'

export class GroupApi {
  async list(): Promise<DocumentGroup[]> {
    const response = await apiClient.get<DocumentGroup[]>('/api/groups')
    return response.data
  }

  async getById(id: string): Promise<DocumentGroup> {
    const response = await apiClient.get<DocumentGroup>(`/api/groups/${id}`)
    return response.data
  }

  async create(request: CreateGroupRequest): Promise<DocumentGroup> {
    const response = await apiClient.post<DocumentGroup>('/api/groups', request)
    return response.data
  }

  async update(id: string, request: UpdateGroupRequest): Promise<DocumentGroup> {
    const response = await apiClient.put<DocumentGroup>(`/api/groups/${id}`, request)
    return response.data
  }

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/api/groups/${id}`)
  }
}

export const groupApi = new GroupApi()


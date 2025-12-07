import { GroupApi } from '../../infrastructure/api/GroupApi'
import { DocumentGroup, CreateGroupRequest, UpdateGroupRequest } from '../../domain/entities/DocumentGroup'

export class GroupService {
  constructor(private groupApi: GroupApi) {}

  async listGroups(): Promise<DocumentGroup[]> {
    return this.groupApi.list()
  }

  async getGroup(id: string): Promise<DocumentGroup> {
    return this.groupApi.getById(id)
  }

  async createGroup(request: CreateGroupRequest): Promise<DocumentGroup> {
    return this.groupApi.create(request)
  }

  async updateGroup(id: string, request: UpdateGroupRequest): Promise<DocumentGroup> {
    return this.groupApi.update(id, request)
  }

  async deleteGroup(id: string): Promise<void> {
    return this.groupApi.delete(id)
  }
}


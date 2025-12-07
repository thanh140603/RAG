import { create } from 'zustand'
import { DocumentGroup, CreateGroupRequest, UpdateGroupRequest } from '../../domain/entities/DocumentGroup'
import { GroupService } from '../../application/services/GroupService'
import { groupApi } from '../../infrastructure/api/GroupApi'

interface GroupState {
  groups: DocumentGroup[]
  isLoading: boolean
  error: string | null
  selectedGroupId: string | null
  fetchGroups: () => Promise<void>
  createGroup: (request: CreateGroupRequest) => Promise<DocumentGroup>
  updateGroup: (id: string, request: UpdateGroupRequest) => Promise<DocumentGroup>
  deleteGroup: (id: string) => Promise<void>
  setSelectedGroupId: (id: string | null) => void
}

const groupService = new GroupService(groupApi)

export const useGroupStore = create<GroupState>((set, get) => ({
  groups: [],
  isLoading: false,
  error: null,
  selectedGroupId: null,

  fetchGroups: async () => {
    set({ isLoading: true, error: null })
    try {
      const groups = await groupService.listGroups()
      set({ groups, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch groups',
        isLoading: false,
      })
    }
  },

  createGroup: async (request: CreateGroupRequest) => {
    set({ error: null })
    try {
      const newGroup = await groupService.createGroup(request)
      set((state) => ({
        groups: [...state.groups, newGroup],
      }))
      return newGroup
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create group'
      set({ error: errorMessage })
      throw error
    }
  },

  updateGroup: async (id: string, request: UpdateGroupRequest) => {
    set({ error: null })
    try {
      const updatedGroup = await groupService.updateGroup(id, request)
      set((state) => ({
        groups: state.groups.map((g) => (g.id === id ? updatedGroup : g)),
      }))
      return updatedGroup
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update group'
      set({ error: errorMessage })
      throw error
    }
  },

  deleteGroup: async (id: string) => {
    set({ error: null })
    try {
      await groupService.deleteGroup(id)
      set((state) => ({
        groups: state.groups.filter((g) => g.id !== id),
        selectedGroupId: state.selectedGroupId === id ? null : state.selectedGroupId,
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete group'
      set({ error: errorMessage })
      throw error
    }
  },

  setSelectedGroupId: (id: string | null) => {
    set({ selectedGroupId: id })
  },
}))


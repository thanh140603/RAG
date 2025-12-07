export interface DocumentGroup {
  id: string
  user_id: string
  name: string
  description: string | null
  color: string | null // Hex color like "#3B82F6"
  created_at: string
  updated_at: string
}

export interface CreateGroupRequest {
  name: string
  description?: string | null
  color?: string | null
}

export interface UpdateGroupRequest {
  name?: string
  description?: string | null
  color?: string | null
}


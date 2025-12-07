export type DocumentStatus = 'pending' | 'processing' | 'indexed' | 'error'

export interface Document {
  id: string
  user_id: string
  filename: string
  file_size: number
  mime_type: string
  status: DocumentStatus
  storage_key?: string
  checksum?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}


export interface UploadRequest {
  files: Array<{
    filename: string
    file_size: number
    content_type: string
  }>
  group_id?: string | null
}

export interface UploadRequestResponse {
  uploads: Array<{
    document_id: string
    filename: string
    content_type: string
    upload_url: string
    storage_key: string
    expires_in: number
  }>
}

export interface UploadConfirmRequest {
  document_id: string
  file_size: number
  checksum?: string
  metadata?: Record<string, any>
  group_id?: string | null
}


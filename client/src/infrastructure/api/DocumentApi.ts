import axios from 'axios'
import { apiClient } from './apiClient'
import {
  UploadRequest,
  UploadRequestResponse,
  UploadConfirmRequest,
} from '../../domain/entities/UploadRequest'
import { Document } from '../../domain/entities/Document'

export class DocumentApi {
  async requestUpload(request: UploadRequest): Promise<UploadRequestResponse> {
    const response = await apiClient.post<UploadRequestResponse>(
      '/api/documents/upload-request',
      request
    )
    return response.data
  }

  async confirmUpload(request: UploadConfirmRequest): Promise<Document> {
    const response = await apiClient.post<Document>(
      '/api/documents/upload/confirm',
      request
    )
    return response.data
  }

  async uploadFile(uploadUrl: string, file: File): Promise<void> {
    await axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type,
      },
    })
  }

  async getDocuments(): Promise<Document[]> {
    const response = await apiClient.get<Document[]>('/api/documents/')
    return response.data
  }

  async getDocument(id: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/api/documents/${id}`)
    return response.data
  }

  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/api/documents/${id}`)
  }
}

export const documentApi = new DocumentApi()


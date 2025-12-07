import { DocumentApi } from '../../infrastructure/api/DocumentApi'
import {
  UploadRequest,
  UploadRequestResponse,
  UploadConfirmRequest,
} from '../../domain/entities/UploadRequest'
import { Document } from '../../domain/entities/Document'

export class DocumentService {
  constructor(private documentApi: DocumentApi) {}

  async uploadFile(file: File, groupId?: string | null): Promise<Document> {
    // Step 1: Request upload URL
    const uploadRequest: UploadRequest = {
      files: [
        {
          filename: file.name,
          file_size: file.size,
          content_type: file.type,
        },
      ],
      group_id: groupId || null,
    }

    const response = await this.documentApi.requestUpload(uploadRequest)
    const uploadItem = response.uploads[0]

    // Step 2: Upload file to presigned URL
    await this.documentApi.uploadFile(uploadItem.upload_url, file)

    // Step 3: Confirm upload (triggers background ingestion)
    const confirmRequest: UploadConfirmRequest = {
      document_id: uploadItem.document_id,
      file_size: file.size,
      group_id: groupId || null,
    }

    return await this.documentApi.confirmUpload(confirmRequest)
  }

  async getDocuments(): Promise<Document[]> {
    return await this.documentApi.getDocuments()
  }

  async getDocument(id: string): Promise<Document> {
    return await this.documentApi.getDocument(id)
  }

  async deleteDocument(id: string): Promise<void> {
    await this.documentApi.deleteDocument(id)
  }
}


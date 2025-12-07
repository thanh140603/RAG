import { create } from 'zustand'
import { Document } from '../../domain/entities/Document'
import { DocumentService } from '../../application/services/DocumentService'
import { documentApi } from '../../infrastructure/api/DocumentApi'

interface DocumentState {
  documents: Document[]
  selectedDocument: Document | null
  isLoading: boolean
  error: string | null
  uploadProgress: number
  fetchDocuments: () => Promise<void>
  uploadFile: (file: File, groupId?: string | null) => Promise<Document>
  selectDocument: (document: Document | null) => void
  deleteDocument: (id: string) => Promise<void>
  setError: (error: string | null) => void
}

const documentService = new DocumentService(documentApi)

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  selectedDocument: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,

  fetchDocuments: async () => {
    set({ isLoading: true, error: null })
    try {
      const documents = await documentService.getDocuments()
      set({ documents, isLoading: false })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch documents',
        isLoading: false,
      })
    }
  },

  uploadFile: async (file: File, groupId?: string | null) => {
    set({ isLoading: true, error: null, uploadProgress: 0 })
    try {
      // Simulate progress (actual upload happens in service)
      const progressInterval = setInterval(() => {
        set((state) => ({
          uploadProgress: Math.min(state.uploadProgress + 10, 90),
        }))
      }, 200)

      const document = await documentService.uploadFile(file, groupId)
      
      clearInterval(progressInterval)
      set({ uploadProgress: 100 })

      // Refresh documents list
      await get().fetchDocuments()

      set({ isLoading: false, uploadProgress: 0 })
      return document
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Upload failed',
        isLoading: false,
        uploadProgress: 0,
      })
      throw error
    }
  },

  selectDocument: (document) => set({ selectedDocument: document }),

  deleteDocument: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await documentService.deleteDocument(id)
      set((state) => ({
        documents: state.documents.filter((doc) => doc.id !== id),
        selectedDocument:
          state.selectedDocument?.id === id ? null : state.selectedDocument,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Delete failed',
        isLoading: false,
      })
    }
  },

  setError: (error) => set({ error }),
}))


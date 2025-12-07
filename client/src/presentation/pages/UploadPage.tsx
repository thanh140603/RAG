import { useState, useRef, useEffect } from 'react'
import { useDocumentStore } from '../stores/useDocumentStore'
import { useGroupStore } from '../stores/useGroupStore'
import { GroupManager } from '../components/GroupManager'

export const UploadPage = () => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [isGroupManagerOpen, setIsGroupManagerOpen] = useState(false)
  const {
    documents,
    isLoading,
    error,
    uploadProgress,
    uploadFile,
    fetchDocuments,
    deleteDocument,
  } = useDocumentStore()
  const {
    groups,
    fetchGroups,
    selectedGroupId: storeSelectedGroupId,
    setSelectedGroupId: setStoreSelectedGroupId,
  } = useGroupStore()

  useEffect(() => {
    fetchDocuments()
    fetchGroups()
  }, [fetchDocuments, fetchGroups])

  useEffect(() => {
    if (storeSelectedGroupId !== null) {
      setSelectedGroupId(storeSelectedGroupId)
    }
  }, [storeSelectedGroupId])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    try {
      await uploadFile(file, selectedGroupId)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      // Error handled by store
    }
  }

  const filteredDocuments = selectedGroupId
    ? documents.filter((doc) => (doc as any).group_id === selectedGroupId)
    : documents

  const handleGroupChange = (groupId: string | null) => {
    setSelectedGroupId(groupId)
    setStoreSelectedGroupId(groupId)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* Upload Area - Left */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.html,.md"
          disabled={isLoading}
        />

        {error && (
          <div className="mb-4 w-full max-w-2xl rounded-md bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        {/* Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`w-full max-w-2xl border-2 border-dashed rounded-xl p-12 text-center transition-all ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white hover:border-gray-400'
          }`}
        >
          <div className="space-y-6">
            {/* Upload Icon */}
            <div className="flex justify-center">
              <svg
                className="w-16 h-16 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Upload Documents
              </h3>
              <p className="text-gray-600 mb-4">
                Drag and drop files here, or click to browse
              </p>

              {/* Group Selector */}
              <div className="mb-6 w-full max-w-md mx-auto">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assign to Group (Optional)
                </label>
                <select
                  value={selectedGroupId || ''}
                  onChange={(e) => handleGroupChange(e.target.value || null)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No Group</option>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-center space-x-4">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Choose File
                </button>
                <button
                  type="button"
                  className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  Paste Text
                </button>
              </div>

              <p className="mt-4 text-sm text-gray-500">
                Supported formats: TXT, MD, DOC, DOCX, PDF
              </p>
            </div>

            {isLoading && uploadProgress > 0 && (
              <div className="mt-6">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="mt-2 text-sm text-gray-600">
                  Uploading... {uploadProgress}%
                </p>
              </div>
            )}
          </div>
        </div>

        {/* How it works */}
        <div className="mt-8 w-full max-w-2xl">
          <h4 className="text-lg font-semibold text-blue-600 mb-2">How it works:</h4>
          <p className="text-gray-600">
            Upload documents to build your knowledge base. The chatbot will retrieve
            relevant information from these documents to answer your questions.
          </p>
        </div>
      </div>

      {/* Knowledge Base Sidebar - Right */}
      <div className="w-64 bg-white border-l border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">RAG Chatbot</h1>
              <p className="text-xs text-gray-500">Retrieval-Augmented Generation</p>
            </div>
          </div>
        </div>

        {/* Upload Button */}
        <div className="p-4 space-y-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Upload Document
          </button>
          <button
            onClick={() => setIsGroupManagerOpen(true)}
            className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Manage Groups
          </button>
        </div>

        {/* Group Filter */}
        <div className="px-4 py-2 border-b border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Group
          </label>
          <select
            value={selectedGroupId || ''}
            onChange={(e) => handleGroupChange(e.target.value || null)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Groups</option>
            {groups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.name}
              </option>
            ))}
          </select>
        </div>

        {/* Documents Count */}
        <div className="px-4 py-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Documents</h2>
          <p className="text-2xl font-bold text-gray-900">{filteredDocuments.length}</p>
          <p className="text-xs text-gray-500 mt-1">
            {selectedGroupId ? 'filtered documents' : 'total documents'}
          </p>
        </div>

        {/* Documents List */}
               <div className="flex-1 overflow-y-auto px-4 pb-4">
                 {filteredDocuments.length === 0 ? (
                   <p className="text-sm text-gray-400 mt-4">
                     {selectedGroupId ? 'No documents in this group' : 'No documents uploaded yet'}
                   </p>
                 ) : (
                   <div className="space-y-2">
                     {filteredDocuments.map((doc) => {
                       const docGroup = groups.find((g) => g.id === (doc as any).group_id);
                       return (
                         <div
                           key={doc.id}
                           className="p-2 rounded-lg hover:bg-gray-50 cursor-pointer group"
                         >
                           <div className="flex items-start justify-between">
                             <div className="flex-1 min-w-0">
                               <p className="text-sm font-medium text-gray-900 truncate">
                                 {doc.filename}
                               </p>
                               <div className="flex items-center gap-2 mt-1">
                                 <p className="text-xs text-gray-500">
                                   {formatFileSize(doc.file_size)}
                                 </p>
                                 {docGroup && (
                                   <span
                                     className="text-xs px-2 py-0.5 rounded-full text-white"
                                     style={{
                                       backgroundColor: docGroup.color || '#3B82F6',
                                     }}
                                   >
                                     {docGroup.name}
                                   </span>
                                 )}
                               </div>
                             </div>
                             <button
                               onClick={(e) => {
                                 e.stopPropagation()
                                 deleteDocument(doc.id)
                               }}
                               className="opacity-0 group-hover:opacity-100 ml-2 text-red-500 hover:text-red-700"
                             >
                               <svg
                                 className="w-4 h-4"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                               >
                                 <path
                                   strokeLinecap="round"
                                   strokeLinejoin="round"
                                   strokeWidth={2}
                                   d="M6 18L18 6M6 6l12 12"
                                 />
                               </svg>
                             </button>
                           </div>
                         </div>
                       )
                     })}
                   </div>
                 )}
               </div>

        {/* Tip */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-start space-x-2">
            <svg
              className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <p className="text-xs text-gray-600">
              <span className="font-semibold">Tip:</span> Upload text files, PDFs, or paste
              content to build your knowledge base.
            </p>
          </div>
        </div>
      </div>

      {/* Group Manager Modal */}
      <GroupManager isOpen={isGroupManagerOpen} onClose={() => setIsGroupManagerOpen(false)} />
    </div>
  )
}
import { useState, useEffect, useRef } from 'react'
import { useChatStore } from '../stores/useChatStore'
import { useGroupStore } from '../stores/useGroupStore'
import { ChatMessage } from '../../domain/entities/ChatMessage'
import { ConfirmModal } from '../components/ConfirmModal'

export const ChatPage = () => {
  const [input, setInput] = useState('')
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const {
    currentSession,
    messages,
    isSending,
    error,
    sendMessage,
    createSession,
    fetchSessions,
    sessions,
    selectSession,
    updateSessionTitle,
    deleteSession,
  } = useChatStore()
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const titleInputRef = useRef<HTMLInputElement>(null)
  const { groups, fetchGroups, selectedGroupId: storeSelectedGroupId, setSelectedGroupId: setStoreSelectedGroupId } = useGroupStore()

  useEffect(() => {
    fetchSessions()
    fetchGroups()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (storeSelectedGroupId !== null) {
      setSelectedGroupId(storeSelectedGroupId)
    }
  }, [storeSelectedGroupId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // Auto focus input
    inputRef.current?.focus()
  }, [messages])

  useEffect(() => {
    // Auto focus title input when editing
    if (editingSessionId && titleInputRef.current) {
      titleInputRef.current.focus()
      titleInputRef.current.select()
    }
  }, [editingSessionId])

  const handleRenameClick = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    setEditTitle(session?.title || 'New Chat')
    setEditingSessionId(sessionId)
    setMenuOpenId(null)
  }

  const handleSaveRename = async () => {
    if (editingSessionId && editTitle.trim()) {
      await updateSessionTitle(editingSessionId, editTitle.trim())
      setEditingSessionId(null)
      setEditTitle('')
    }
  }

  const handleCancelRename = () => {
    setEditingSessionId(null)
    setEditTitle('')
  }

  const handleDeleteClick = (sessionId: string) => {
    setSessionToDelete(sessionId)
    setDeleteConfirmOpen(true)
    setMenuOpenId(null)
  }

  const handleConfirmDelete = async () => {
    if (sessionToDelete) {
      setIsDeleting(true)
      try {
        await deleteSession(sessionToDelete)
        setDeleteConfirmOpen(false)
        setSessionToDelete(null)
      } catch (error) {
        console.error('Failed to delete session:', error)
      } finally {
        setIsDeleting(false)
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSending) return

    const query = input
    setInput('')
    await sendMessage(query, selectedGroupId)
  }

  const handleGroupChange = (groupId: string | null) => {
    setSelectedGroupId(groupId)
    setStoreSelectedGroupId(groupId)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      // Don't close if clicking inside the menu or the menu button
      if (menuOpenId && !target.closest('.chat-menu') && !target.closest('.chat-menu-button')) {
        setMenuOpenId(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [menuOpenId])

  return (
    <div className="flex h-full bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 flex items-center gap-3">
              {editingSessionId === currentSession?.id ? (
                <div className="flex items-center gap-2 flex-1 max-w-md">
                  <input
                    ref={titleInputRef}
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleSaveRename()
                      } else if (e.key === 'Escape') {
                        handleCancelRename()
                      }
                    }}
                    onBlur={handleSaveRename}
                    className="flex-1 px-3 py-1.5 text-lg font-semibold text-gray-900 border border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSaveRename}
                    className="p-1.5 text-green-600 hover:text-green-700"
                    title="Save"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                  <button
                    onClick={handleCancelRename}
                    className="p-1.5 text-gray-400 hover:text-gray-600"
                    title="Cancel"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold text-gray-900">
                    {currentSession?.title || 'RAG Chatbot'}
                  </h2>
                  {currentSession && (
                    <button
                      onClick={() => handleRenameClick(currentSession.id)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Rename chat"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}
                </div>
              )}
            </div>
            <div className="w-64">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Query from Group
              </label>
              <select
                value={selectedGroupId || ''}
                onChange={(e) => handleGroupChange(e.target.value || null)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Documents</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-white">
          {error && (
            <div className="mx-auto max-w-3xl px-4 pt-4">
              <div className="rounded-md bg-red-50 p-4">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          )}

          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-2xl px-4">
                <div className="mb-6">
                  <svg
                    className="mx-auto h-16 w-16 text-gray-300"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                  How can I help you today?
                </h3>
                <p className="text-gray-500">
                  Ask questions about your uploaded documents
                </p>
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl px-4 py-8">
              <div className="space-y-6">
                {messages.map((message: ChatMessage, index: number) => (
                  <div
                    key={message.id || `msg-${index}`}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0 mr-3">
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                          <svg
                            className="w-5 h-5 text-white"
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
                        </div>
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>
                    {message.role === 'user' && (
                      <div className="flex-shrink-0 ml-3">
                        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                          <svg
                            className="w-5 h-5 text-gray-600"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {isSending && (
                  <div className="flex justify-start">
                    <div className="flex-shrink-0 mr-3">
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                        <svg
                          className="w-5 h-5 text-white"
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
                      </div>
                    </div>
                    <div className="bg-gray-100 rounded-2xl px-4 py-3">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: '0.1s' }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: '0.2s' }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-4 py-4">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message RAG Chatbot..."
                disabled={isSending}
                rows={1}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  maxHeight: '200px',
                  minHeight: '48px',
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`
                }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isSending}
                className="absolute right-2 bottom-2 p-2 text-blue-600 hover:text-blue-700 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </form>
            <p className="text-xs text-gray-500 mt-2 text-center">
              RAG Chatbot can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>

      {/* Chat Sessions Sidebar - Right */}
      <div className="w-64 bg-gray-900 text-white flex flex-col border-l border-gray-800">
        <div className="p-4 border-b border-gray-800">
          <button
            onClick={() => createSession('New Chat')}
            className="w-full flex items-center justify-center px-4 py-2 bg-white text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
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
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          <div className="space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative flex items-center ${
                  currentSession?.id === session.id
                    ? 'bg-gray-800'
                    : 'hover:bg-gray-800'
                } rounded-lg`}
              >
                {editingSessionId === session.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={async () => {
                      if (editTitle.trim()) {
                        await updateSessionTitle(session.id, editTitle.trim())
                      }
                      setEditingSessionId(null)
                      setEditTitle('')
                    }}
                    onKeyDown={async (e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        if (editTitle.trim()) {
                          await updateSessionTitle(session.id, editTitle.trim())
                        }
                        setEditingSessionId(null)
                        setEditTitle('')
                      } else if (e.key === 'Escape') {
                        setEditingSessionId(null)
                        setEditTitle('')
                      }
                    }}
                    autoFocus
                    className="flex-1 px-3 py-2 bg-gray-700 text-white rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <>
                    <button
                      onClick={() => selectSession(session.id)}
                      className={`flex-1 text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        currentSession?.id === session.id
                          ? 'text-white'
                          : 'text-gray-300'
                      }`}
                    >
                      <div className="truncate">
                        {session.title || 'New Chat'}
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setMenuOpenId(menuOpenId === session.id ? null : session.id)
                      }}
                      className="chat-menu-button opacity-0 group-hover:opacity-100 px-2 py-1 text-gray-400 hover:text-white transition-opacity"
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
                          d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                        />
                      </svg>
                    </button>
                    {menuOpenId === session.id && (
                      <div className="chat-menu absolute right-0 top-8 z-10 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRenameClick(session.id)
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        >
                          <svg
                            className="w-4 h-4 mr-2"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                          Rename
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteClick(session.id)
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                        >
                          <svg
                            className="w-4 h-4 mr-2"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                          Delete
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Confirm Delete Modal */}
      <ConfirmModal
        isOpen={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false)
          setSessionToDelete(null)
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Chat Session"
        message={`Are you sure you want to delete "${sessions.find(s => s.id === sessionToDelete)?.title || 'this chat'}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  )
}

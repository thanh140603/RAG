import { useState } from 'react'
import { useGroupStore } from '../stores/useGroupStore'
import { DocumentGroup, CreateGroupRequest, UpdateGroupRequest } from '../../domain/entities/DocumentGroup'

interface GroupManagerProps {
  isOpen: boolean
  onClose: () => void
}

const DEFAULT_COLORS = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#84CC16', // Lime
]

export const GroupManager = ({ isOpen, onClose }: GroupManagerProps) => {
  const { groups, createGroup, updateGroup, deleteGroup, error } = useGroupStore()
  const [editingGroup, setEditingGroup] = useState<DocumentGroup | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState(DEFAULT_COLORS[0])

  const resetForm = () => {
    setEditingGroup(null)
    setName('')
    setDescription('')
    setColor(DEFAULT_COLORS[0])
  }

  const handleCreate = async () => {
    if (!name.trim()) return

    try {
      await createGroup({ name: name.trim(), description: description.trim() || null, color })
      resetForm()
    } catch (err) {
      // Error handled by store
    }
  }

  const handleUpdate = async () => {
    if (!editingGroup || !name.trim()) return

    try {
      await updateGroup(editingGroup.id, {
        name: name.trim(),
        description: description.trim() || null,
        color,
      })
      resetForm()
    } catch (err) {
      // Error handled by store
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this group? Documents will be ungrouped.')) {
      return
    }

    try {
      await deleteGroup(id)
    } catch (err) {
      // Error handled by store
    }
  }

  const startEdit = (group: DocumentGroup) => {
    setEditingGroup(group)
    setName(group.name)
    setDescription(group.description || '')
    setColor(group.color || DEFAULT_COLORS[0])
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Manage Groups</h2>
          <button
            onClick={() => {
              resetForm()
              onClose()
            }}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-6 mt-4 rounded-md bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        {/* Form */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingGroup ? 'Edit Group' : 'Create New Group'}
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Project Alpha"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
              <div className="flex gap-2">
                {DEFAULT_COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setColor(c)}
                    className={`w-10 h-10 rounded-lg border-2 ${
                      color === c ? 'border-gray-900' : 'border-gray-300'
                    }`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={editingGroup ? handleUpdate : handleCreate}
                disabled={!name.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {editingGroup ? 'Update' : 'Create'}
              </button>
              {editingGroup && (
                <button
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Groups List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Existing Groups</h3>
          {groups.length === 0 ? (
            <p className="text-sm text-gray-500">No groups yet. Create one above!</p>
          ) : (
            <div className="space-y-2">
              {groups.map((group) => (
                <div
                  key={group.id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: group.color || '#3B82F6' }}
                    />
                    <div>
                      <p className="font-medium text-gray-900">{group.name}</p>
                      {group.description && (
                        <p className="text-sm text-gray-500">{group.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => startEdit(group)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(group.id)}
                      className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


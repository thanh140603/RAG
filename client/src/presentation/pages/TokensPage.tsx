import { useState, useEffect } from 'react'
import { TokenApi, TokenUsageSummary, TokenUsage, SetLimitsRequest } from '../../infrastructure/api/TokenApi'
import { ConfirmModal } from '../components/ConfirmModal'

const tokenApi = new TokenApi()

export const TokensPage = () => {
  const [summary, setSummary] = useState<TokenUsageSummary[]>([])
  const [usage, setUsage] = useState<TokenUsage[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingProvider, setEditingProvider] = useState<string | null>(null)
  const [dailyLimit, setDailyLimit] = useState<string>('')
  const [monthlyLimit, setMonthlyLimit] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (selectedProvider) {
      fetchUsage(selectedProvider)
    }
  }, [selectedProvider])

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const summaryData = await tokenApi.getSummary()
      setSummary(summaryData)
      if (summaryData.length > 0 && !selectedProvider) {
        setSelectedProvider(summaryData[0].provider)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load token usage')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchUsage = async (provider: string) => {
    try {
      const usageData = await tokenApi.getUsage(provider, 30)
      setUsage(usageData)
    } catch (err: any) {
      console.error('Failed to load usage history:', err)
    }
  }

  const handleEditLimits = (provider: string, currentDaily?: number | null, currentMonthly?: number | null) => {
    setEditingProvider(provider)
    setDailyLimit(currentDaily?.toString() || '')
    setMonthlyLimit(currentMonthly?.toString() || '')
  }

  const handleSaveLimits = async () => {
    if (!editingProvider) return

    setIsSaving(true)
    try {
      const limits: SetLimitsRequest = {
        daily_limit: dailyLimit ? parseInt(dailyLimit) : null,
        monthly_limit: monthlyLimit ? parseInt(monthlyLimit) : null,
      }
      await tokenApi.setLimits(editingProvider, limits)
      setEditingProvider(null)
      setDailyLimit('')
      setMonthlyLimit('')
      await fetchData() // Refresh summary
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update limits')
    } finally {
      setIsSaving(false)
    }
  }

  const getPercentageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 70) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-600'
    if (percentage >= 70) return 'bg-yellow-600'
    return 'bg-green-600'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading token usage...</p>
        </div>
      </div>
    )
  }

  if (error && summary.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Show empty state if no providers have usage data yet
  if (!isLoading && summary.length === 0 && !error) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">API Token Usage</h1>
            <p className="text-gray-600 mt-2">Monitor and manage token usage for external APIs</p>
          </div>
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <svg
              className="mx-auto h-16 w-16 text-gray-400 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Token Usage Data Yet</h3>
            <p className="text-gray-600 mb-6">
              Token usage tracking will begin automatically when you use the chatbot or web search features.
            </p>
            <p className="text-sm text-gray-500">
              Try sending a message in the Q&A Chatbot to generate usage data for Groq and Tavily.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">API Token Usage</h1>
          <p className="text-gray-600 mt-2">Monitor and manage token usage for external APIs</p>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {summary.map((item) => (
            <div key={item.provider} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 capitalize">{item.provider}</h3>
                <button
                  onClick={() => handleEditLimits(item.provider, item.daily_limit, item.monthly_limit)}
                  className="text-blue-600 hover:text-blue-700 text-sm"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </div>

              {/* Daily Usage */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Today</span>
                  <span className="font-medium">
                    {item.today_tokens.toLocaleString()} / {item.daily_limit ? item.daily_limit.toLocaleString() : '∞'} tokens
                  </span>
                </div>
                {item.daily_limit && (
                  <>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressBarColor(item.daily_percentage)}`}
                        style={{ width: `${Math.min(item.daily_percentage, 100)}%` }}
                      ></div>
                    </div>
                    <p className={`text-xs mt-1 ${getPercentageColor(item.daily_percentage)}`}>
                      {item.daily_percentage.toFixed(1)}% used
                    </p>
                  </>
                )}
                <p className="text-xs text-gray-500 mt-1">{item.today_requests} requests</p>
              </div>

              {/* Monthly Usage */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">This Month</span>
                  <span className="font-medium">
                    {item.month_tokens.toLocaleString()} / {item.monthly_limit ? item.monthly_limit.toLocaleString() : '∞'} tokens
                  </span>
                </div>
                {item.monthly_limit && (
                  <>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressBarColor(item.monthly_percentage)}`}
                        style={{ width: `${Math.min(item.monthly_percentage, 100)}%` }}
                      ></div>
                    </div>
                    <p className={`text-xs mt-1 ${getPercentageColor(item.monthly_percentage)}`}>
                      {item.monthly_percentage.toFixed(1)}% used
                    </p>
                  </>
                )}
                <p className="text-xs text-gray-500 mt-1">{item.month_requests} requests</p>
              </div>
            </div>
          ))}
        </div>

        {/* Usage History */}
        {selectedProvider && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Usage History - {selectedProvider.charAt(0).toUpperCase() + selectedProvider.slice(1)}
                </h2>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {summary.map((item) => (
                    <option key={item.provider} value={item.provider}>
                      {item.provider.charAt(0).toUpperCase() + item.provider.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens Used</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {usage.map((item) => (
                    <tr key={item.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(item.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.tokens_used.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.requests_count}
                      </td>
                    </tr>
                  ))}
                  {usage.length === 0 && (
                    <tr>
                      <td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">
                        No usage data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Edit Limits Modal */}
        {editingProvider && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setEditingProvider(null)}></div>
            <div className="flex min-h-full items-center justify-center p-4">
              <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Set Limits - {editingProvider.charAt(0).toUpperCase() + editingProvider.slice(1)}
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Daily Limit</label>
                      <input
                        type="number"
                        value={dailyLimit}
                        onChange={(e) => setDailyLimit(e.target.value)}
                        placeholder="No limit"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Limit</label>
                      <input
                        type="number"
                        value={monthlyLimit}
                        onChange={(e) => setMonthlyLimit(e.target.value)}
                        placeholder="No limit"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      onClick={() => setEditingProvider(null)}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                      disabled={isSaving}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveLimits}
                      disabled={isSaving}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {isSaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


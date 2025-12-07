import { apiClient } from './apiClient'

export interface TokenUsageSummary {
  provider: string
  today_tokens: number
  today_requests: number
  month_tokens: number
  month_requests: number
  daily_limit: number | null
  monthly_limit: number | null
  daily_percentage: number
  monthly_percentage: number
}

export interface TokenUsage {
  id: string
  provider: string
  date: string
  tokens_used: number
  requests_count: number
  daily_limit: number | null
  monthly_limit: number | null
  metadata: Record<string, any>
}

export interface SetLimitsRequest {
  daily_limit?: number | null
  monthly_limit?: number | null
}

export class TokenApi {
  async getSummary(): Promise<TokenUsageSummary[]> {
    const response = await apiClient.get<TokenUsageSummary[]>('/api/tokens/summary')
    return response.data
  }

  async getUsage(provider?: string, days: number = 30): Promise<TokenUsage[]> {
    const params = new URLSearchParams()
    if (provider) params.append('provider', provider)
    params.append('days', days.toString())
    
    const response = await apiClient.get<TokenUsage[]>(`/api/tokens/usage?${params.toString()}`)
    return response.data
  }

  async setLimits(provider: string, limits: SetLimitsRequest): Promise<{ message: string; provider: string }> {
    const response = await apiClient.post<{ message: string; provider: string }>(
      `/api/tokens/limits/${provider}`,
      limits
    )
    return response.data
  }
}


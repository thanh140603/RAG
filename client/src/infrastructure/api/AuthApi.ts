import { apiClient } from './apiClient'
import { LoginRequest, LoginResponse } from '../../domain/entities/Auth'
import { User } from '../../domain/entities/User'

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export class AuthApi {
  async login(request: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/login', request)
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me')
    return response.data
  }

  async logout(): Promise<void> {
    // JWT tokens are stateless, no need to call backend
    // Just clear token from localStorage (handled in AuthService)
  }
}

export const authApi = new AuthApi()


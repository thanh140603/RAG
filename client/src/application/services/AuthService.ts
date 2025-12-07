import { AuthApi } from '../../infrastructure/api/AuthApi'
import { LoginRequest, LoginResponse } from '../../domain/entities/Auth'
import { User } from '../../domain/entities/User'

export class AuthService {
  constructor(private authApi: AuthApi) {}

  async login(request: LoginRequest): Promise<LoginResponse> {
    const tokenResponse = await this.authApi.login(request)
    // Store token
    localStorage.setItem('auth_token', tokenResponse.access_token)
    
    // Get user info after login
    const user = await this.getCurrentUser()
    
    return {
      access_token: tokenResponse.access_token,
      token_type: tokenResponse.token_type,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
      },
    }
  }

  async getCurrentUser(): Promise<User> {
    return await this.authApi.getCurrentUser()
  }

  async logout(): Promise<void> {
    try {
      await this.authApi.logout()
    } finally {
      localStorage.removeItem('auth_token')
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token')
  }
}


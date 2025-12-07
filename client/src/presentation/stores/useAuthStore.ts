import { create } from 'zustand'
import { User } from '../../domain/entities/User'
import { AuthService } from '../../application/services/AuthService'
import { authApi } from '../../infrastructure/api/AuthApi'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setUser: (user: User | null) => void
  setError: (error: string | null) => void
}

const authService = new AuthService(authApi)

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('auth_token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authService.login({ email, password })
      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false,
      })
      throw error
    }
  },

  logout: async () => {
    try {
      await authService.logout()
    } finally {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      })
    }
  },

  checkAuth: async () => {
    if (!get().token) {
      set({ isAuthenticated: false })
      return
    }

    set({ isLoading: true })
    try {
      const user = await authService.getCurrentUser()
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      })
    }
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setError: (error) => set({ error }),
}))


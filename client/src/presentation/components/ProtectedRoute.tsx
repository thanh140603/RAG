import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/useAuthStore'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

export const ProtectedRoute = ({ children, requireAdmin = false }: ProtectedRouteProps) => {
  const { isAuthenticated, token, checkAuth, isLoading, user } = useAuthStore()

  useEffect(() => {
    if (token && !isAuthenticated) {
      checkAuth()
    }
  }, [token, isAuthenticated, checkAuth])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/upload" replace />
  }

  return <>{children}</>
}


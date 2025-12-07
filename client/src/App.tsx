import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from './presentation/stores/useAuthStore'
import { ProtectedRoute } from './presentation/components/ProtectedRoute'
import { MainLayout } from './presentation/layouts/MainLayout'
import { LoginPage } from './presentation/pages/LoginPage'
import { UploadPage } from './presentation/pages/UploadPage'
import { ChatPage } from './presentation/pages/ChatPage'
import { TokensPage } from './presentation/pages/TokensPage'

function App() {
  const { checkAuth, token } = useAuthStore()

  useEffect(() => {
    if (token) {
      checkAuth()
    }
  }, [token, checkAuth])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <MainLayout>
                <UploadPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ChatPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tokens"
          element={
            <ProtectedRoute requireAdmin>
              <MainLayout>
                <TokensPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

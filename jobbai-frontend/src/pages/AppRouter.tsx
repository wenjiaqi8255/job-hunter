import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import HomePage from './HomePage'
import LoginPage from './LoginPage'
import AuthCallbackPage from './AuthCallbackPage'
import JobDetailPage from './JobDetailPage'
import ProfilePage from './ProfilePage'
import ApplicationsPage from './ApplicationsPage'
import DebugSessionPage from './DebugSessionPage'

function AppRouter() {
  const { initialize, isLoading } = useAuthStore()

  // 初始化认证状态
  useEffect(() => {
    initialize()
  }, [initialize])

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route path="/sessions/:sessionId/jobs/:id" element={<JobDetailPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/debug-session" element={<DebugSessionPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
      </Routes>
    </Router>
  )
}

export default AppRouter

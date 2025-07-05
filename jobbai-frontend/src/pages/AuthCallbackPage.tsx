import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

function AuthCallbackPage() {
  const navigate = useNavigate()
  const { isAuthenticated, error } = useAuthStore()

  useEffect(() => {
    console.log('[AuthCallback] Page loaded - letting Supabase.js handle authentication')
    console.log('[AuthCallback] Current URL:', window.location.href)
    
    // 什么都不做，让Supabase.js自动处理
    // detectSessionInUrl: true 会自动处理 #access_token= 或 ?code= 
    // onAuthStateChange 会在 authStore 中监听状态变化
  }, [])

  // 监听认证状态，一旦成功立即跳转
  useEffect(() => {
    if (isAuthenticated) {
      console.log('[AuthCallback] Authentication successful, redirecting to home')
      navigate('/', { replace: true })
    } else if (error) {
      console.log('[AuthCallback] Authentication failed, redirecting to login')
      navigate('/login', { replace: true })
    }
  }, [isAuthenticated, error, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">正在处理登录...</p>
        <p className="mt-2 text-sm text-gray-500">
          等待认证完成...
        </p>
      </div>
    </div>
  )
}

export default AuthCallbackPage

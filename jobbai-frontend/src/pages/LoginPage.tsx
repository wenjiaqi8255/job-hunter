import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import PageLayout from '../components/PageLayout'
import LoadingSpinner from '../components/LoadingSpinner'

function LoginPage() {
  const { signInWithGoogle, isAuthenticated, isLoading, error } = useAuthStore()
  const navigate = useNavigate()

  // 如果已经登录，重定向到主页
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  return (
    <PageLayout>
      <div className="flex items-center justify-center min-h-[calc(100vh-112px)] px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-border p-6 md:p-8">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-textPrimary">Login to JobbAI</h2>
              <p className="text-textSecondary mt-2">
                Sign in with your Google account to continue.
              </p>
            </div>
            
            {error && (
              <div className="bg-danger/10 text-danger text-sm p-3 rounded-lg mb-4 text-center">
                {error}
              </div>
            )}
            
            <button
              onClick={signInWithGoogle}
              disabled={isLoading}
              className="w-full flex justify-center items-center py-3 px-4 bg-primary text-textPrimary text-sm font-bold rounded-lg hover:bg-primaryHover disabled:opacity-50"
            >
              {isLoading ? (
                <LoadingSpinner />
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Sign In with Google
                </>
              )}
            </button>
            
            <div className="text-center mt-6">
              <p className="text-xs text-textSecondary">
                By signing in, you agree to our Terms of Service.
              </p>
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}

export default LoginPage

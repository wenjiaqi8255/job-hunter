import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useI18n } from '../hooks/useI18n'
import MainPageLayout from '../components/MainPageLayout'
import Sidebar from '../components/Sidebar'
import MainContent from '../components/MainContent'
import ProfilePreview from '../components/ProfilePreview'
import JobList from '../components/JobList'

function HomePage() {
  const { user, isAuthenticated, signOut } = useAuthStore()
  const { t } = useI18n()
  const navigate = useNavigate()

  // 如果未登录，重定向到登录页
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  if (!isAuthenticated) {
    return null // 重定向中
  }

  return (
    <MainPageLayout>
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 主内容区域 */}
      <MainContent>
        {/* 用户信息快速显示 */}
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {t('welcome_back')}, {user?.user_metadata?.name || user?.email}
                </p>
                <p className="text-xs text-gray-500">
                  {t('user_id')}: {user?.id}
                </p>
              </div>
            </div>
            <button
              onClick={signOut}
              className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700"
            >
              {t('logout')}
            </button>
          </div>
        </div>

        {/* 个人资料预览 */}
        <ProfilePreview />
        
        {/* 工作列表 */}
        <JobList showMatchResults={true} />
      </MainContent>
    </MainPageLayout>
  )
}

export default HomePage

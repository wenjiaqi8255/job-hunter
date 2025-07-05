import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useUserStore } from '../stores/userStore'
import { useI18n } from '../hooks/useI18n'
import LoadingSpinner from '../components/LoadingSpinner'
import PageLayout from '../components/PageLayout'

function ProfilePage() {
  const { user, isAuthenticated } = useAuthStore()
  const { profile, loading, error, fetchProfile, updateProfile } = useUserStore()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    cv_text: '',
    preferences_text: ''
  })

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    
    fetchProfile()
  }, [isAuthenticated, navigate, fetchProfile])

  useEffect(() => {
    if (profile) {
      setFormData({
        cv_text: profile.cv_text || '',
        preferences_text: profile.preferences_text || ''
      })
    }
  }, [profile])

  const handleSave = async () => {
    try {
      await updateProfile(formData)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update profile:', error)
    }
  }

  const handleCancel = () => {
    setFormData({
      cv_text: profile?.cv_text || '',
      preferences_text: profile?.preferences_text || ''
    })
    setIsEditing(false)
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <PageLayout>
      {/* 主内容 */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('personal_profile')}</h1>
          <p className="mt-2 text-gray-600">{t('manage_info')}</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-8">
            {/* 用户信息 */}
            <div className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">用户信息</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    姓名
                  </label>
                  <div className="text-gray-900">
                    {user?.user_metadata?.name || user?.user_metadata?.full_name || '未设置'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    邮箱
                  </label>
                  <div className="text-gray-900">{user?.email}</div>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-8">
                <LoadingSpinner />
                <span className="ml-3 text-gray-600">加载个人资料中...</span>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700">加载个人资料时出错: {error}</p>
              </div>
            ) : (
              <>
                {/* CV编辑区域 */}
                <div className="mb-8">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      <i className="fas fa-file-alt text-gray-600 mr-2"></i>
                      简历内容
                    </h3>
                    {!isEditing && (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                      >
                        <i className="fas fa-edit mr-2"></i>
                        编辑
                      </button>
                    )}
                  </div>
                  
                  {isEditing ? (
                    <div>
                      <textarea
                        value={formData.cv_text}
                        onChange={(e) => setFormData({...formData, cv_text: e.target.value})}
                        rows={10}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="请输入您的简历内容..."
                      />
                    </div>
                  ) : (
                    <div className="border border-gray-300 rounded-md p-4 bg-gray-50 min-h-[200px]">
                      {profile?.cv_text ? (
                        <div className="text-gray-700 whitespace-pre-wrap">
                          {profile.cv_text}
                        </div>
                      ) : (
                        <div className="text-gray-500 italic">
                          还没有上传简历。点击"编辑"按钮来添加您的简历内容。
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* 偏好设置编辑区域 */}
                <div className="mb-8">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    <i className="fas fa-heart text-red-600 mr-2"></i>
                    工作偏好
                  </h3>
                  
                  {isEditing ? (
                    <div>
                      <textarea
                        value={formData.preferences_text}
                        onChange={(e) => setFormData({...formData, preferences_text: e.target.value})}
                        rows={6}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="请输入您的工作偏好，例如：期望薪资、工作地点、工作类型等..."
                      />
                    </div>
                  ) : (
                    <div className="border border-gray-300 rounded-md p-4 bg-gray-50 min-h-[120px]">
                      {profile?.preferences_text ? (
                        <div className="text-gray-700 whitespace-pre-wrap">
                          {profile.preferences_text}
                        </div>
                      ) : (
                        <div className="text-gray-500 italic">
                          还没有设置工作偏好。点击"编辑"按钮来添加您的偏好。
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* 编辑模式按钮 */}
                {isEditing && (
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={handleCancel}
                      className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md border border-gray-300 hover:bg-gray-200"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleSave}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                    >
                      保存
                    </button>
                  </div>
                )}

                {/* 个人资料状态 */}
                <div className="mt-8 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    <i className="fas fa-info-circle text-blue-600 mr-2"></i>
                    个人资料状态
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-500 mb-1">创建时间</div>
                      <div className="text-gray-900">
                        {profile?.created_at ? new Date(profile.created_at).toLocaleString() : '未知'}
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-500 mb-1">最后更新</div>
                      <div className="text-gray-900">
                        {profile?.updated_at ? new Date(profile.updated_at).toLocaleString() : '未知'}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </PageLayout>
  )
}

export default ProfilePage

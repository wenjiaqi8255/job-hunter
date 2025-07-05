import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useUserStore } from '../stores/userStore'
import AIMatchButton from './AIMatchButton'
import LoadingSpinner from './LoadingSpinner'

function ProfilePreview() {
  const { isAuthenticated } = useAuthStore()
  const { profile, loading: userLoading, error: userError, fetchProfile } = useUserStore()

  // 获取用户个人资料
  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile()
    }
  }, [isAuthenticated, fetchProfile])

  if (!isAuthenticated) {
    // 访客用户显示
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-medium text-gray-900">
            Review Your Profile & Start Match
          </h5>
        </div>
        
        <div className="p-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h5 className="text-lg font-medium text-blue-900 mb-2">
              Welcome, Guest!
            </h5>
            <p className="text-blue-700 mb-3">
              You are viewing this page as a guest. You can browse all available jobs below.
            </p>
            <hr className="border-blue-200 my-3" />
            <p className="text-blue-700 mb-0">
              To get personalized job matches, save applications, and use other features, please{' '}
              <Link to="/login" className="text-blue-800 underline hover:text-blue-900">
                log in or create an account
              </Link>.
            </p>
          </div>
        </div>
        
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
          <Link 
            to="/login" 
            className="bg-blue-600 text-white px-6 py-2 rounded-md text-lg font-medium hover:bg-blue-700 inline-flex items-center"
          >
            <i className="fas fa-sign-in-alt mr-2"></i>
            Log In to Find Matches
          </Link>
        </div>
      </div>
    )
  }

  // 认证用户显示
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div className="border-b border-gray-200 px-6 py-4">
        <h5 className="text-lg font-medium text-gray-900">
          Review Your Profile & Start Match
        </h5>
      </div>
      
      <div className="p-6">
        {userLoading ? (
          <div className="flex justify-center items-center py-8">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Loading profile...</span>
          </div>
        ) : userError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">Error loading profile: {userError}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CV 预览 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <strong>Your Current CV:</strong>
              </label>
              <div className="border border-gray-300 rounded-md p-4 bg-gray-50 max-h-48 overflow-y-auto">
                {profile?.cv_text ? (
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {profile.cv_text.substring(0, 200)}
                    {profile.cv_text.length > 200 && '...'}
                  </div>
                ) : (
                  <small className="text-gray-500">
                    No CV uploaded yet. Please upload your CV to get personalized matches.
                  </small>
                )}
              </div>
              <div className="mt-2">
                <Link 
                  to="/profile"
                  className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm border border-gray-300 hover:bg-gray-200"
                >
                  <i className="fas fa-edit mr-1"></i>
                  Edit CV in Profile
                </Link>
              </div>
            </div>

            {/* 偏好设置预览 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <strong>Your Preferences:</strong>
              </label>
              <div className="border border-gray-300 rounded-md p-4 bg-gray-50 max-h-40 overflow-y-auto">
                {profile?.preferences_text ? (
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {profile.preferences_text.substring(0, 150)}
                    {profile.preferences_text.length > 150 && '...'}
                  </div>
                ) : (
                  <small className="text-gray-500">
                    No preferences set yet. Set your preferences to get better matches.
                  </small>
                )}
              </div>
              <div className="mt-2">
                <Link 
                  to="/profile"
                  className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm border border-gray-300 hover:bg-gray-200"
                >
                  <i className="fas fa-edit mr-1"></i>
                  Edit Preferences in Profile
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
        <AIMatchButton 
          onMatchComplete={() => {
            console.log('AI匹配完成')
          }}
        />
      </div>
    </div>
  )
}

export default ProfilePreview

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
    } else {
      fetchProfile()
    }
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
    await updateProfile(formData)
    setIsEditing(false)
  }

  const handleCancel = () => {
    if (profile) {
      setFormData({
        cv_text: profile.cv_text || '',
        preferences_text: profile.preferences_text || ''
      })
    }
    setIsEditing(false)
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <PageLayout className="max-w-4xl mx-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">{t('personal_profile')}</h1>
        <p className="mt-1 text-textSecondary">{t('manage_info_and_cv')}</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-6 text-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="p-6 text-center text-danger">
            <p>{error}</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {/* User Info Section */}
            <div className="p-6">
              <h3 className="text-lg font-bold text-textPrimary mb-4">User Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="font-medium text-textSecondary">Name</label>
                  <p className="text-textPrimary mt-1">{user?.user_metadata?.name || 'Not set'}</p>
                </div>
                <div>
                  <label className="font-medium text-textSecondary">Email</label>
                  <p className="text-textPrimary mt-1">{user?.email}</p>
                </div>
              </div>
            </div>

            {/* CV Section */}
            <div className="p-6">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-bold text-textPrimary">📄 Your CV</h3>
                {!isEditing && (
                  <button onClick={() => setIsEditing(true)} className="bg-primaryLight text-textPrimary text-sm font-bold py-2 px-4 rounded-lg">
                    Edit
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={formData.cv_text}
                  onChange={(e) => setFormData({ ...formData, cv_text: e.target.value })}
                  rows={12}
                  className="w-full border-border rounded-md p-2 text-sm"
                  placeholder="Paste your CV here..."
                />
              ) : (
                <div className="text-sm text-textSecondary whitespace-pre-wrap p-4 bg-gray-50 rounded-lg min-h-[150px]">
                  {profile?.cv_text || 'No CV provided.'}
                </div>
              )}
            </div>

            {/* Preferences Section */}
            <div className="p-6">
              <h3 className="text-lg font-bold text-textPrimary mb-2">❤️ Job Preferences</h3>
              {isEditing ? (
                <textarea
                  value={formData.preferences_text}
                  onChange={(e) => setFormData({ ...formData, preferences_text: e.target.value })}
                  rows={6}
                  className="w-full border-border rounded-md p-2 text-sm"
                  placeholder="e.g., Desired salary, locations, remote work..."
                />
              ) : (
                <div className="text-sm text-textSecondary whitespace-pre-wrap p-4 bg-gray-50 rounded-lg min-h-[100px]">
                  {profile?.preferences_text || 'No preferences set.'}
                </div>
              )}
            </div>
            
            {isEditing && (
              <div className="p-6 flex justify-end gap-3 bg-gray-50">
                <button onClick={handleCancel} className="bg-gray-200 text-textPrimary text-sm font-bold py-2 px-4 rounded-lg">
                  Cancel
                </button>
                <button onClick={handleSave} className="bg-primary text-textPrimary text-sm font-bold py-2 px-4 rounded-lg hover:bg-primaryHover">
                  Save Changes
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  )
}

export default ProfilePage

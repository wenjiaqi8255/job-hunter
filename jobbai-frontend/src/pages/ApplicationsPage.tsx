import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useI18n } from '../hooks/useI18n'
import { jobsApi } from '../services/api'
import type { SavedJob } from '../types'
import PageLayout from '../components/PageLayout'
import LoadingSpinner from '../components/LoadingSpinner'

// 状态选项映射（与AuthenticatedJobActions保持一致）
const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'bookmarked', label: 'Bookmarked' },
  { value: 'applied', label: 'Applied' },
  { value: 'interviewing', label: 'Interviewing' },
  { value: 'offer_received', label: 'Offer Received' },
  { value: 'rejected', label: 'Rejected' },
]

const statusClasses: { [key: string]: string } = {
  applied: 'bg-status-applied-bg text-status-applied-text',
  interviewing: 'bg-status-interviewing-bg text-status-interviewing-text',
  offer: 'bg-status-offer-bg text-status-offer-text',
  rejected: 'bg-status-rejected-bg text-status-rejected-text',
  bookmarked: 'bg-purple-100 text-purple-800', // Example custom one
  not_applied: 'bg-status-not_applied-bg text-status-not_applied-text',
}

function ApplicationsPage() {
  const { isAuthenticated } = useAuthStore()
  const { t } = useI18n()
  const navigate = useNavigate()
  
  // 数据状态
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentFilter, setCurrentFilter] = useState<string>('all')

  // 如果未登录，重定向到登录页
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  // 加载保存的工作数据
  useEffect(() => {
    if (isAuthenticated) {
      loadSavedJobs()
    }
  }, [isAuthenticated])

  const loadSavedJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await jobsApi.getSavedJobs()
      
      if (response.success && response.data) {
        setSavedJobs(response.data.jobs || [])
      } else {
        setError(response.error || 'Failed to fetch saved jobs.')
      }
    } catch (err) {
      console.error('加载保存的工作失败:', err)
      setError('An error occurred while fetching data.')
    } finally {
      setLoading(false)
    }
  }

  // 获取状态统计
  const getStatusCounts = () => {
    const counts: Record<string, number> = {
      all: savedJobs.length,
      not_applied: 0,
      bookmarked: 0,
      applied: 0,
      interviewing: 0,
      offer_received: 0,
      rejected: 0,
    }

    savedJobs.forEach(job => {
      counts[job.status] = (counts[job.status] || 0) + 1
    })

    return counts
  }

  // 过滤工作
  const getFilteredJobs = () => {
    if (currentFilter === 'all') {
      return savedJobs
    }
    return savedJobs.filter(job => job.status === currentFilter)
  }

  // 获取状态标签
  const getStatusLabel = (status: string) => {
    const option = STATUS_OPTIONS.find(opt => opt.value === status)
    return option ? option.label : status
  }

  // 获取状态样式
  const getStatusBadgeClass = (status: string) => {
    const baseClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
    
    switch (status) {
      case 'applied':
        return `${baseClass} bg-blue-100 text-blue-800`
      case 'interviewing':
        return `${baseClass} bg-yellow-100 text-yellow-800`
      case 'offer_received':
        return `${baseClass} bg-green-100 text-green-800`
      case 'rejected':
        return `${baseClass} bg-red-100 text-red-800`
      case 'bookmarked':
        return `${baseClass} bg-purple-100 text-purple-800`
      case 'withdrawn':
        return `${baseClass} bg-gray-100 text-gray-800`
      default:
        return `${baseClass} bg-gray-100 text-gray-800`
    }
  }

  if (!isAuthenticated) {
    return null // 重定向中
  }

  const statusCounts = getStatusCounts()
  const filteredJobs = getFilteredJobs()

  return (
    <PageLayout className="max-w-7xl mx-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">{t('my_applications')}</h1>
        <p className="mt-1 text-textSecondary">Track and manage your job applications.</p>
      </div>

      <div className="mb-6 border-b border-border">
        <nav className="-mb-px flex space-x-6">
          {STATUS_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setCurrentFilter(option.value)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                currentFilter === option.value
                  ? 'border-primary text-primary'
                  : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'
              }`}
            >
              {option.label}
              <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                {statusCounts[option.value] || 0}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {loading && (
        <div className="text-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-danger">{error}</p>
          <button onClick={loadSavedJobs} className="mt-4 bg-primary text-textPrimary px-4 py-2 rounded-lg text-sm font-bold">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredJobs.length > 0 ? filteredJobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow-sm border border-border p-5 flex flex-col justify-between">
              <div>
                <div className="mb-3">
                  <span className={`px-2 py-1 rounded-md text-xs font-medium ${statusClasses[job.status] || statusClasses.not_applied}`}>
                    {job.status}
                  </span>
                </div>
                <h3 className="font-bold text-textPrimary hover:text-primary cursor-pointer" onClick={() => navigate(`/jobs/${job.original_job_id}`)}>
                  {job.job_title}
                </h3>
                <p className="text-sm text-textSecondary mt-1">{job.company_name}</p>
                {job.location && <p className="text-xs text-textSecondary mt-2">📍 {job.location}</p>}
              </div>
              <div className="text-xs text-textSecondary mt-4 pt-3 border-t border-border">
                Updated: {new Date(job.updated_at).toLocaleDateString()}
              </div>
            </div>
          )) : (
            <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg">
              <div className="text-4xl mb-4">🗂️</div>
              <h3 className="text-lg font-bold text-textPrimary mb-2">No Applications Found</h3>
              <p className="text-textSecondary text-sm">
                You haven't saved any applications with this status yet.
              </p>
            </div>
          )}
        </div>
      )}
    </PageLayout>
  )
}

export default ApplicationsPage

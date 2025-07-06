import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useI18n } from '../hooks/useI18n'
import { jobsApi } from '../services/api'
import type { SavedJob } from '../types'
import PageLayout from '../components/PageLayout'

// 状态选项映射（与AuthenticatedJobActions保持一致）
const STATUS_OPTIONS = [
  { value: 'not_applied', label: '未申请' },
  { value: 'bookmarked', label: '已收藏' },
  { value: 'applied', label: '已申请' },
  { value: 'interviewing', label: '面试中' },
  { value: 'offer_received', label: '已获得Offer' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'withdrawn', label: '已撤回' },
]

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
        setError(response.error || '获取保存的工作失败')
      }
    } catch (err) {
      console.error('加载保存的工作失败:', err)
      setError('加载数据失败，请稍后重试')
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
      withdrawn: 0,
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
    <PageLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('my_applications')}</h1>
          <p className="mt-2 text-gray-600">查看和管理您的职位申请记录</p>
        </div>

        {/* 状态筛选标签 */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {/* 全部标签 */}
              <button
                onClick={() => setCurrentFilter('all')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  currentFilter === 'all'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                全部
                <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2.5 rounded-full text-xs">
                  {statusCounts.all}
                </span>
              </button>
              
              {/* 状态标签 */}
              {STATUS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setCurrentFilter(option.value)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    currentFilter === option.value
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {option.label}
                  <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2.5 rounded-full text-xs">
                    {statusCounts[option.value] || 0}
                  </span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* 加载状态 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center px-4 py-2 font-semibold leading-6 text-sm shadow rounded-md text-gray-500 bg-white">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              加载中...
            </div>
          </div>
        )}

        {/* 错误状态 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <i className="fas fa-exclamation-circle text-red-400"></i>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
                <button
                  onClick={loadSavedJobs}
                  className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                >
                  重试
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 工作列表 */}
        {!loading && !error && filteredJobs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredJobs.map((job) => (
              <div key={job.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                <div className="p-6">
                  {/* 工作标题和公司 */}
                  <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      <button
                        onClick={() => navigate(`/jobs/${job.original_job_id}`)}
                        className="hover:text-blue-600 transition-colors"
                      >
                        {job.job_title}
                      </button>
                    </h3>
                    <p className="text-sm text-gray-600">{job.company_name}</p>
                  </div>

                  {/* 状态标签 */}
                  <div className="mb-4">
                    <span className={getStatusBadgeClass(job.status)}>
                      {getStatusLabel(job.status)}
                    </span>
                  </div>

                  {/* 位置和时间 */}
                  <div className="space-y-2 mb-4">
                    {job.location && (
                      <p className="text-sm text-gray-500">
                        <i className="fas fa-map-marker-alt mr-1"></i>
                        {job.location}
                      </p>
                    )}
                    <p className="text-sm text-gray-500">
                      <i className="fas fa-clock mr-1"></i>
                      更新于 {new Date(job.updated_at).toLocaleDateString()}
                    </p>
                  </div>

                  {/* 笔记预览 */}
                  {job.notes && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-md">
                      <p className="text-sm text-gray-700 line-clamp-2">
                        <strong>笔记:</strong> {job.notes}
                      </p>
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex space-x-3">
                    <button
                      onClick={() => navigate(`/jobs/${job.original_job_id}`)}
                      className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                      <i className="fas fa-eye mr-2"></i>
                      查看详情
                    </button>
                    <button
                      onClick={() => navigate(`/jobs/${job.original_job_id}/cover-letter`)}
                      className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
                    >
                      <i className="fas fa-envelope mr-2"></i>
                      生成求职信
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 空状态 */}
        {!loading && !error && filteredJobs.length === 0 && (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
              <svg fill="none" stroke="currentColor" viewBox="0 0 48 48" aria-hidden="true">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.712-3.714M14 40v-4a9.971 9.971 0 01.712-3.714m0 0A9.973 9.973 0 0118 32a9.973 9.973 0 013.288 0.714M30 20a6 6 0 11-12 0 6 6 0 0112 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {currentFilter === 'all' ? '还没有保存的工作' : `没有"${getStatusLabel(currentFilter)}"状态的工作`}
            </h3>
            <p className="text-gray-500 mb-6">
              {currentFilter === 'all' 
                ? '开始寻找工作并保存您感兴趣的职位吧' 
                : '您可以在工作详情页面更改工作状态'
              }
            </p>
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {t('start_matching')}
            </button>
          </div>
        )}
      </div>
    </PageLayout>
  )
}

export default ApplicationsPage

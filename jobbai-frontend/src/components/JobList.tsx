import { useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useJobsStore } from '../stores/jobsStore'
import { useSessionStore } from '../stores/sessionStore'
import JobCard from './JobCard'
import LoadingSpinner from './LoadingSpinner'

interface JobListProps {
  showMatchResults?: boolean
}

function JobList({ showMatchResults = true }: JobListProps) {
  const { isAuthenticated } = useAuthStore()
  const { jobs, loading, error, fetchJobs, fetchMatchedJobs, clearError } = useJobsStore()
  const { currentSession } = useSessionStore()
  const lastAuthState = useRef<boolean | null>(null)
  const isFetching = useRef<boolean>(false)
  
  // 固定数据源为 jobs，移除对 currentJobs 的依赖
  const displayJobs = jobs

  // 根据认证状态获取数据 - 优化：避免重复请求
  useEffect(() => {
    // 如果正在请求中，跳过
    if (isFetching.current) {
      return
    }
    
    // 如果认证状态没有变化且已有数据，跳过
    if (lastAuthState.current === isAuthenticated && jobs.length > 0) {
      return
    }
    
    lastAuthState.current = isAuthenticated
    isFetching.current = true
    
    if (isAuthenticated) {
      // 已认证用户：获取匹配的工作
      fetchMatchedJobs().finally(() => {
        isFetching.current = false
      })
    } else {
      // 未认证用户：获取所有工作
      fetchJobs().finally(() => {
        isFetching.current = false
      })
    }
  }, [isAuthenticated, fetchJobs, fetchMatchedJobs])

  // 手动刷新函数
  const handleRefresh = () => {
    isFetching.current = true
    if (isAuthenticated) {
      fetchMatchedJobs(true).finally(() => {
        isFetching.current = false
      })
    } else {
      fetchJobs().finally(() => {
        isFetching.current = false
      })
    }
  }

  // 加载状态
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
        <span className="ml-3 text-gray-600">加载工作列表中...</span>
      </div>
    )
  }

  // 错误状态
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <i className="fas fa-exclamation-triangle text-red-400"></i>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              加载工作列表失败
            </h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <div className="ml-auto">
            <button
              onClick={clearError}
              className="text-red-400 hover:text-red-600"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleRefresh}
            className="bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // 无数据状态
  if (displayJobs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 mb-4">
          <i className="fas fa-briefcase text-4xl"></i>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          暂无工作机会
        </h3>
        <p className="text-gray-600">
          {currentSession 
            ? '当前会话中暂无匹配的工作' 
            : isAuthenticated 
              ? '暂时没有匹配的工作，请稍后再试' 
              : '请登录以查看个性化推荐'}
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* 匹配结果说明 */}
      {showMatchResults && (
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">
                {currentSession
                  ? `当前会话匹配到 ${displayJobs.length} 个工作机会`
                  : isAuthenticated 
                    ? `为您找到 ${displayJobs.length} 个匹配的工作机会` 
                    : `共找到 ${displayJobs.length} 个工作机会，登录后查看个性化匹配`}
              </p>
              {currentSession && (
                <p className="text-xs text-gray-500 mt-1">
                  会话时间: {new Date(currentSession.matched_at || currentSession.created_at).toLocaleString()}
                </p>
              )}
            </div>
            <button
              onClick={handleRefresh}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              <i className="fas fa-sync-alt mr-1"></i>
              刷新
            </button>
          </div>
        </div>
      )}

      {/* 工作列表 */}
      <div className="space-y-4">
        {displayJobs.map(job => (
          <JobCard 
            key={job.id} 
            job={job} 
          />
        ))}
      </div>

      {/* 加载更多按钮 */}
      <div className="mt-8 text-center">
        <button className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400">
          Load More Jobs
        </button>
      </div>
    </div>
  )
}

export default JobList

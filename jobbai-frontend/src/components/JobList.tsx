import { useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useJobsStore } from '../stores/jobsStore'
import JobCard from './JobCard'
import LoadingSpinner from './LoadingSpinner'

interface JobListProps {
  showMatchResults?: boolean
  sessionId: string | null
}

function JobList({ showMatchResults = true, sessionId }: JobListProps) {
  const { isAuthenticated } = useAuthStore()
  const { 
    jobs, 
    loading, 
    error, 
    fetchJobs, 
    fetchMatchedJobs,
    fetchJobsBySession,
    clearError 
  } = useJobsStore()
  
  const lastSessionId = useRef<string | null>(null)
  
  const displayJobs = jobs

  useEffect(() => {
    if (sessionId) {
      if (sessionId !== lastSessionId.current) {
        fetchJobsBySession(sessionId)
        lastSessionId.current = sessionId
      }
    } else if (isAuthenticated) {
      fetchMatchedJobs()
    } else {
      fetchJobs()
    }
  }, [sessionId, isAuthenticated, fetchJobs, fetchMatchedJobs, fetchJobsBySession])

  // 手动刷新函数
  const handleRefresh = () => {
    if (sessionId) {
      fetchJobsBySession(sessionId)
    } else if (isAuthenticated) {
      fetchMatchedJobs(true)
    } else {
      fetchJobs()
    }
  }

  // 加载状态
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <LoadingSpinner />
        <p className="mt-2 text-sm text-textSecondary">Loading jobs...</p>
      </div>
    )
  }

  // 错误状态
  if (error) {
    return (
      <div className="bg-danger/10 border border-danger/20 rounded-lg p-4 mb-6 text-center">
        <div className="text-danger text-2xl mb-2">😞</div>
        <h3 className="text-sm font-bold text-danger mb-1">Failed to load jobs</h3>
        <p className="text-sm text-danger/80 mb-4">{error}</p>
        <button
          onClick={handleRefresh}
          className="bg-danger text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-danger/80"
        >
          Retry
        </button>
      </div>
    )
  }

  // 无数据状态
  if (displayJobs.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <div className="text-4xl mb-4">🗂️</div>
        <h3 className="text-lg font-bold text-textPrimary mb-2">No Jobs Found</h3>
        <p className="text-textSecondary text-sm">
          {sessionId
            ? 'There are no matched jobs in this session.'
            : isAuthenticated
            ? "We couldn't find any matched jobs for you at the moment."
            : 'Log in to see personalized job recommendations.'}
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* 匹配结果说明 */}
      {showMatchResults && (
        <div className="mb-4">
          <p className="text-sm text-textSecondary">
            {sessionId
              ? `Found ${displayJobs.length} jobs in this session.`
              : isAuthenticated 
                ? `Found ${displayJobs.length} matched jobs for you.` 
                : `Found ${displayJobs.length} jobs. Log in for personalized matches.`}
          </p>
        </div>
      )}

      {/* 工作列表 */}
      <div className="space-y-4">
        {displayJobs.map(job => (
          <JobCard 
            key={job.id} 
            job={job}
            showMatchScore={showMatchResults}
          />
        ))}
      </div>

      {/* 加载更多按钮 */}
      <div className="mt-8 text-center">
        <button className="bg-primary text-textPrimary rounded-full px-6 py-2 text-sm font-bold hover:bg-primaryHover disabled:bg-gray-300">
          Load More Jobs
        </button>
      </div>
    </div>
  )
}

export default JobList

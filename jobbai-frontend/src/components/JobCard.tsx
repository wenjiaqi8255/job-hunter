import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'
import type { Job } from '../types'

interface JobCardProps {
  job: Job
}

function JobCard({ job }: JobCardProps) {
  // 在 JobCard 组件开头添加：
  console.log('=== JobCard 接收数据调试 ===')
  console.log('接收到的job对象:', job)
  console.log('job.title:', job.title)
  console.log('job.company:', job.company)
  console.log('Object.keys(job):', Object.keys(job))

  const { currentSession } = useSessionStore()
  const navigate = useNavigate()
  
  // 处理点击工作详情 - 根据会话信息决定URL格式
  const handleViewDetails = () => {
    // 如果有 currentSession，导航到 /sessions/${sessionId}/jobs/${jobId}
    if (currentSession) {
      navigate(`/sessions/${currentSession.id}/jobs/${job.id}`)
    } else {
      // 否则导航到 /jobs/${jobId}
      navigate(`/jobs/${job.id}`)
    }
  }
  
  // 临时移除saveJob功能，简化组件
  const handleSaveJob = async () => {
    try {
      // TODO: 实现保存工作功能
      console.log('Save job:', job.id)
    } catch (error) {
      console.error('Failed to save job:', error)
    }
  }

  const handleApplyNow = () => {
    if (job.applicationUrl) {
      window.open(job.applicationUrl, '_blank')
    }
  }

  // 获取匹配分数
  const getMatchScore = () => {
    return job.score || 0
  }

  // 获取匹配原因
  const getMatchReason = () => {
    return job.analysis?.reasoning || ''
  }

  // 获取申请建议
  const getApplicationTips = () => {
    return job.application_tips?.specific_advice || ''
  }

  // 获取优势和劣势 - 使用新的数据结构
  const getInsights = () => {
    if (job.analysis?.pros?.length || job.analysis?.cons?.length) {
      return [{
        category: 'Analysis',
        pros: job.analysis.pros || [],
        cons: job.analysis.cons || []
      }]
    }
    
    return []
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* 工作标题和匹配分数 */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h5 className="text-lg font-medium text-gray-900 mb-1">
              <button 
                onClick={handleViewDetails}
                className="text-blue-600 hover:text-blue-800 no-underline text-left"
              >
                {job.title}
              </button>
            </h5>
            <small className="text-gray-500">{job.company}</small>
          </div>
          {getMatchScore() > 0 && (
            <div className="text-center ml-4">
              <h2 className="text-2xl font-bold text-blue-600 mb-0">
                {getMatchScore()}%
              </h2>
              <small className="text-gray-500">Match Score</small>
            </div>
          )}
        </div>

        {/* 工作基本信息 */}
        <div className="mb-3">
          <div className="text-sm text-gray-600 space-x-4">
            <span><i className="fas fa-briefcase mr-1"></i> {job.level}</span>
            <span><i className="fas fa-map-marker-alt mr-1"></i> {job.location}</span>
            <span><i className="fas fa-industry mr-1"></i> {job.industry}</span>
            <span><i className="fas fa-clock mr-1"></i> {job.flexibility}</span>
            {job.salaryRange && (
              <span><i className="fas fa-dollar-sign mr-1"></i> {job.salaryRange}</span>
            )}
          </div>
        </div>

        {/* 匹配原因 */}
        {getMatchReason() && (
          <p className="text-sm text-gray-700 mb-3">
            {getMatchReason()}
          </p>
        )}

        {/* 申请建议 */}
        {getApplicationTips() && (
          <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-md">
            <h6 className="text-sm font-medium text-green-800 mb-2">
              <i className="fas fa-lightbulb mr-2"></i>
              Application Tips
            </h6>
            <p className="text-sm text-green-700">
              {getApplicationTips()}
            </p>
          </div>
        )}

        {/* 关键洞察 */}
        {getInsights().length > 0 && (
          <div className="mb-4">
            <div className="border border-gray-200 rounded-md">
              <button className="w-full px-4 py-2 text-left text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-t-md">
                <i className="fas fa-lightbulb mr-2"></i>
                Key Insights
              </button>
              <div className="p-4 bg-white">
                {getInsights().map((insight, index) => (
                  <div key={index} className="mb-3 last:mb-0">
                    <h6 className="text-sm font-medium text-gray-700 mb-2">{insight.category}</h6>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {insight.pros && insight.pros.length > 0 && (
                        <div>
                          <h6 className="text-sm font-medium text-green-600 mb-1">
                            <i className="fas fa-thumbs-up mr-1"></i>Pros
                          </h6>
                          <ul className="text-sm text-green-700 space-y-1">
                            {insight.pros.map((pro, i) => (
                              <li key={i} className="flex items-start">
                                <i className="fas fa-check-circle text-green-500 mr-2 mt-1 flex-shrink-0"></i>
                                <span>{pro}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {insight.cons && insight.cons.length > 0 && (
                        <div>
                          <h6 className="text-sm font-medium text-red-600 mb-1">
                            <i className="fas fa-thumbs-down mr-1"></i>Cons
                          </h6>
                          <ul className="text-sm text-red-700 space-y-1">
                            {insight.cons.map((con, i) => (
                              <li key={i} className="flex items-start">
                                <i className="fas fa-times-circle text-red-500 mr-2 mt-1 flex-shrink-0"></i>
                                <span>{con}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-between items-center pt-3 border-t border-gray-200">
          <button
            onClick={handleViewDetails}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            View Details
          </button>
          
          <div className="flex space-x-2">
            <button 
              onClick={handleSaveJob}
              className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm border border-gray-300 hover:bg-gray-200"
            >
              <i className="fas fa-heart mr-1"></i>
              Save Job
            </button>
            <button 
              onClick={handleApplyNow}
              className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
            >
              <i className="fas fa-external-link-alt mr-1"></i>
              Apply Now
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JobCard

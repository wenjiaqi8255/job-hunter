/**
 * 匹配历史页面
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求实现
 * 演示如何使用新的JSONB结构化数据
 */

import React, { useState } from 'react'
import { MatchHistoryList } from '../components/MatchHistoryList'
import { JobMatchCard } from '../components/JobMatchCard'
import { useMatchHistory } from '../hooks/useMatchHistory'
import type { MatchedJob } from '../types'

const MatchHistoryPage: React.FC = () => {
  const [selectedJob, setSelectedJob] = useState<MatchedJob | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  
  const {
    latestJobs,
    loading,
    error,
    triggerNewMatch,
    updateJobStatus,
    getJobDetails,
    clearError,
    refresh
  } = useMatchHistory()

  const handleJobDetails = async (jobId: string) => {
    const job = await getJobDetails(jobId)
    if (job) {
      setSelectedJob(job)
      setShowDetails(true)
    }
  }

  const handleTriggerMatch = async () => {
    await triggerNewMatch()
  }

  const handleJobStatusUpdate = async (jobId: string, status: string) => {
    await updateJobStatus(jobId, { status: status as any })
  }

  return (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-12">
          {/* 页面标题 */}
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h1 className="h2">
              <i className="fas fa-history me-2"></i>
              Match History
            </h1>
            <div className="btn-group">
              <button 
                className="btn btn-primary"
                onClick={handleTriggerMatch}
                disabled={loading}
              >
                <i className="fas fa-magic me-1"></i>
                {loading ? 'Matching...' : 'New Match'}
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={refresh}
                disabled={loading}
              >
                <i className="fas fa-refresh me-1"></i>
                Refresh
              </button>
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              <i className="fas fa-exclamation-triangle me-2"></i>
              {error}
              <button 
                type="button" 
                className="btn-close" 
                onClick={clearError}
                aria-label="Close"
              ></button>
            </div>
          )}

          {/* 最新匹配结果 */}
          {latestJobs.length > 0 && (
            <div className="mb-5">
              <h3 className="mb-3">
                <i className="fas fa-star me-2"></i>
                Latest Match Results
              </h3>
              <div className="row">
                {latestJobs.map((job) => (
                  <div key={job.id} className="col-lg-6 col-xl-4 mb-3">
                    <JobMatchCard 
                      matchedJob={job}
                      onViewDetails={handleJobDetails}
                      onUpdateStatus={handleJobStatusUpdate}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 匹配历史列表 */}
          <MatchHistoryList 
            limit={20}
            onJobDetails={handleJobDetails}
          />
        </div>
      </div>

      {/* 工作详情模态框 */}
      {selectedJob && (
        <div 
          className={`modal fade ${showDetails ? 'show' : ''}`}
          style={{ display: showDetails ? 'block' : 'none' }}
          tabIndex={-1}
          role="dialog"
        >
          <div className="modal-dialog modal-lg" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="fas fa-briefcase me-2"></i>
                  {selectedJob.title}
                </h5>
                <button 
                  type="button" 
                  className="btn-close"
                  onClick={() => setShowDetails(false)}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <div className="row">
                  <div className="col-md-8">
                    <h6>Company: {selectedJob.company}</h6>
                    <p className="text-muted">
                      <i className="fas fa-map-marker-alt me-1"></i>
                      {selectedJob.location} | {selectedJob.level} | {selectedJob.industry}
                    </p>
                    
                    {/* 匹配分析 */}
                    <div className="mb-4">
                      <h6 className="text-primary">Match Analysis</h6>
                      <p>{selectedJob.analysis.reasoning}</p>
                      
                      {/* 关键洞察 */}
                      {selectedJob.analysis.key_insights.length > 0 && (
                        <div className="mb-3">
                          <strong>Key Insights:</strong>
                          <ul className="mt-2">
                            {selectedJob.analysis.key_insights.map((insight, index) => (
                              <li key={index} className="small">{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* 申请建议 */}
                    <div className="mb-4">
                      <h6 className="text-success">Application Tips</h6>
                      {selectedJob.application_tips.specific_advice && (
                        <p className="mb-2">{selectedJob.application_tips.specific_advice}</p>
                      )}
                      
                      {selectedJob.application_tips.tips.length > 0 && (
                        <div className="mb-3">
                          <strong>Tips:</strong>
                          <ul className="mt-2">
                            {selectedJob.application_tips.tips.map((tip, index) => (
                              <li key={index} className="small">{tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* 工作描述 */}
                    {selectedJob.description && (
                      <div className="mb-3">
                        <h6>Job Description</h6>
                        <div className="border p-3 rounded bg-light" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                          <pre className="small mb-0" style={{ whiteSpace: 'pre-wrap' }}>
                            {selectedJob.description}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="col-md-4">
                    <div className="text-center mb-3">
                      <h2 className="text-primary">{selectedJob.score}%</h2>
                      <small className="text-muted">Match Score</small>
                    </div>
                    
                    <div className="mb-3">
                      <span className={`badge badge-${selectedJob.status} fs-6`}>
                        {selectedJob.status.charAt(0).toUpperCase() + selectedJob.status.slice(1)}
                      </span>
                    </div>
                    
                    {selectedJob.applicationUrl && (
                      <a 
                        href={selectedJob.applicationUrl}
                        className="btn btn-primary w-100 mb-3"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <i className="fas fa-external-link-alt me-1"></i>
                        Apply Now
                      </a>
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowDetails(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MatchHistoryPage

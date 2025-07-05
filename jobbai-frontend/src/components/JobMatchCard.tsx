/**
 * 匹配工作卡片组件
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求实现
 * 使用新的JSONB结构化数据展示
 */

import React from 'react'
import type { MatchedJob } from '../types'

interface JobMatchCardProps {
  matchedJob: MatchedJob
  onViewDetails?: (jobId: string) => void
  onUpdateStatus?: (jobId: string, status: string) => void
}

export const JobMatchCard: React.FC<JobMatchCardProps> = ({ 
  matchedJob, 
  onViewDetails, 
  onUpdateStatus 
}) => {
  console.log('[JobMatchCard] Rendering job card')
  console.log('[JobMatchCard] matchedJob data:', matchedJob)
  console.log('[JobMatchCard] analysis:', matchedJob.analysis)
  console.log('[JobMatchCard] application_tips:', matchedJob.application_tips)
  
  const { analysis: analysis, application_tips } = matchedJob

  // 如果analysis_data或application_tips为空，提供默认值
  const safeAnalysisData = analysis || {
    reasoning: 'No analysis available',
    pros: [],
    cons: [],
    key_insights: []
  }
  
  const safeApplicationTips = application_tips || {
    specific_advice: 'No tips available',
    tips: [],
    recommendations: []
  }

  console.log('[JobMatchCard] safeAnalysisData:', safeAnalysisData)
  console.log('[JobMatchCard] safeApplicationTips:', safeApplicationTips)

  const handleViewDetails = () => {
    if (onViewDetails) {
      onViewDetails(matchedJob.id)
    }
  }

  const handleStatusChange = (newStatus: string) => {
    if (onUpdateStatus) {
      onUpdateStatus(matchedJob.id, newStatus)
    }
  }

  return (
    <div className="card job-match-card shadow-sm">
      <div className="card-body">
        {/* 工作基本信息 */}
        <div className="d-flex justify-content-between align-items-start mb-3">
          <div>
            <h5 className="card-title mb-1">
              <button 
                className="btn btn-link p-0 text-decoration-none"
                onClick={handleViewDetails}
              >
                {matchedJob.title}
              </button>
            </h5>
            <p className="text-muted mb-1">{matchedJob.company}</p>
            <small className="text-muted">
              <i className="fas fa-map-marker-alt me-1"></i>
              {matchedJob.location} | {matchedJob.level} | {matchedJob.industry}
            </small>
          </div>
          <div className="text-center">
            <h3 className="mb-1 text-primary">
              {matchedJob.score || 'N/A'}
              {matchedJob.score && '%'}
            </h3>
            <small className="text-muted">Match Score</small>
          </div>
        </div>

        {/* 匹配原因 */}
        {safeAnalysisData.reasoning && (
          <div className="mb-3">
            <p className="small text-muted mb-1">
              <i className="fas fa-lightbulb me-1"></i>
              {safeAnalysisData.reasoning}
            </p>
          </div>
        )}

        {/* 优势和劣势 */}
        {(safeAnalysisData.pros.length > 0 || safeAnalysisData.cons.length > 0) && (
          <div className="mb-3">
            <div className="accordion accordion-flush" id={`accordion-${matchedJob.id}`}>
              <div className="accordion-item">
                <h2 className="accordion-header">
                  <button 
                    className="accordion-button collapsed p-2" 
                    type="button" 
                    data-bs-toggle="collapse" 
                    data-bs-target={`#collapse-insights-${matchedJob.id}`}
                  >
                    <small><strong>Key Insights</strong></small>
                  </button>
                </h2>
                <div 
                  id={`collapse-insights-${matchedJob.id}`} 
                  className="accordion-collapse collapse"
                  data-bs-parent={`#accordion-${matchedJob.id}`}
                >
                  <div className="accordion-body p-2">
                    <div className="row">
                      {safeAnalysisData.pros.length > 0 && (
                        <div className="col-md-6">
                          <h6 className="text-success mb-2">
                            <i className="fas fa-thumbs-up me-1"></i>Pros
                          </h6>
                          <ul className="list-unstyled">
                            {safeAnalysisData.pros.map((pro, index) => (
                              <li key={index} className="small mb-1">
                                <i className="fas fa-check-circle text-success me-1"></i>
                                {pro}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {safeAnalysisData.cons.length > 0 && (
                        <div className="col-md-6">
                          <h6 className="text-danger mb-2">
                            <i className="fas fa-thumbs-down me-1"></i>Cons
                          </h6>
                          <ul className="list-unstyled">
                            {safeAnalysisData.cons.map((con, index) => (
                              <li key={index} className="small mb-1">
                                <i className="fas fa-times-circle text-danger me-1"></i>
                                {con}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 申请建议 */}
        {safeApplicationTips.tips.length > 0 && (
          <div className="mb-3">
            <div className="accordion accordion-flush" id={`accordion-tips-${matchedJob.id}`}>
              <div className="accordion-item">
                <h2 className="accordion-header">
                  <button 
                    className="accordion-button collapsed p-2" 
                    type="button" 
                    data-bs-toggle="collapse" 
                    data-bs-target={`#collapse-tips-${matchedJob.id}`}
                  >
                    <small><strong>Application Tips</strong></small>
                  </button>
                </h2>
                <div 
                  id={`collapse-tips-${matchedJob.id}`} 
                  className="accordion-collapse collapse"
                  data-bs-parent={`#accordion-tips-${matchedJob.id}`}
                >
                  <div className="accordion-body p-2">
                    {safeApplicationTips.specific_advice && (
                      <p className="small mb-2">
                        <strong>Specific Advice:</strong> {safeApplicationTips.specific_advice}
                      </p>
                    )}
                    {safeApplicationTips.tips.length > 0 && (
                      <div className="mb-2">
                        <h6 className="small mb-1">Tips:</h6>
                        <ul className="list-unstyled">
                          {safeApplicationTips.tips.map((tip, index) => (
                            <li key={index} className="small mb-1">
                              <i className="fas fa-arrow-right me-1"></i>
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {safeApplicationTips.recommendations.length > 0 && (
                      <div>
                        <h6 className="small mb-1">Recommendations:</h6>
                        <ul className="list-unstyled">
                          {safeApplicationTips.recommendations.map((rec, index) => (
                            <li key={index} className="small mb-1">
                              <i className="fas fa-star me-1"></i>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="d-flex justify-content-between align-items-center mt-3">
          <div className="btn-group btn-group-sm">
            <button 
              className="btn btn-outline-secondary"
              onClick={() => handleStatusChange('viewed')}
            >
              <i className="fas fa-eye me-1"></i>
              View
            </button>
            <button 
              className="btn btn-outline-primary"
              onClick={() => handleStatusChange('applied')}
            >
              <i className="fas fa-paper-plane me-1"></i>
              Applied
            </button>
          </div>
          
          {matchedJob.applicationUrl && (
            <a 
              href={matchedJob.applicationUrl} 
              className="btn btn-primary btn-sm"
              target="_blank"
              rel="noopener noreferrer"
            >
              <i className="fas fa-external-link-alt me-1"></i>
              Apply Now
            </a>
          )}
        </div>

        {/* 状态显示 */}
        <div className="mt-2">
          <span className={`badge badge-${matchedJob.status}`}>
            {matchedJob.status.charAt(0).toUpperCase() + matchedJob.status.slice(1)}
          </span>
        </div>
      </div>
    </div>
  )
}

export default JobMatchCard

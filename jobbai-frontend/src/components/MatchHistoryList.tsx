/**
 * 匹配历史列表组件
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求实现
 * 展示用户的匹配历史和结构化数据
 */

import React, { useState, useEffect } from 'react'
import { matchApi } from '../services/api'
import { JobMatchCard } from './JobMatchCard'
import type { MatchSession } from '../types'

interface MatchHistoryListProps {
  limit?: number
  onJobDetails?: (jobId: string) => void
}

export const MatchHistoryList: React.FC<MatchHistoryListProps> = ({ 
  limit = 10, 
  onJobDetails 
}) => {
  const [sessions, setSessions] = useState<MatchSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMatchHistory()
  }, [limit])

  const loadMatchHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await matchApi.getMatchHistory(limit)
      
      if (response.success && response.data) {
        setSessions(response.data.sessions)
      } else {
        setError(response.error || 'Failed to load match history')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateJobStatus = async (jobId: string, status: string) => {
    try {
      const response = await matchApi.updateJobStatus(jobId, { status: status as any })
      
      if (response.success) {
        // 更新本地状态
        setSessions(prevSessions => 
          prevSessions.map(session => ({
            ...session,
            matched_jobs: session.matched_jobs.map(job => 
              job.id === jobId ? { ...job, status: status as any } : job
            )
          }))
        )
      }
    } catch (err) {
      console.error('Failed to update job status:', err)
    }
  }

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <i className="fas fa-exclamation-triangle me-2"></i>
        {error}
        <button className="btn btn-link ms-2" onClick={loadMatchHistory}>
          Try Again
        </button>
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-5">
        <i className="fas fa-search fa-3x text-muted mb-3"></i>
        <h4>No Match History Found</h4>
        <p className="text-muted">
          You haven't run any AI matching yet. 
          <br />
          Start by triggering your first match!
        </p>
      </div>
    )
  }

  return (
    <div className="match-history-list">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Match History</h3>
        <button 
          className="btn btn-outline-primary btn-sm"
          onClick={loadMatchHistory}
        >
          <i className="fas fa-refresh me-1"></i>
          Refresh
        </button>
      </div>

      {sessions.map((session) => (
        <div key={session.id} className="mb-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5>
              <i className="fas fa-history me-2"></i>
              Match Session - {new Date(session.matched_at).toLocaleDateString()}
            </h5>
            <small className="text-muted">
              {session.matched_jobs.length} jobs matched
            </small>
          </div>

          {/* 会话摘要 */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="row">
                <div className="col-md-6">
                  <h6 className="mb-1">Skills:</h6>
                  <p className="small text-muted">
                    {session.skills_text.substring(0, 100)}...
                  </p>
                </div>
                <div className="col-md-6">
                  <h6 className="mb-1">Preferences:</h6>
                  <p className="small text-muted">
                    {session.user_preferences_text.substring(0, 100)}...
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 匹配的工作 */}
          <div className="row">
            {session.matched_jobs.map((job) => (
              <div key={job.id} className="col-lg-6 col-xl-4 mb-3">
                <JobMatchCard 
                  matchedJob={job}
                  onViewDetails={onJobDetails}
                  onUpdateStatus={handleUpdateJobStatus}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default MatchHistoryList

/**
 * 匹配历史数据管理Hook
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求实现
 * 使用新的JSONB结构化数据API
 */

import { useState, useEffect, useCallback } from 'react'
import { matchApi } from '../services/api'
import type { MatchSession, MatchedJob, MatchJobStatusUpdate } from '../types'

interface UseMatchHistoryReturn {
  // 数据状态
  sessions: MatchSession[]
  latestJobs: MatchedJob[]
  loading: boolean
  error: string | null
  
  // 操作方法
  loadMatchHistory: () => Promise<void>
  loadLatestMatch: () => Promise<void>
  triggerNewMatch: () => Promise<void>
  updateJobStatus: (jobId: string, statusUpdate: MatchJobStatusUpdate) => Promise<void>
  getJobDetails: (jobId: string) => Promise<MatchedJob | null>
  
  // 状态管理
  clearError: () => void
  refresh: () => Promise<void>
}

export const useMatchHistory = (limit: number = 10): UseMatchHistoryReturn => {
  const [sessions, setSessions] = useState<MatchSession[]>([])
  const [latestJobs, setLatestJobs] = useState<MatchedJob[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 加载匹配历史
  const loadMatchHistory = useCallback(async () => {
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
  }, [limit])

  // 加载最新匹配结果
  const loadLatestMatch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('[useMatchHistory] Loading latest match...')
      const response = await matchApi.getLatestMatch()
      
      console.log('[useMatchHistory] Latest match response:', response)
      
      if (response.success && response.data) {
        console.log('[useMatchHistory] Latest jobs received:', response.data.jobs?.length)
        console.log('[useMatchHistory] First job structure:', response.data.jobs?.[0])
        
        setLatestJobs(response.data.jobs)
        console.log('[useMatchHistory] Latest jobs set in state')
      } else {
        console.error('[useMatchHistory] Failed to load latest match:', response.error)
        setError(response.error || 'Failed to load latest match')
      }
    } catch (err) {
      console.error('[useMatchHistory] Error loading latest match:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  // 触发新的匹配
  const triggerNewMatch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('[useMatchHistory] Triggering new match...')
      const response = await matchApi.triggerMatch()
      
      console.log('[useMatchHistory] Trigger match response:', response)
      
      if (response.success && response.data) {
        console.log('[useMatchHistory] New match jobs received:', response.data.jobs?.length)
        console.log('[useMatchHistory] First new job structure:', response.data.jobs?.[0])
        
        // 更新最新匹配结果
        setLatestJobs(response.data.jobs)
        console.log('[useMatchHistory] New jobs set in state')
        
        // 重新加载历史记录
        await loadMatchHistory()
      } else {
        console.error('[useMatchHistory] Failed to trigger match:', response.error)
        setError(response.error || 'Failed to trigger match')
      }
    } catch (err) {
      console.error('[useMatchHistory] Error triggering match:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [loadMatchHistory])

  // 更新工作状态
  const updateJobStatus = useCallback(async (jobId: string, statusUpdate: MatchJobStatusUpdate) => {
    try {
      const response = await matchApi.updateJobStatus(jobId, statusUpdate)
      
      if (response.success) {
        // 更新sessions中的工作状态
        setSessions(prevSessions => 
          prevSessions.map(session => ({
            ...session,
            matched_jobs: session.matched_jobs.map(job => 
              job.id === jobId ? { ...job, status: statusUpdate.status } : job
            )
          }))
        )
        
        // 更新latestJobs中的工作状态
        setLatestJobs(prevJobs => 
          prevJobs.map(job => 
            job.id === jobId ? { ...job, status: statusUpdate.status } : job
          )
        )
      } else {
        setError(response.error || 'Failed to update job status')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }, [])

  // 获取工作详情
  const getJobDetails = useCallback(async (jobId: string): Promise<MatchedJob | null> => {
    try {
      const response = await matchApi.getMatchJobDetails(jobId)
      
      if (response.success && response.data) {
        return response.data.job
      } else {
        setError(response.error || 'Failed to get job details')
        return null
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    }
  }, [])

  // 清除错误
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // 刷新所有数据
  const refresh = useCallback(async () => {
    await Promise.all([
      loadMatchHistory(),
      loadLatestMatch()
    ])
  }, [loadMatchHistory, loadLatestMatch])

  // 初始化加载
  useEffect(() => {
    loadMatchHistory()
  }, [loadMatchHistory])

  return {
    // 数据状态
    sessions,
    latestJobs,
    loading,
    error,
    
    // 操作方法
    loadMatchHistory,
    loadLatestMatch,
    triggerNewMatch,
    updateJobStatus,
    getJobDetails,
    
    // 状态管理
    clearError,
    refresh
  }
}

export default useMatchHistory

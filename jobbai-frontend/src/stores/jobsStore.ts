import { create } from 'zustand'
import type { Job } from '../types'
import { jobsApi, matchApi } from '../services/api'
import { useSessionStore } from './sessionStore'

interface JobsState {
  // 状态
  jobs: Job[]
  loading: boolean
  error: string | null
  lastFetch: number | null
  
  // 动作
  fetchJobs: () => Promise<void>
  fetchMatchedJobs: (forceRefresh?: boolean) => Promise<void>
  triggerAIMatch: () => Promise<void>
  clearError: () => void
  
  // 辅助方法
  getJobById: (id: string) => Job | undefined
}

export const useJobsStore = create<JobsState>()((set, get) => ({
  // 初始状态
  jobs: [],
  loading: false,
  error: null,
  lastFetch: null,
  
  // 获取所有工作（公开访问）
  fetchJobs: async () => {
    console.log('[JobsStore] Fetching jobs...')
    set({ loading: true, error: null })
    
    try {
      const response = await jobsApi.getJobs()
      
      if (response.success && response.data) {
        console.log('[JobsStore] Jobs fetched successfully:', response.data.count)
        set({ 
          jobs: response.data.jobs, 
          loading: false,
          lastFetch: Date.now()
        })
      } else {
        throw new Error(response.error || 'Failed to fetch jobs')
      }
    } catch (error) {
      console.error('[JobsStore] Error fetching jobs:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 获取用户匹配的工作（需要认证）- 带缓存优化
  fetchMatchedJobs: async (forceRefresh = false) => {
    console.log('[JobsStore] Fetching matched jobs...')
    
    // 缓存优化：如果不是强制刷新且5分钟内已获取过，则跳过
    const { lastFetch } = get()
    if (!forceRefresh && lastFetch && Date.now() - lastFetch < 5 * 60 * 1000) {
      console.log('[JobsStore] Using cached jobs, skipping API call')
      return
    }
    
    set({ loading: true, error: null })
    
    try {
      const response = await matchApi.getLatestMatch()
      
      console.log('[JobsStore] API response:', response)
      
      if (response.success && response.data) {
        console.log('[JobsStore] Matched jobs fetched successfully:', response.data.count)
        
        // 同时设置会话信息到 sessionStore
        if (response.data.session_id && response.data.matched_at) {
          const sessionInfo = {
            id: response.data.session_id,
            matched_at: response.data.matched_at,
            user_id: response.data.user_id,
            created_at: response.data.matched_at,
            skills_text: '',
            user_preferences_text: '',
            structured_user_profile_json: {},
            job_count: response.data.jobs?.length || 0
          }
          useSessionStore.getState().setCurrentSession(sessionInfo)
        }
        
        // 数据转换和验证
        if (response.data.jobs && Array.isArray(response.data.jobs)) {
          // 转换MatchedJob到Job类型（使用统一的字段）
          const jobs: Job[] = response.data.jobs.map((matchedJob: any) => {
            console.log('[JobsStore] Processing job:', matchedJob.id, 'title:', matchedJob.title)
            return {
              id: String(matchedJob.id), // 确保ID是字符串
              job_id: matchedJob.job_id,
              title: matchedJob.title,
              company: matchedJob.company,
              location: matchedJob.location,
              level: matchedJob.level,
              industry: matchedJob.industry,
              flexibility: matchedJob.flexibility,
              salaryRange: matchedJob.salaryRange,
              description: matchedJob.description,
              applicationUrl: matchedJob.applicationUrl,
              created_at: matchedJob.created_at,
              updated_at: matchedJob.updated_at,
              score: matchedJob.score,
              status: matchedJob.status,
              analysis: matchedJob.analysis,
              application_tips: matchedJob.application_tips,
            }
          })
          
          console.log('[JobsStore] Converted jobs:', jobs.map(job => ({ id: job.id, title: job.title, idType: typeof job.id })))
          
          set({ 
            jobs: jobs,
            loading: false,
            lastFetch: Date.now()
          })
          console.log('[JobsStore] Jobs successfully converted and set in store')
        } else {
          console.warn('[JobsStore] No jobs array in response data')
          set({ 
            jobs: [],
            loading: false,
            lastFetch: Date.now()
          })
        }
      } else {
        console.error('[JobsStore] API response failed:', response.error)
        throw new Error(response.error || 'Failed to fetch matched jobs')
      }
    } catch (error) {
      console.error('[JobsStore] Error fetching matched jobs:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 触发AI匹配工作（需要认证）
  triggerAIMatch: async () => {
    console.log('[JobsStore] Triggering AI match...')
    set({ loading: true, error: null })
    
    try {
      const response = await matchApi.triggerMatch()
      
      console.log('[JobsStore] Trigger match API response:', response)
      
      if (response.success && response.data) {
        console.log('[JobsStore] AI match completed successfully:', response.data.count)
        
        // 同时设置会话信息到 sessionStore
        if (response.data.session_id && response.data.matched_at) {
          const sessionInfo = {
            id: response.data.session_id,
            matched_at: response.data.matched_at,
            user_id: response.data.user_id,
            created_at: response.data.matched_at,
            skills_text: '',
            user_preferences_text: '',
            structured_user_profile_json: {},
            job_count: response.data.jobs?.length || 0
          }
          useSessionStore.getState().setCurrentSession(sessionInfo)
        }
        
        // 数据转换和验证
        if (response.data.jobs && Array.isArray(response.data.jobs)) {
          // 转换MatchedJob到Job类型（使用统一的字段）
          const jobs: Job[] = response.data.jobs.map((matchedJob: any) => {
            console.log('[JobsStore] Processing job from trigger:', matchedJob.id, 'title:', matchedJob.title)
            return {
              id: String(matchedJob.id), // 确保ID是字符串
              job_id: matchedJob.job_id,
              title: matchedJob.title,
              company: matchedJob.company,
              location: matchedJob.location,
              level: matchedJob.level,
              industry: matchedJob.industry,
              flexibility: matchedJob.flexibility,
              salaryRange: matchedJob.salaryRange,
              description: matchedJob.description,
              applicationUrl: matchedJob.applicationUrl,
              created_at: matchedJob.created_at,
              updated_at: matchedJob.updated_at,
              score: matchedJob.score,
              status: matchedJob.status,
              analysis: matchedJob.analysis,
              application_tips: matchedJob.application_tips,
            }
          })
          
          console.log('[JobsStore] Converted jobs from trigger:', jobs.map(job => ({ id: job.id, title: job.title, idType: typeof job.id })))
          
          set({ 
            jobs: jobs,
            loading: false,
            lastFetch: Date.now()
          })
          console.log('[JobsStore] New jobs successfully converted and set in store')
        } else {
          console.warn('[JobsStore] No jobs array in trigger response data')
          set({ 
            jobs: [],
            loading: false,
            lastFetch: Date.now()
          })
        }
      } else {
        console.error('[JobsStore] Trigger match API response failed:', response.error)
        throw new Error(response.error || 'Failed to trigger AI match')
      }
    } catch (error) {
      console.error('[JobsStore] Error triggering AI match:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 清除错误
  clearError: () => {
    set({ error: null })
  },
  
  // 根据ID获取工作
  getJobById: (id: string) => {
    const { jobs } = get()
    console.log('[JobsStore] getJobById called with id:', id, 'type:', typeof id)
    console.log('[JobsStore] Available jobs:', jobs.map(job => ({ id: job.id, title: job.title, idType: typeof job.id })))
    
    const foundJob = jobs.find(job => job.id === id)
    console.log('[JobsStore] Found job:', foundJob ? `${foundJob.title} (${foundJob.id})` : 'NOT FOUND')
    
    // 尝试使用字符串转换进行匹配
    if (!foundJob) {
      const foundJobStr = jobs.find(job => String(job.id) === String(id))
      console.log('[JobsStore] Found job with string conversion:', foundJobStr ? `${foundJobStr.title} (${foundJobStr.id})` : 'NOT FOUND')
      return foundJobStr
    }
    
    return foundJob
  }
}))

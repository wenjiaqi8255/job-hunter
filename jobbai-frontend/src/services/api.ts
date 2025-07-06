import { supabase } from './supabase'
import type { ApiResponse } from '../types'

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// 获取认证头部
const getAuthHeaders = async (): Promise<Record<string, string>> => {
  const { data: { session } } = await supabase.auth.getSession()
  
  console.log('[API] 获取认证头部 - 会话状态:', {
    hasSession: !!session,
    hasAccessToken: !!session?.access_token,
    tokenLength: session?.access_token?.length,
    userId: session?.user?.id,
    userEmail: session?.user?.email
  })
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
    console.log('[API] 添加认证头部:', `Bearer ${session.access_token.substring(0, 20)}...`)
  } else {
    console.warn('[API] 警告: 无认证令牌')
  }
  
  return headers
}

// API客户端类
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      // 获取认证头部
      const authHeaders = await getAuthHeaders()
      
      // 合并头部
      const headers = {
        ...authHeaders,
        ...options.headers,
      }

      console.log(`[API] ${options.method || 'GET'} ${url}`)
      
      const response = await fetch(url, {
        ...options,
        headers,
      })

      console.log(`[API] ${url} response:`, response.status)

      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      return {
        success: true,
        data,
      }
    } catch (error) {
      console.error(`[API] Error calling ${url}:`, error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  // GET请求
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST请求
  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PUT请求
  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PATCH请求
  async patch<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // DELETE请求
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// 导出API客户端实例
export const apiClient = new ApiClient(API_BASE_URL)

// 工作相关API调用
export const jobsApi = {
  // 获取所有工作列表（公开访问）
  getJobs: async () => {
    return apiClient.get<import('../types').MatchApiResponse>('/api/jobs/')
  },
  
  // 获取单个工作详情（公开访问）
  getJobDetail: async (jobId: string) => {
    return apiClient.get<{ success: boolean; job: import('../types').Job }>(`/api/jobs/${jobId}/`)
  },
  
  // 获取用户的匹配工作（需要认证）- 使用简单的静态匹配
  getMatchedJobs: async () => {
    return apiClient.get<import('../types').MatchApiResponse>('/api/jobs/matched/')
  },
  
  // 触发AI匹配工作（需要认证）- 兼容性保留，推荐使用matchApi.triggerMatch
  triggerAIMatch: async () => {
    return apiClient.post<import('../types').MatchApiResponse>('/api/match-jobs/')
  },
  
  // 保存工作
  saveJob: async (jobId: string, status: string, notes?: string) => {
    return apiClient.post<import('../types').SaveJobApiResponse>('/api/jobs/save/', { job_id: jobId, status, notes })
  },
  
  // 获取用户保存的工作
  getSavedJobs: async () => {
    return apiClient.get<import('../types').SavedJobsApiResponse>('/api/jobs/saved/')
  },
  
  // 获取单个工作的保存状态
  getJobSavedStatus: async (jobId: string) => {
    return apiClient.get<import('../types').JobSavedStatusApiResponse>(`/api/jobs/${jobId}/saved-status/`)
  }
}

// 用户相关API调用
export const userApi = {
  // 获取用户个人资料
  getProfile: async () => {
    return apiClient.get<import('../types').UserProfileApiResponse>('/api/user-profile/')
  },
  
  // 更新用户个人资料
  updateProfile: async (profileData: any) => {
    return apiClient.post<import('../types').UserProfileApiResponse>('/api/user-profile/', profileData)
  },
  
  // 触发CV分析
  analyzeCV: async (cvText: string) => {
    return apiClient.post<import('../types').CVAnalysisApiResponse>('/api/cv-analysis/', { cv_text: cvText })
  }
}

// 系统健康检查API
export const systemApi = {
  // 获取系统健康状态
  getHealthStatus: async () => {
    return apiClient.get<import('../types').HealthStatusApiResponse>('/api/sync-health/')
  }
}

// 匹配历史API调用 (新增)
export const matchApi = {
  // 触发AI匹配 (新的语义化端点)
  triggerMatch: async () => {
    return apiClient.post<import('../types').MatchApiResponse>('/api/match/trigger/')
  },
  
  // 获取最新匹配结果 (新的语义化端点)
  getLatestMatch: async () => {
    return apiClient.get<import('../types').MatchApiResponse>('/api/match/latest/')
  },
  
  // 获取匹配工作详情 (新的语义化端点)
  getMatchJobDetails: async (jobMatchId: string) => {
    return apiClient.get<import('../types/matching').MatchJobDetailsResponse>(`/api/match/session/${jobMatchId}/`)
  },
  
  // 更新匹配工作状态
  updateJobStatus: async (jobMatchId: string, statusUpdate: import('../types/matching').MatchJobStatusUpdate) => {
    return apiClient.patch(`/api/match/session/${jobMatchId}/`, statusUpdate)
  }
}

// 开发环境日志
if (import.meta.env.VITE_NODE_ENV === 'development') {
  console.log('[API] Client initialized with base URL:', API_BASE_URL)
}

// 求职信相关API调用
export const coverLetterApi = {
  // 生成求职信
  generateCoverLetter: async (jobId: string) => {
    return apiClient.post<import('../types').CoverLetterApiResponse>(`/api/jobs/${jobId}/cover-letter/`)
  },
  
  // 获取求职信
  getCoverLetter: async (jobId: string) => {
    return apiClient.get<import('../types').CoverLetterApiResponse>(`/api/jobs/${jobId}/cover-letter/get/`)
  },
  
  // 更新求职信
  updateCoverLetter: async (jobId: string, content: string) => {
    return apiClient.put<import('../types').CoverLetterApiResponse>(`/api/jobs/${jobId}/cover-letter/update/`, { content })
  }
}

// 定制简历相关API调用
export const customCvApi = {
  // 生成定制简历
  generateCustomCv: async (jobId: string) => {
    return apiClient.post<import('../types').CustomCvApiResponse>(`/api/jobs/${jobId}/custom-cv/`)
  },
  
  // 获取定制简历
  getCustomCv: async (jobId: string) => {
    return apiClient.get<import('../types').CustomCvApiResponse>(`/api/jobs/${jobId}/custom-cv/get/`)
  },
  
  // 更新定制简历
  updateCustomCv: async (jobId: string, content: string, customizationNotes?: string) => {
    return apiClient.put<import('../types').CustomCvApiResponse>(`/api/jobs/${jobId}/custom-cv/update/`, { 
      content, 
      customization_notes: customizationNotes 
    })
  }
}

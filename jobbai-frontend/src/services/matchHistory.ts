/**
 * 匹配历史API服务
 * 重构后：主要功能已移至统一的 API 服务
 * 此文件标记为废弃，将在未来版本中移除
 */

import { apiClient } from './api'
import type { 
  MatchApiResponse,
  ApiResponse 
} from '../types'
import type {
  MatchJobDetailsResponse,
  MatchJobStatusUpdate
} from '../types/matching'

export const matchHistoryApi = {
  /**
   * @deprecated - 不再使用，数据统一从 api.getLatestMatch() 获取
   * 获取用户的匹配历史
   */
  getMatchHistory: async (limit?: number): Promise<ApiResponse<MatchApiResponse>> => {
    const params = limit ? `?limit=${limit}` : ''
    return apiClient.get<MatchApiResponse>(`/api/match/history/${params}`)
  },

  /**
   * 获取特定匹配工作的详细信息
   * 使用新的语义化API端点: /api/match/session/<id>/
   */
  getMatchJobDetails: async (jobMatchId: string): Promise<ApiResponse<MatchJobDetailsResponse>> => {
    return apiClient.get<MatchJobDetailsResponse>(`/api/match/session/${jobMatchId}/`)
  },

  /**
   * 触发AI匹配
   * 使用新的语义化API端点: /api/match/trigger/
   */
  triggerMatch: async (): Promise<ApiResponse<MatchApiResponse>> => {
    return apiClient.post<MatchApiResponse>('/api/match/trigger/')
  },

  /**
   * 获取最新匹配结果
   * 使用新的语义化API端点: /api/match/latest/
   */
  getLatestMatch: async (): Promise<ApiResponse<MatchApiResponse>> => {
    return apiClient.get<MatchApiResponse>('/api/match/latest/')
  },

  /**
   * 更新匹配工作状态
   * 注意：这个API端点可能需要在后端实现
   */
  updateJobStatus: async (jobMatchId: string, statusUpdate: MatchJobStatusUpdate): Promise<ApiResponse<any>> => {
    return apiClient.patch(`/api/match/session/${jobMatchId}/`, statusUpdate)
  }
}

// 为了向后兼容，保留旧的API调用方式
export const legacyMatchApi = {
  /**
   * 触发AI匹配 (旧API端点)
   * 兼容性端点: /api/match-jobs/
   */
  triggerAIMatch: async (): Promise<ApiResponse<MatchApiResponse>> => {
    return apiClient.post<MatchApiResponse>('/api/match-jobs/')
  },

  /**
   * 获取匹配历史 (旧API端点)
   * 兼容性端点: /api/match-history/
   */
  getMatchHistory: async (): Promise<ApiResponse<MatchApiResponse>> => {
    return apiClient.get<MatchApiResponse>('/api/match-history/')
  },

  /**
   * 获取匹配工作详情 (旧API端点)
   * 兼容性端点: /api/match-history/job/<id>/
   */
  getMatchJobDetails: async (jobMatchId: string): Promise<ApiResponse<MatchJobDetailsResponse>> => {
    return apiClient.get<MatchJobDetailsResponse>(`/api/match-history/job/${jobMatchId}/`)
  }
}

/**
 * 匹配历史相关的TypeScript类型定义
 * 重构后：统一类型定义已移至 index.ts
 * 此文件仅保留导出以维持向后兼容性
 */

// 重新导出统一的类型定义
export type {
  AnalysisData,
  ApplicationTips,
  MatchedJob,
  MatchSession,
  MatchApiResponse as MatchHistoryResponse,
  MatchApiResponse as TriggerMatchResponse,
  MatchApiResponse as LatestMatchResponse,
} from './index'

// 保留的旧类型定义（向后兼容）
import type { MatchedJob } from './index'

export interface MatchJobDetailsResponse {
  success: boolean;
  job: MatchedJob;
  message?: string;
  error?: string;
}

export interface MatchJobStatusUpdate {
  status: 'new' | 'applied' | 'viewed' | 'rejected';
  notes?: string;
}

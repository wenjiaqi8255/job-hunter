// 用户相关类型
export interface User {
  id: string;
  email: string;
  user_metadata?: {
    name?: string;
    avatar_url?: string;
    full_name?: string;
  };
  created_at: string;
  updated_at: string;
}

// 认证状态
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 匹配分析数据结构
export interface AnalysisData {
  reasoning: string;
  pros: string[];
  cons: string[];
  key_insights: string[];
  match_details?: {
    skill_alignment: string;
    culture_fit: string;
    growth_potential: string;
  };
}

// 申请建议数据结构
export interface ApplicationTips {
  specific_advice: string;
  tips: string[];
  recommendations: string[];
  cover_letter_suggestions?: string[];
  interview_preparation?: string[];
}

// 基础工作信息（来自 job_listings 表）
export interface BaseJob {
  id: string;
  title: string;
  company: string;
  location: string;
  level: string;
  industry: string;
  flexibility: string;
  salaryRange?: string;
  description: string;
  applicationUrl?: string;
  created_at: string;
  updated_at: string;
}

// 匹配工作信息（来自 matched_jobs 表）
export interface MatchedJob extends BaseJob {
  job_id: string;
  score: number;
  status: 'new' | 'applied' | 'viewed' | 'rejected';
  analysis: AnalysisData;
  application_tips: ApplicationTips;
}

// 统一的工作类型（可能有匹配信息，也可能没有）
export type Job = BaseJob & Partial<Pick<MatchedJob, 'job_id' | 'score' | 'status' | 'analysis' | 'application_tips'>>

// 匹配会话数据结构
export interface MatchSession {
  id: string;
  user_id: string;
  skills_text: string;
  user_preferences_text: string;
  structured_user_profile_json: any;
  matched_at: string;
  created_at: string;
  job_count: number;
}

// 统一的API响应格式
export interface MatchApiResponse {
  success: boolean;
  jobs: Job[];
  count: number;
  session_id?: string;
  matched_at?: string;
  user_id: string;
  error?: string;
}

// 用户个人资料API响应
export interface UserProfileApiResponse {
  success: boolean;
  profile: {
    user_id: string;
    cv_text: string;
    preferences_text: string;
    structured_profile?: any;
    created_at: string;
    updated_at: string;
  };
  user_id?: string;
}

// CV分析API响应
export interface CVAnalysisApiResponse {
  success: boolean;
  analysis: {
    structured_profile: any;
    analysis_summary: string;
    timestamp: string;
  };
  user_id?: string;
}

// 健康状态API响应
export interface HealthStatusApiResponse {
  success: boolean;
  status: {
    django_status: string;
    supabase_status: string;
    sync_status: string;
    last_sync: string;
  };
}

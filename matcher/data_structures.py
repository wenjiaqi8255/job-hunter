"""
匹配历史数据结构单一事实来源
SINGLE SOURCE OF TRUTH for Match History Data Structure

目的：防止前后端数据结构不一致问题
用途：作为开发参考，确保所有组件使用统一的数据结构
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

class AnalysisData(TypedDict):
    """
    匹配分析数据结构 - 对应Supabase matched_jobs.analysis JSONB字段
    """
    reasoning: str
    pros: List[str]
    cons: List[str]
    key_insights: List[str]
    match_details: Optional[Dict[str, str]]  # skill_alignment, culture_fit, growth_potential

class ApplicationTips(TypedDict):
    """
    申请建议数据结构 - 对应Supabase matched_jobs.application_tips JSONB字段
    """
    specific_advice: str
    tips: List[str]
    recommendations: List[str]
    cover_letter_suggestions: Optional[List[str]]
    interview_preparation: Optional[List[str]]

class MatchedJobData(TypedDict):
    """
    匹配工作完整数据结构 - 前后端API传输格式
    对应Supabase matched_jobs表 + job_listings表的组合数据
    """
    # 基础标识符
    id: str                    # job_id，对应job_listings.id
    job_id: str               # 冗余字段，保持向后兼容
    
    # 匹配相关数据（来自matched_jobs表）
    score: Optional[int]       # 匹配分数 (0-100)
    status: str               # 匹配状态: 'new', 'applied', 'viewed', 'rejected'
    analysis: AnalysisData    # JSONB字段：匹配分析数据
    application_tips: ApplicationTips  # JSONB字段：申请建议数据
    
    # 工作基础信息（来自job_listings表）
    title: str                # job_title
    company: str              # company_name
    location: Optional[str]   # location
    level: Optional[str]      # level
    industry: str             # industry
    flexibility: Optional[str] # flexibility
    salaryRange: Optional[str] # salary_range
    description: Optional[str] # description
    applicationUrl: Optional[str] # application_url
    
    # 时间戳
    created_at: str           # ISO格式时间字符串
    updated_at: Optional[str] # ISO格式时间字符串
    
    # 向后兼容字段（前端可能仍在使用）
    matchScore: Optional[int] # 等同于score
    matchReason: Optional[str] # 等同于analysis.reasoning
    insights: Optional[List[Dict[str, Any]]] # 旧格式洞察数据
    tips: Optional[List[str]] # 等同于application_tips.tips
    recommendations: Optional[List[str]] # 等同于application_tips.recommendations

class MatchSessionData(TypedDict):
    """
    匹配会话数据结构 - 对应Supabase match_sessions表
    """
    id: str
    user_id: str
    skills_text: Optional[str]
    user_preferences_text: Optional[str]
    structured_user_profile_json: Optional[Dict[str, Any]]
    matched_at: Optional[str]
    created_at: str
    matched_jobs: List[MatchedJobData]

# API响应格式
class MatchHistoryApiResponse(TypedDict):
    """
    匹配历史API响应格式
    """
    success: bool
    sessions: List[MatchSessionData]
    count: int
    user_id: str
    error: Optional[str]

class LatestMatchApiResponse(TypedDict):
    """
    最新匹配API响应格式
    """
    success: bool
    jobs: List[MatchedJobData]
    count: int
    user_id: str
    session_id: Optional[str]
    matched_at: Optional[str]
    message: Optional[str]
    error: Optional[str]

class TriggerMatchApiResponse(TypedDict):
    """
    触发匹配API响应格式
    """
    success: bool
    jobs: List[MatchedJobData]
    count: int
    session_id: Optional[str]
    supabase_saved: bool
    message: str
    user_id: str
    error: Optional[str]

# 数据库字段映射
SUPABASE_FIELD_MAPPING = {
    # matched_jobs表字段
    'matched_jobs': {
        'id': 'id',
        'job_id': 'job_id',
        'match_session_id': 'match_session_id',
        'score': 'score',
        'status': 'status',
        'analysis': 'analysis',  # JSONB字段
        'application_tips': 'application_tips',  # JSONB字段
        'created_at': 'created_at'
    },
    # job_listings表字段
    'job_listings': {
        'id': 'id',
        'job_title': 'title',
        'company_name': 'company',
        'location': 'location',
        'level': 'level',
        'industry': 'industry',
        'flexibility': 'flexibility',
        'salary_range': 'salaryRange',
        'description': 'description',
        'application_url': 'applicationUrl',
        'created_at': 'created_at'
    },
    # match_sessions表字段
    'match_sessions': {
        'id': 'id',
        'user_id': 'user_id',
        'skills_text': 'skills_text',
        'user_preferences_text': 'user_preferences_text',
        'structured_user_profile_json': 'structured_user_profile_json',
        'matched_at': 'matched_at',
        'created_at': 'created_at'
    }
}

# 示例数据
SAMPLE_ANALYSIS_DATA = {
    "reasoning": "This AI automation marketing role is an excellent match for Jiaqi's technical skills, AI/ML background, and product thinking. The combination of marketing and IT aligns perfectly with his product management experience and technical capabilities.",
    "pros": [
        "Perfect location in Munich",
        "AI & Automation directly matches expertise",
        "Marketing + IT combination ideal",
        "Startup environment fits profile",
        "Internship allows learning"
    ],
    "cons": [
        "Internship vs Werkstudent (possibly lower pay)",
        "Small company less prestige",
        "Limited German still challenging"
    ],
    "key_insights": [
        "Excellent skill-role alignment",
        "Perfect industry match",
        "Great learning opportunity",
        "Builds on existing AI/ML experience"
    ],
    "match_details": {
        "skill_alignment": "Excellent - AI/ML, product strategy, technical skills all relevant",
        "culture_fit": "Excellent - startup environment, innovation focus",
        "growth_potential": "High - cutting-edge field with great career prospects"
    }
}

SAMPLE_APPLICATION_TIPS = {
    "specific_advice": "Below your skill level but could provide German business environment experience. Consider only if other options unavailable.",
    "tips": [
        "Highlight customer success metrics from PM roles",
        "Show understanding of business development",
        "Emphasize relationship building skills"
    ],
    "recommendations": [
        "Consider only as stepping stone or backup",
        "Focus on learning business development aspects"
    ],
    "cover_letter_suggestions": [
        "Connect customer success from product management",
        "Show interest in business development"
    ],
    "interview_preparation": [
        "Research company's sales process",
        "Prepare examples of customer relationship management"
    ]
}

# 前端TypeScript类型定义（用于生成TypeScript文件）
TYPESCRIPT_TYPES = '''
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

// 匹配的工作数据结构
export interface MatchedJob {
  id: string;
  job_id: string;
  score: number;
  status: 'new' | 'applied' | 'viewed' | 'rejected';
  
  // 新的JSONB结构化数据 - 与Supabase数据库字段名一致
  analysis: AnalysisData;
  application_tips: ApplicationTips;
  
  // 基础工作信息
  title: string;
  company: string;
  location: string;
  level: string;
  industry: string;
  flexibility: string;
  salaryRange?: string;
  description: string;
  applicationUrl?: string;
  
  // 时间戳
  created_at: string;
  updated_at: string;
  
  // 向后兼容字段
  matchScore?: number;
  matchReason?: string;
  insights?: Array<{
    category: string;
    content?: string;
    pros?: string[];
    cons?: string[];
  }>;
  tips?: string[];
  recommendations?: string[];
}
'''

if __name__ == "__main__":
    print("=== 匹配历史数据结构单一事实来源 ===")
    print("请确保前后端代码都遵循此数据结构定义")
    print("\n关键字段名:")
    print("- analysis (不是 analysis_data)")
    print("- application_tips (保持一致)")
    print("- 数据库字段名与API字段名保持一致")
    print("\n示例数据:")
    print("Analysis Data:", SAMPLE_ANALYSIS_DATA)
    print("Application Tips:", SAMPLE_APPLICATION_TIPS)

"""
Pydantic schemas - 对应Django models
保持数据结构的1:1映射，确保兼容性
"""
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# ========== 状态枚举 ==========
class SavedJobStatus(str, Enum):
    """保存工作的状态选择"""
    NOT_APPLIED = "not_applied"
    VIEWED = "viewed"
    APPLIED = "applied"
    INTERESTED = "interested"  # 添加前端使用的新状态
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"  # 添加后端验证逻辑中的状态

# ========== User相关 ==========
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    date_joined: datetime

    class Config:
        from_attributes = True

# ========== UserProfile ==========
class UserProfileBase(BaseModel):
    user_cv_text: Optional[str] = None
    user_preferences_text: Optional[str] = None
    user_email: Optional[EmailStr] = None

class UserProfileCreate(UserProfileBase):
    user_id: int

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    user_id: int  # 对应Django的user.id作为主键
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== JobListing ==========
class JobListingBase(BaseModel):
    company_name: str
    job_title: str
    description: Optional[str] = None
    translated_description: Optional[str] = None
    application_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    industry: str
    flexibility: Optional[str] = None
    salary_range: Optional[str] = None
    level: Optional[str] = None
    reason_for_match: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None

class JobListingCreate(JobListingBase):
    id: str  # Django中是CharField主键

class JobListingUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    translated_description: Optional[str] = None
    application_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    flexibility: Optional[str] = None
    salary_range: Optional[str] = None
    level: Optional[str] = None
    reason_for_match: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None

class JobListing(JobListingBase):
    id: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ========== MatchSession ==========
class MatchSessionBase(BaseModel):
    skills_text: str
    user_preferences_text: Optional[str] = None
    structured_user_profile_json: Optional[Dict[str, Any]] = None

class MatchSessionCreate(MatchSessionBase):
    user_id: Optional[int] = None

class MatchSession(MatchSessionBase):
    id: UUID
    user_id: Optional[int] = None
    matched_at: datetime
    
    class Config:
        from_attributes = True

# ========== MatchedJob ==========
class MatchedJobBase(BaseModel):
    score: int = 0
    reason: Optional[str] = None
    insights: Optional[str] = None
    tips: Optional[str] = None

class MatchedJobCreate(MatchedJobBase):
    match_session_id: UUID
    job_listing_id: str

class MatchedJob(MatchedJobBase):
    match_session_id: UUID
    job_listing_id: str
    
    # 关联对象
    job_listing: Optional[JobListing] = None
    
    class Config:
        from_attributes = True

# ========== SavedJob ==========
class SavedJobBase(BaseModel):
    status: SavedJobStatus = SavedJobStatus.NOT_APPLIED  # 使用枚举确保状态值有效
    notes: Optional[str] = None

class SavedJobCreate(SavedJobBase):
    job_listing_id: str
    user_id: int

class SavedJobUpdate(BaseModel):
    status: Optional[SavedJobStatus] = None
    notes: Optional[str] = None

class SavedJob(SavedJobBase):
    id: int
    job_listing_id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    # 关联对象
    job_listing: Optional[JobListing] = None
    
    class Config:
        from_attributes = True

# ========== CoverLetter ==========
class CoverLetterBase(BaseModel):
    content: str

class CoverLetterCreate(CoverLetterBase):
    saved_job_id: int  # 引用SavedJob的ID

class CoverLetterUpdate(CoverLetterBase):
    pass

class CoverLetter(CoverLetterBase):
    saved_job_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== CustomResume ==========
class CustomResumeBase(BaseModel):
    content: str

class CustomResumeCreate(CustomResumeBase):
    user_id: int
    job_listing_id: str

class CustomResumeUpdate(CustomResumeBase):
    pass

class CustomResume(CustomResumeBase):
    user_id: int
    job_listing_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== API响应schemas ==========
class JobMatchResponse(BaseModel):
    """工作匹配响应"""
    job_object: JobListing
    reason: Optional[str] = None
    score: int
    tips: Optional[str] = None
    parsed_tips_list: List[str] = []
    parsed_insights_list: List[str] = []
    job_anomalies: List[Dict[str, Any]] = []
    saved_status: Optional[str] = None

class MatchSessionResponse(BaseModel):
    """匹配会话响应"""
    session: MatchSession
    matched_jobs: List[JobMatchResponse]
    total_matches: int


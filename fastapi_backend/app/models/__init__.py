"""
SQLAlchemy models - 对应Django models
保持与Django数据库结构的1:1映射
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base

# ========== User模型 ==========
class User(Base):
    __tablename__ = "auth_user"  # Django默认用户表名
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(254), nullable=True)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Django用户模型的其他必需字段（简化）
    password = Column(String(128), nullable=False)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    
    # 关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    match_sessions = relationship("MatchSession", back_populates="user")
    saved_jobs = relationship("SavedJob", back_populates="user")
    custom_resumes = relationship("CustomResume", back_populates="user")

# ========== UserProfile模型 ==========
class UserProfile(Base):
    __tablename__ = "matcher_userprofile"
    
    user_id = Column(Integer, ForeignKey("auth_user.id"), primary_key=True)
    user_cv_text = Column(Text, nullable=True)
    user_preferences_text = Column(Text, nullable=True)
    user_email = Column(String(254), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="profile")

# ========== JobListing模型 ==========
class JobListing(Base):
    __tablename__ = "matcher_joblisting"
    
    id = Column(String(50), primary_key=True)  # 对应Django的CharField主键
    company_name = Column(String(200), nullable=False)
    job_title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    translated_description = Column(Text, nullable=True)
    application_url = Column(Text, nullable=True)  # URLField在SQLAlchemy中用Text
    location = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=False)
    flexibility = Column(String(50), nullable=True)
    salary_range = Column(String(100), nullable=True)
    level = Column(String(100), nullable=True)
    reason_for_match = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    matched_jobs = relationship("MatchedJob", back_populates="job_listing")
    saved_instances = relationship("SavedJob", back_populates="job_listing")
    custom_resumes = relationship("CustomResume", back_populates="job_listing")

# ========== MatchSession模型 ==========
class MatchSession(Base):
    __tablename__ = "matcher_matchsession"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID字段
    user_id = Column(Integer, ForeignKey("auth_user.id"), nullable=True)
    skills_text = Column(Text, nullable=False)
    user_preferences_text = Column(Text, nullable=True)
    structured_user_profile_json = Column(JSON, nullable=True)
    matched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="match_sessions")
    matched_jobs = relationship("MatchedJob", back_populates="match_session")

# ========== MatchedJob模型 ==========
class MatchedJob(Base):
    __tablename__ = "matcher_matchedjob"
    
    id = Column(Integer, primary_key=True, index=True)
    match_session_id = Column(String(36), ForeignKey("matcher_matchsession.id"), nullable=False)
    job_listing_id = Column(String(50), ForeignKey("matcher_joblisting.id"), nullable=False)
    score = Column(Integer, default=0)
    reason = Column(Text, nullable=True)
    insights = Column(Text, nullable=True)
    tips = Column(Text, nullable=True)
    
    # 关系
    match_session = relationship("MatchSession", back_populates="matched_jobs")
    job_listing = relationship("JobListing", back_populates="matched_jobs")

# ========== SavedJob模型 ==========
class SavedJob(Base):
    __tablename__ = "matcher_savedjob"
    
    id = Column(Integer, primary_key=True, index=True)
    job_listing_id = Column(String(50), ForeignKey("matcher_joblisting.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    status = Column(String(20), default="not_applied")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    job_listing = relationship("JobListing", back_populates="saved_instances")
    user = relationship("User", back_populates="saved_jobs")
    cover_letter = relationship("CoverLetter", back_populates="saved_job", uselist=False)

# ========== CoverLetter模型 ==========
class CoverLetter(Base):
    __tablename__ = "matcher_coverletter"
    
    id = Column(Integer, primary_key=True, index=True)
    saved_job_id = Column(Integer, ForeignKey("matcher_savedjob.id"), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    saved_job = relationship("SavedJob", back_populates="cover_letter")

# ========== CustomResume模型 ==========
class CustomResume(Base):
    __tablename__ = "matcher_customresume"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    job_listing_id = Column(String(50), ForeignKey("matcher_joblisting.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="custom_resumes")
    job_listing = relationship("JobListing", back_populates="custom_resumes")

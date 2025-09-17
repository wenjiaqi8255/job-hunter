"""
工作匹配相关API
对应Django的main_views.py中的核心匹配逻辑
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ....core.database import get_db
from ....schemas import (
    MatchSession, MatchSessionCreate, MatchSessionResponse,
    MatchedJob, JobMatchResponse
)
from ....models import (
    MatchSession as MatchSessionModel,
    MatchedJob as MatchedJobModel,
    JobListing as JobListingModel,
    UserProfile as UserProfileModel
)

router = APIRouter()

@router.post("/sessions", response_model=MatchSession)
async def create_match_session(
    session_data: MatchSessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    创建新的匹配会话
    对应Django的start_new_match_session
    """
    # 检查用户是否有完整的CV信息
    if session_data.user_id:
        user_profile = db.query(UserProfileModel).filter(
            UserProfileModel.user_id == session_data.user_id
        ).first()
        
        if not user_profile or not user_profile.user_cv_text:
            raise HTTPException(
                status_code=400,
                detail="Please complete your profile with a CV before starting a match"
            )
    
    # 创建匹配会话
    session_dict = session_data.dict()
    new_session = MatchSessionModel(**session_dict)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # 后台任务：执行实际的工作匹配
    background_tasks.add_task(
        perform_job_matching,
        session_id=new_session.id,
        db_session=db
    )
    
    return new_session

@router.get("/sessions", response_model=List[MatchSession])
async def get_user_match_sessions(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取用户的匹配历史
    对应Django的all_matches_page
    """
    sessions = db.query(MatchSessionModel).filter(
        MatchSessionModel.user_id == user_id
    ).order_by(MatchSessionModel.matched_at.desc()).offset(skip).limit(limit).all()
    
    return sessions

@router.get("/sessions/{session_id}", response_model=MatchSessionResponse)
async def get_match_session_detail(
    session_id: UUID,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取特定匹配会话的详情
    对应Django的_handle_session_view_get
    """
    # 构建查询条件
    query = db.query(MatchSessionModel).filter(MatchSessionModel.id == str(session_id))
    if user_id:
        query = query.filter(MatchSessionModel.user_id == user_id)
    
    session = query.first()
    if not session:
        raise HTTPException(status_code=404, detail="Match session not found")
    
    # 获取匹配的工作
    matched_jobs = db.query(MatchedJobModel).filter(
        MatchedJobModel.match_session_id == str(session_id)
    ).join(JobListingModel).order_by(MatchedJobModel.score.desc()).all()
    
    # 构建响应
    job_matches = []
    for matched_job in matched_jobs:
        job_match = JobMatchResponse(
            job_object=matched_job.job_listing,
            reason=matched_job.reason,
            score=matched_job.score,
            tips=matched_job.tips,
            parsed_tips_list=parse_tips_string(matched_job.tips) if matched_job.tips else [],
            parsed_insights_list=parse_insights_string(matched_job.insights) if matched_job.insights else [],
            job_anomalies=[],  # 需要从Supabase获取
            saved_status=None  # 需要查询SavedJob状态
        )
        job_matches.append(job_match)
    
    return MatchSessionResponse(
        session=session,
        matched_jobs=job_matches,
        total_matches=len(job_matches)
    )

@router.delete("/sessions/{session_id}")
async def delete_match_session(
    session_id: UUID,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    删除匹配会话
    """
    session = db.query(MatchSessionModel).filter(
        MatchSessionModel.id == str(session_id),
        MatchSessionModel.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Match session not found")
    
    # 删除关联的匹配工作
    db.query(MatchedJobModel).filter(
        MatchedJobModel.match_session_id == str(session_id)
    ).delete()
    
    # 删除会话
    db.delete(session)
    db.commit()
    
    return {"message": "Match session deleted successfully"}

# ========== 辅助函数 ==========
async def perform_job_matching(session_id: str, db_session: Session):
    """
    执行实际的工作匹配逻辑
    对应Django的gemini_utils.match_jobs
    """
    # 这里应该调用AI服务进行匹配
    # 暂时跳过实际的AI调用，直接返回模拟结果
    pass

def parse_tips_string(tips: str) -> List[str]:
    """解析tips字符串为列表"""
    if not tips:
        return []
    return [tip.strip() for tip in tips.split('\n') if tip.strip()]

def parse_insights_string(insights: str) -> List[str]:
    """解析insights字符串为列表"""
    if not insights:
        return []
    return [insight.strip() for insight in insights.split('\n') if insight.strip()]

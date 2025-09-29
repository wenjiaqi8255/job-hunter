"""
工作匹配相关API
对应Django的main_views.py中的核心匹配逻辑
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from uuid import UUID
import time
import json
from datetime import datetime

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
from ....services import ai_service, supabase_service
from ....services.mock_data_service import get_mock_job_listings, create_mock_matched_jobs, get_mock_anomaly_analysis

router = APIRouter()

from sqlalchemy import text

@router.get('/debug/users')
async def debug_users(db: Session = Depends(get_db)):
    users = db.execute(text('SELECT * FROM auth_user')).fetchall()
    return [dict(row) for row in users]

@router.get('/debug/profiles')
async def debug_profiles(db: Session = Depends(get_db)):
    profiles = db.execute(text('SELECT * FROM matcher_userprofile')).fetchall()
    return [dict(row) for row in profiles]

@router.get('/debug/profile/{user_id}')
async def debug_profile(user_id: int, db: Session = Depends(get_db)):
    result = db.execute(text('SELECT * FROM matcher_userprofile WHERE user_id = :uid'), {'uid': str(user_id)}).fetchone()
    return dict(result) if result else None
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

        # 检查防抖机制
        if not _check_rate_limit(session_data.user_id):
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {_match_cooldown_seconds} seconds before starting another match"
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
    
    # 获取异常分析数据
    # 对于开发环境，直接使用job_listing.id
    job_ids = [str(job.job_listing.id) for job in matched_jobs if job.job_listing.id]
    anomaly_data_map = {}
    if job_ids:
        supabase = supabase_service.create_supabase_client()
        if supabase:
            anomaly_data_map = supabase_service.fetch_anomaly_analysis_for_jobs_from_supabase(supabase, job_ids)
        else:
            # 使用模拟异常分析数据
            anomaly_data_map = get_mock_anomaly_analysis(job_ids)

    # 构建响应
    job_matches = []
    for matched_job in matched_jobs:
        # 解析异常分析数据
        job_anomalies = []
        if matched_job.job_listing.id:
            anomaly_data = anomaly_data_map.get(str(matched_job.job_listing.id))
            if anomaly_data and anomaly_data.get('anomaly_analysis'):
                anomaly_json = anomaly_data['anomaly_analysis']
                try:
                    if isinstance(anomaly_json, str):
                        anomaly_json = json.loads(anomaly_json)

                    if anomaly_json.get('semantic_anomalies'):
                        for anomaly in anomaly_json['semantic_anomalies']:
                            job_anomalies.append({
                                'type': anomaly.get('type', 'Unknown'),
                                'chunk': anomaly.get('chunk', ''),
                                'similarity_to_role': anomaly.get('similarity_to_role', 0),
                                'similarity_to_global': anomaly.get('similarity_to_global', 0),
                                'similarity_to_industry': anomaly.get('similarity_to_industry', 0)
                            })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"WARNING: Could not parse anomaly data for job {matched_job.job_listing.supabase_id}: {e}")

        job_match = JobMatchResponse(
            job_object=matched_job.job_listing,
            reason=matched_job.reason,
            score=matched_job.score,
            tips=matched_job.tips,
            parsed_tips_list=parse_tips_string(matched_job.tips) if matched_job.tips else [],
            parsed_insights_list=parse_insights_string(matched_job.insights) if matched_job.insights else [],
            job_anomalies=job_anomalies,
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
# 防抖缓存 - 防止用户短时间内重复请求
_last_match_time = {}
_match_cooldown_seconds = 30  # 30秒防抖，与Django保持一致

def _check_rate_limit(user_id: int) -> bool:
    """检查用户是否在防抖期内"""
    if user_id in _last_match_time:
        time_since_last = time.time() - _last_match_time[user_id]
        if time_since_last < _match_cooldown_seconds:
            return False
    return True

def _update_last_match_time(user_id: int):
    """更新用户最后一次匹配时间"""
    _last_match_time[user_id] = time.time()

def _save_matches_to_db(db_session: Session, matches: List[Dict], session: MatchSessionModel):
    """保存匹配结果到数据库"""
    try:
        for match in matches:
            # 获取或创建工作职位记录
            # 对于开发环境，直接使用id字段查找
            job_listing = db_session.query(JobListingModel).filter(
                JobListingModel.id == str(match['job'].get('id'))
            ).first()

            if not job_listing:
                print(f"WARNING: Job listing with id {match['job'].get('id')} not found, skipping")
                continue

            # 创建匹配记录
            matched_job = MatchedJobModel(
                match_session_id=session.id,
                job_listing_id=job_listing.id,
                score=match['score'],
                reason=match['reason'],
                insights=match.get('insights', ''),
                tips=match.get('tips', '')
            )
            db_session.add(matched_job)

        # 更新会话状态
        session.matched_at = datetime.now()
        db_session.commit()
        return True
    except Exception as e:
        print(f"ERROR: Failed to save matches to database: {e}")
        db_session.rollback()
        return False

async def perform_job_matching(session_id: str, db_session: Session):
    """
    执行实际的工作匹配逻辑
    对应Django的gemini_utils.match_jobs
    """
    try:
        # 获取匹配会话
        session = db_session.query(MatchSessionModel).filter(
            MatchSessionModel.id == session_id
        ).first()

        if not session:
            print(f"ERROR: Session {session_id} not found")
            return

        # 检查防抖
        if session.user_id and not _check_rate_limit(session.user_id):
            print(f"WARNING: User {session.user_id} is in cooldown period")
            return

        # 使用AI服务提取用户个人资料
        structured_profile = ai_service.extract_user_profile(
            session.skills_text,
            session.user_preferences_text
        )

        # 从Supabase获取今日工作职位，如果未配置则使用数据库中的数据
        supabase = supabase_service.create_supabase_client()
        if not supabase:
            print("WARNING: Supabase not configured - using database data for development")
            # 直接使用数据库中的工作职位数据
            job_listings = get_mock_job_listings(db_session)
            if not job_listings:
                print("ERROR: No job listings available in database")
                return

            # 使用AI服务进行工作匹配（会使用模拟模式）
            matches = ai_service.match_jobs(
                structured_profile,
                job_listings,
                max_jobs_to_process=36  # 与Django保持一致
            )

            # 保存匹配结果到数据库
            success = _save_matches_to_db(db_session, matches, session)
        else:
            # 正常流程：从Supabase获取今日工作职位
            job_listings = supabase_service.fetch_todays_job_listings_from_supabase(supabase)
            if not job_listings:
                print("INFO: No job listings found for today")
                return

            # 使用AI服务进行工作匹配
            matches = ai_service.match_jobs(
                structured_profile,
                job_listings,
                max_jobs_to_process=36  # 与Django保持一致
            )

            # 保存匹配结果到数据库
            success = _save_matches_to_db(db_session, matches, session)

        if success:
            print(f"SUCCESS: Completed job matching for session {session_id} with {len(matches)} matches")
            # 更新防抖时间
            if session.user_id:
                _update_last_match_time(session.user_id)
        else:
            print(f"ERROR: Failed to save matches for session {session_id}")

    except Exception as e:
        print(f"ERROR: Job matching failed for session {session_id}: {e}")

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

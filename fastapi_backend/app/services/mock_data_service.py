"""
Mock数据服务 - 为开发环境提供模拟数据
当Supabase未配置时，使用数据库中的现有数据进行匹配
"""
import json
import random
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ..models import JobListing, MatchedJob, UserProfile


def get_mock_job_listings(db: Session, limit: int = 50) -> List[Dict]:
    """从数据库获取工作职位列表，转换为模拟数据格式"""
    try:
        # 从数据库获取现有的工作职位
        job_listings = db.query(JobListing).limit(limit).all()

        if not job_listings:
            print("WARNING: No job listings found in database for mock data")
            return []

        # 转换为字典格式，模拟Supabase数据结构
        mock_jobs = []
        for job in job_listings:
            job_dict = {
                'id': job.id,
                'job_title': job.job_title,
                'company_name': job.company_name,
                'location': job.location,
                'description': job.description,
                'industry': job.industry,
                'salary_range': job.salary_range,
                'level': job.level,
                'flexibility': job.flexibility,
                'application_url': job.application_url,
                'created_at': job.created_at.isoformat() if job.created_at else None,
            }
            mock_jobs.append(job_dict)

        print(f"INFO: Mock data service returning {len(mock_jobs)} job listings from database")
        return mock_jobs

    except Exception as e:
        print(f"ERROR: Failed to get mock job listings: {e}")
        return []


def create_mock_matched_jobs(db: Session, session_id: str, user_id: int, job_listings: List[Dict]) -> List[MatchedJob]:
    """为匹配会话创建模拟匹配工作"""
    try:
        matched_jobs = []

        # 获取用户档案信息用于匹配逻辑
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        # 为每个工作职位创建匹配结果
        for job in job_listings[:20]:  # 限制最多20个
            # 基于简单的匹配逻辑生成分数
            base_score = random.randint(60, 95)

            # 根据用户偏好调整分数
            if user_profile and user_profile.user_preferences_text:
                prefs_text = user_profile.user_preferences_text.lower()
                if 'munich' in prefs_text and 'munich' in job.get('location', '').lower():
                    base_score += 5
                if 'remote' in prefs_text and 'remote' in job.get('location', '').lower():
                    base_score += 3

            score = min(100, base_score)

            # 创建匹配原因
            reasons = ["Mock match based on database data"]
            if user_profile:
                if 'python' in user_profile.user_cv_text.lower() and 'python' in job.get('job_title', '').lower():
                    reasons.append("Good Python skill alignment")
                if 'munich' in job.get('location', '').lower():
                    reasons.append("Location matches preference")

            reason = " | ".join(reasons) if reasons else "Mock match"

            # 创建见解和建议
            insights = f"Mock insights for {job.get('job_title', 'this position')}"
            tips = f"Mock tips: Highlight relevant skills for this role"

            # 创建匹配的工作记录
            matched_job = MatchedJob(
                match_session_id=session_id,
                job_listing_id=job.get('id'),
                score=score,
                reason=reason,
                insights=insights,
                tips=tips
            )

            matched_jobs.append(matched_job)

        # 批量保存到数据库
        if matched_jobs:
            db.add_all(matched_jobs)
            db.commit()
            print(f"INFO: Created {len(matched_jobs)} mock matched jobs for session {session_id}")

        return matched_jobs

    except Exception as e:
        print(f"ERROR: Failed to create mock matched jobs: {e}")
        db.rollback()
        return []


def get_mock_anomaly_analysis(job_ids: List[str]) -> Dict[str, Dict]:
    """生成模拟异常分析数据"""
    try:
        anomaly_data = {}

        for job_id in job_ids:
            # 创建模拟异常分析数据
            anomaly_data[job_id] = {
                'role': 'Software Engineer',
                'job_id': job_id,
                'industry': 'Technology',
                'job_title': 'Software Engineer',
                'company_name': 'Mock Company',
                'anomaly_analysis': json.dumps({
                    'semantic_anomalies': [
                        {
                            'type': 'Skill Gap',
                            'chunk': 'Mock anomaly chunk',
                            'similarity_to_role': 0.75,
                            'similarity_to_global': 0.65,
                            'similarity_to_industry': 0.80
                        }
                    ]
                })
            }

        print(f"INFO: Generated mock anomaly analysis for {len(job_ids)} jobs")
        return anomaly_data

    except Exception as e:
        print(f"ERROR: Failed to generate mock anomaly analysis: {e}")
        return {}
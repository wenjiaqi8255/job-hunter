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

        # 获取用户技能和偏好
        user_skills = []
        user_preferences = []
        if user_profile:
            if user_profile.user_cv_text:
                # 简单提取技能
                user_skills = [skill.strip() for skill in user_profile.user_cv_text.lower().split(',') if skill.strip()]
            if user_profile.user_preferences_text:
                user_preferences = [pref.strip() for pref in user_profile.user_preferences_text.lower().split(',') if pref.strip()]

        # 为每个工作职位创建匹配结果
        for i, job in enumerate(job_listings[:20]):  # 限制最多20个
            # 基于详细的匹配逻辑生成分数
            base_score = random.randint(60, 95)

            job_title = job.get('job_title', '').lower()
            job_location = job.get('location', '').lower()
            job_industry = job.get('industry', '').lower()
            company_name = job.get('company_name', '').lower()
            job_description = job.get('description', '').lower()

            # 技能匹配加分
            skill_matches = []
            for skill in user_skills:
                if skill in job_title or skill in job_description:
                    skill_matches.append(skill)
                    base_score += len(skill_matches) * 2

            # 位置匹配加分
            location_match = False
            for pref in user_preferences:
                if pref in job_location:
                    base_score += 5
                    location_match = True
                    break

            # 远程工作加分
            if 'remote' in user_preferences and 'remote' in job_location:
                base_score += 3

            # 行业匹配加分
            for pref in user_preferences:
                if pref in job_industry:
                    base_score += 2
                    break

            score = min(100, base_score)

            # 创建详细的匹配原因
            reason_parts = []
            if skill_matches:
                reason_parts.append(f"Strong alignment with your skills: {', '.join(skill_matches[:3])}")
            if location_match:
                reason_parts.append(f"Location preference match: {job.get('location', '')}")
            if 'remote' in job_location and 'remote' in user_preferences:
                reason_parts.append("Remote work option available")
            if score >= 85:
                reason_parts.append("Excellent overall fit for your profile")
            elif score >= 75:
                reason_parts.append("Good match with potential for growth")

            reason = ". ".join(reason_parts) + "." if reason_parts else "General position match based on your profile."

            # 创建结构化的见解（包含Pro:和Con:项目）
            insights_parts = []

            # Pros (优点)
            pros = []
            if skill_matches:
                pros.append(f"Your {', '.join(skill_matches[:2])} skills align well with requirements")
            if score >= 80:
                pros.append("Strong overall match with your experience level")
            if 'remote' in job_location:
                pros.append("Offers flexible work arrangements")
            if 'munich' in job_location and any('munich' in pref for pref in user_preferences):
                pros.append("Preferred location match")

            # Cons (缺点)
            cons = []
            if not skill_matches:
                cons.append("May require additional skill development")
            if score < 75:
                cons.append("Could be stretch position - consider skill gaps")
            if job_location and not any(loc in job_location for loc in ['munich', 'remote', 'berlin'] if any(loc in pref for pref in user_preferences)):
                cons.append(f"Location ({job.get('location', '')}) may not match preferences")
            if not job_description:
                cons.append("Limited job description available for detailed assessment")

            # 构建insights字符串
            insights_items = []
            for pro, con in zip(pros, cons):
                if pro:
                    insights_items.append(f"Pro: {pro}")
                if con:
                    insights_items.append(f"Con: {con}")

            # 添加未配对的pros或cons
            remaining_pros = pros[len(cons):] if len(pros) > len(cons) else []
            remaining_cons = cons[len(pros):] if len(cons) > len(pros) else []

            for pro in remaining_pros:
                insights_items.append(f"Pro: {pro}")
            for con in remaining_cons:
                insights_items.append(f"Con: {con}")

            insights = "\n".join(insights_items) if insights_items else "Pro: Standard position fit.\nCon: Review job requirements carefully."

            # 创建详细的建议（使用*分隔）
            tips_parts = []
            if skill_matches:
                tips_parts.append(f"Highlight your {', '.join(skill_matches[:2])} experience in your application")
            tips_parts.append(f"Research {company_name.title()} to tailor your application")
            if score >= 80:
                tips_parts.append("Apply promptly as this is a strong match")
            else:
                tips_parts.append("Consider if you meet most qualifications before applying")
            tips_parts.append("Prepare specific examples from your experience that relate to this role")
            if 'remote' in job_location:
                tips_parts.append("Emphasize your remote work experience and communication skills")

            tips = "\n".join(tips_parts) if tips_parts else "Standard application advice.\nResearch the company and role thoroughly."

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
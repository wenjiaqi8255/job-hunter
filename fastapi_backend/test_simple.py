#!/usr/bin/env python3
"""
简单测试：验证匹配功能的核心逻辑
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.mock_data_service import get_mock_job_listings
from app.services.ai_service import match_jobs
from app.api.v1.endpoints.matching import _save_matches_to_db
from app.models import MatchSession, MatchedJob

def test_matching_logic():
    """测试匹配逻辑"""
    print("🧪 测试匹配逻辑...")

    db = SessionLocal()
    try:
        # 1. 获取模拟工作职位
        print("\n1. 获取模拟工作职位...")
        job_listings = get_mock_job_listings(db, limit=10)
        print(f"✅ 获取到 {len(job_listings)} 个工作职位")

        # 2. 创建模拟用户档案
        print("\n2. 创建模拟用户档案...")
        user_profile = {
            "summary": "Experienced Python developer",
            "key_skills": ["Python", "Django", "JavaScript"],
            "experience_level": "Mid-Level",
            "preferences": {
                "desired_roles": ["Software Developer"],
                "location_preferences": ["Munich", "Remote"]
            }
        }

        # 3. 执行匹配
        print("\n3. 执行匹配...")
        matches = match_jobs(user_profile, job_listings)
        print(f"✅ 匹配完成，得到 {len(matches)} 个结果")

        if matches:
            print("   前3个匹配结果:")
            for i, match in enumerate(matches[:3]):
                print(f"     {i+1}. {match['job']['job_title']} @ {match['job']['company_name']} - 分数: {match['score']}")

        # 4. 创建测试会话
        print("\n4. 创建测试会话...")
        session = MatchSession(
            user_id=1,
            skills_text="Python, Django, JavaScript",
            user_preferences_text="Munich, Remote"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"✅ 创建会话: {session.id}")

        # 5. 保存匹配结果
        print("\n5. 保存匹配结果...")
        success = _save_matches_to_db(db, matches, session)
        if success:
            print(f"✅ 成功保存匹配结果")

            # 6. 验证结果
            print("\n6. 验证数据库结果...")
            count = db.query(MatchedJob).filter(MatchedJob.match_session_id == session.id).count()
            print(f"✅ 数据库中有 {count} 个匹配记录")

            # 显示前几个匹配结果
            saved_jobs = db.query(MatchedJob).filter(MatchedJob.match_session_id == session.id).limit(3).all()
            print("   数据库中的前3个匹配:")
            for i, job in enumerate(saved_jobs):
                print(f"     {i+1}. 分数: {job.score}, 原因: {job.reason[:50]}...")

        else:
            print("❌ 保存匹配结果失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_matching_logic()
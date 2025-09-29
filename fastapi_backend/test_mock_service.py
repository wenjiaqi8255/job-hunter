#!/usr/bin/env python3
"""
测试mock数据服务
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.mock_data_service import get_mock_job_listings, create_mock_matched_jobs
from app.models import MatchSession, MatchedJob
from sqlalchemy import text

def test_mock_service():
    """测试mock数据服务"""
    print("🧪 测试Mock数据服务...")

    db = SessionLocal()
    try:
        # 1. 测试获取工作职位
        print("\n1. 测试获取工作职位...")
        job_listings = get_mock_job_listings(db, limit=5)
        print(f"✅ 获取到 {len(job_listings)} 个工作职位")
        if job_listings:
            print(f"   示例: {job_listings[0]['job_title']} @ {job_listings[0]['company_name']}")

        # 2. 创建一个测试会话
        print("\n2. 创建测试会话...")
        session = MatchSession(
            user_id=1,
            skills_text="Python, Django, JavaScript",
            user_preferences_text="Munich, Remote"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"✅ 创建会话: {session.id}")

        # 3. 测试创建匹配工作
        print("\n3. 测试创建匹配工作...")
        matched_jobs = create_mock_matched_jobs(db, session.id, 1, job_listings)
        print(f"✅ 创建了 {len(matched_jobs)} 个匹配工作")

        # 4. 验证数据库中的结果
        print("\n4. 验证数据库结果...")
        count = db.query(MatchedJob).filter(MatchedJob.match_session_id == session.id).count()
        print(f"✅ 数据库中有 {count} 个匹配记录")

        # 5. 清理测试数据
        print("\n5. 清理测试数据...")
        db.query(MatchedJob).filter(MatchedJob.match_session_id == session.id).delete()
        db.query(MatchSession).filter(MatchSession.id == session.id).delete()
        db.commit()
        print("✅ 清理完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_mock_service()
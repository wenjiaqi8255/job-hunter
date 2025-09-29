#!/usr/bin/env python3
"""
直接测试API端点
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.api.v1.endpoints.matching import get_match_session_detail
from app.models import MatchSession as MatchSessionModel
from uuid import UUID

def test_get_session_detail():
    """测试获取会话详情"""
    print("🧪 测试获取会话详情...")

    db = SessionLocal()
    try:
        # 获取一个有匹配结果的会话
        from uuid import UUID
        session_id = UUID('453fdb0a-9d30-4096-bc31-4e90aadb17bd')
        session = db.query(MatchSessionModel).filter(MatchSessionModel.id == str(session_id)).first()
        if not session:
            print("❌ 没有找到匹配会话")
            return

        print(f"📋 测试会话: {session.id}")
        print(f"   用户ID: {session.user_id}")
        print(f"   已匹配: {session.matched_at is not None}")

        # 直接调用异步函数
        result = asyncio.run(get_match_session_detail(session_id, 1, db))
        print(f"✅ 函数调用成功")
        print(f"   匹配工作数: {result.total_matches}")

        if result.matched_jobs:
            print(f"   前3个匹配:")
            for i, job in enumerate(result.matched_jobs[:3]):
                print(f"     {i+1}. {job.job_object.job_title} @ {job.job_object.company_name}")
                print(f"        分数: {job.score}")
                print(f"        原因: {job.reason[:50]}...")
                if job.parsed_insights_list:
                    print(f"        见解: {job.parsed_insights_list[0][:50]}...")
                if job.parsed_tips_list:
                    print(f"        建议: {job.parsed_tips_list[0][:50]}...")
                if job.job_anomalies:
                    print(f"        异常数: {len(job.job_anomalies)}")
                print()

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_get_session_detail()
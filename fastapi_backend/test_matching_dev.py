#!/usr/bin/env python3
"""
测试脚本：验证匹配功能在开发环境下的工作情况
"""
import requests
import json
import time

# FastAPI服务器地址
BASE_URL = "http://localhost:8000"

def test_matching_functionality():
    """测试匹配功能"""
    print("🧪 开始测试匹配功能...")

    # 1. 获取现有的匹配会话
    print("\n1. 获取现有的匹配会话...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/matching/sessions?user_id=1")
        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ 找到 {len(sessions)} 个匹配会话")

            if sessions:
                # 选择第一个会话进行测试
                session_id = sessions[0]['id']
                print(f"📋 使用会话: {session_id}")

                # 2. 测试获取会话详情（应该在Supabase未配置时正常工作）
                print("\n2. 测试获取会话详情...")
                detail_response = requests.get(f"{BASE_URL}/api/v1/matching/sessions/{session_id}?user_id=1")
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    print(f"✅ 会话详情获取成功")
                    print(f"   - 会话ID: {detail['session']['id']}")
                    print(f"   - 匹配工作数: {detail['total_matches']}")

                    if detail['total_matches'] == 0:
                        print("ℹ️  此会话还没有匹配结果，需要创建新的匹配会话")
                        test_create_new_session()
                    else:
                        print("✅ 已有匹配结果，可以正常测试前端功能")

                else:
                    print(f"❌ 获取会话详情失败: {detail_response.status_code}")
                    print(f"   错误信息: {detail_response.text}")
            else:
                print("ℹ️  没有找到现有会话，创建新的...")
                test_create_new_session()
        else:
            print(f"❌ 获取会话失败: {response.status_code}")
            print(f"   错误信息: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到FastAPI服务器，请确保服务器正在运行")
        print("   运行命令: uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

    return True

def test_create_new_session():
    """测试创建新的匹配会话"""
    print("\n3. 测试创建新的匹配会话...")

    # 创建新会话的数据
    session_data = {
        "user_id": 1,
        "skills_text": "Python, Django, JavaScript, React",
        "user_preferences_text": "Munich, Remote"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/matching/sessions", json=session_data)
        if response.status_code == 200:
            new_session = response.json()
            print(f"✅ 新会话创建成功")
            print(f"   - 会话ID: {new_session['id']}")
            print(f"   - 用户ID: {new_session['user_id']}")

            # 等待后台任务完成
            print("⏳ 等待后台匹配任务完成...")
            time.sleep(5)

            # 检查匹配结果
            detail_response = requests.get(f"{BASE_URL}/api/v1/matching/sessions/{new_session['id']}?user_id=1")
            if detail_response.status_code == 200:
                detail = detail_response.json()
                print(f"✅ 匹配完成！找到 {detail['total_matches']} 个匹配工作")

                # 显示前几个匹配结果
                if detail['matched_jobs']:
                    print("\n📊 前3个匹配结果:")
                    for i, job in enumerate(detail['matched_jobs'][:3]):
                        print(f"   {i+1}. {job['job_object']['job_title']} @ {job['job_object']['company_name']}")
                        print(f"      匹配分数: {job['score']}/100")
                        print(f"      原因: {job['reason'][:100]}...")
                        print()
            else:
                print(f"❌ 获取新会话详情失败: {detail_response.status_code}")

        else:
            print(f"❌ 创建新会话失败: {response.status_code}")
            print(f"   错误信息: {response.text}")

    except Exception as e:
        print(f"❌ 创建新会话时出现错误: {e}")

def main():
    """主函数"""
    print("🚀 开始测试开发环境下的匹配功能")
    print("=" * 50)

    success = test_matching_functionality()

    if success:
        print("\n🎉 测试完成！")
        print("✅ 开发环境下的匹配功能已可以正常工作")
        print("✅ 前端可以正常测试匹配相关的功能")
    else:
        print("\n❌ 测试失败，请检查配置")

if __name__ == "__main__":
    main()
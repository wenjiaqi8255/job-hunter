#!/bin/bash

echo "🔍 测试前端API集成..."
echo ""

# 测试FastAPI后端是否运行
echo "1. 测试后端服务状态..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ FastAPI后端运行正常"
else
    echo "❌ FastAPI后端未运行，请先启动: poetry run uvicorn main:app --reload"
    exit 1
fi

echo ""
echo "2. 测试API端点..."

# 测试工作列表API
echo "📋 测试工作列表API..."
JOBS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/)
if [[ $JOBS_RESPONSE == *"job_title"* ]]; then
    echo "✅ 工作列表API正常"
    echo "   返回工作数量: $(echo $JOBS_RESPONSE | jq '. | length' 2>/dev/null || echo '多个')"
else
    echo "❌ 工作列表API异常"
fi

# 测试认证API
echo ""
echo "🔐 测试认证相关API..."
AUTH_ME_RESPONSE=$(curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer dummy_token")
if [[ $AUTH_ME_RESPONSE == *"detail"* ]] && [[ $AUTH_ME_RESPONSE == *"Not authenticated"* ]]; then
    echo "✅ 认证API正常 (正确拒绝无效token)"
else
    echo "⚠️  认证API响应异常"
fi

echo ""
echo "3. 检查前端服务..."
# 测试React前端是否运行
if curl -s http://localhost:5173/ > /dev/null; then
    echo "✅ React前端运行正常"
else
    echo "❌ React前端未运行，请先启动: npm run dev"
fi

echo ""
echo "4. 检查数据库数据..."
cd fastapi_backend
if poetry run python -c "
from app.core.database import SessionLocal
from app.models import User, JobListing
db = SessionLocal()
user_count = db.query(User).count()
job_count = db.query(JobListing).count()
db.close()
print(f'用户数: {user_count}, 工作数: {job_count}')
" 2>/dev/null; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 数据库连接异常"
fi

echo ""
echo "🎯 API集成测试建议:"
echo "1. 打开浏览器访问: http://localhost:5173"
echo "2. 测试以下页面:"
echo "   - 首页 (/) - 应显示推荐工作"
echo "   - 工作列表 (/jobs) - 应显示所有工作"
echo "   - 登录 (/login) - 测试认证功能"
echo "   - 匹配结果 (/matches) - 需要登录后测试"
echo "3. 查看浏览器控制台是否有API错误"
echo ""
echo "🔧 如有问题，检查:"
echo "- FastAPI日志: poetry run uvicorn main:app --reload"
echo "- React控制台: F12查看网络请求"
echo "- API文档: http://localhost:8000/docs"
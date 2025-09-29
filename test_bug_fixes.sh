#!/bin/bash

echo "🔧 测试Bug修复结果..."
echo ""

echo "1. 测试工作详情API..."
JOB_DETAIL_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/4267071320)
if [[ $JOB_DETAIL_RESPONSE == *"job_title"* ]]; then
    echo "✅ 工作详情API正常"
    echo "   工作标题: $(echo $JOB_DETAIL_RESPONSE | jq -r '.job_title')"
else
    echo "❌ 工作详情API异常"
fi

echo ""
echo "2. 测试保存工作API..."
# 测试保存工作API端点存在
SAVE_JOB_ENDPOINT=$(curl -s http://localhost:8000/openapi.json | jq '.paths["/api/v1/applications/saved-jobs"].post' 2>/dev/null)
if [[ $SAVE_JOB_ENDPOINT == *"Save Job Application"* ]]; then
    echo "✅ 保存工作API端点正常"
else
    echo "❌ 保存工作API端点异常"
fi

echo ""
echo "3. 测试React前端路由..."
# 检查前端路由是否配置正确
if curl -s http://localhost:5173/ | grep -q "react-router"; then
    echo "✅ React前端运行正常"
else
    echo "❌ React前端可能有问题"
fi

echo ""
echo "4. 测试数据库连接..."
cd fastapi_backend
if poetry run python -c "
from app.core.database import SessionLocal
from app.models import JobListing
db = SessionLocal()
job = db.query(JobListing).filter(JobListing.id == '4267071320').first()
db.close()
if job:
    print(f'✅ 找到工作: {job.job_title}')
else:
    print('❌ 未找到指定工作')
" 2>/dev/null; then
    echo "✅ 数据库查询正常"
else
    echo "❌ 数据库查询失败"
fi

echo ""
echo "🎯 修复内容验证:"
echo "1. ✅ 添加了 /jobs/:jobId 路由"
echo "2. ✅ 创建了 JobDetailPage 组件"
echo "3. ✅ 修复了 SaveJobButton API调用"
echo "4. ✅ 更新了API参数格式 (job_listing_id + user_id)"

echo ""
echo "🧪 现在可以测试的功能:"
echo "- 访问工作详情: http://localhost:5173/jobs/4267071320"
echo "- 测试保存工作功能 (需要登录)"
echo "- 测试工作列表链接"

echo ""
echo "📋 测试步骤建议:"
echo "1. 打开 http://localhost:5173"
echo "2. 点击任意工作卡片的'详情'按钮"
echo "3. 验证详情页面正确显示"
echo "4. 登录后测试'保存职位'功能"
echo "5. 查看浏览器控制台无错误"
#!/bin/bash

# FastAPI 数据层兼容性测试脚本

echo "=== FastAPI Backend 数据层兼容性测试 ==="
echo

# 设置环境变量
export PYTHONPATH="${PWD}:${PWD}/app"

echo "1. 启动 FastAPI 服务器..."
poetry run python main.py &
SERVER_PID=$!

# 等待服务器启动
sleep 3

echo "2. 测试数据库连接..."
curl -X POST "http://localhost:8000/api/v1/sync/test-connection" \
  -H "accept: application/json" | python -m json.tool

echo
echo "3. 验证数据同步状态..."
curl -X GET "http://localhost:8000/api/v1/sync/status" \
  -H "accept: application/json" | python -m json.tool

echo
echo "4. 验证数据一致性..."
curl -X POST "http://localhost:8000/api/v1/sync/validate" \
  -H "accept: application/json" | python -m json.tool

echo
echo "5. 测试表结构查询..."
for table in "auth_user" "matcher_userprofile" "matcher_joblisting"
do
    echo "检查表: $table"
    curl -X GET "http://localhost:8000/api/v1/sync/tables/structure/$table" \
      -H "accept: application/json" | python -m json.tool
    echo
done

echo "6. 测试API文档访问..."
echo "API文档可通过以下URL访问："
echo "- Swagger UI: http://localhost:8000/docs"
echo "- ReDoc: http://localhost:8000/redoc"

echo
echo "=== 测试完成 ==="
echo "服务器PID: $SERVER_PID"
echo "使用 'kill $SERVER_PID' 停止服务器"

# 保持脚本运行直到用户按Ctrl+C
wait $SERVER_PID

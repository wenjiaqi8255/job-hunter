#!/bin/bash

# FastAPI 开发服务器启动脚本

echo "Starting FastAPI development server..."

# 检查虚拟环境
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Warning: No virtual environment detected. Consider activating one."
fi

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# 检查环境变量文件
if [[ ! -f "../.env" ]]; then
    echo "Warning: .env file not found in parent directory"
    echo "Please create .env with required environment variables"
fi

# 启动服务器
echo "Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000

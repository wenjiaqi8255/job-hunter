# FastAPI + React 开发环境设置

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd job_hunting_django

# 安装Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
cd fastapi_backend
poetry install

# 激活虚拟环境
poetry shell
```

### 2. 数据库初始化

```bash
# 创建数据库表
alembic upgrade head

# 导入测试数据（从Django数据转换）
python init_development_data.py
```

### 3. 启动后端服务

```bash
# 启动FastAPI服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问API文档
# http://localhost:8000/docs
```

### 4. 启动前端服务

```bash
# 新终端窗口
cd react_frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问前端应用
# http://localhost:5173
```

## 📋 开发环境测试数据

### 测试用户
- **邮箱**: aries10011@outlook.com
- **用户名**: testuser
- **档案**: 包含完整的CV和偏好设置

### 功能测试流程
1. **用户认证** → 登录/注册功能
2. **资料管理** → 上传CV，设置偏好
3. **工作浏览** → 查看工作列表
4. **智能匹配** → 启动匹配算法
5. **申请管理** → 保存工作，生成求职信

## 🔧 常见问题

### 数据库连接失败
```bash
# 检查数据库文件是否存在
ls -la job_hunting.db

# 重新创建数据库
rm -f job_hunting.db
alembic upgrade head
python init_development_data.py
```

### 前端API连接失败
检查 `react_frontend/src/services/api_gen/core/OpenAPI.ts` 中的BASE配置：
```typescript
export const OpenAPI: OpenAPIConfig = {
    BASE: 'http://localhost:8000',
    VERSION: '1.0.0',
    WITH_CREDENTIALS: false,
    CREDENTIALS: 'include',
    TOKEN: undefined,
};
```

### 文件上传功能
确保CV文件路径正确，或者使用模拟数据进行测试。

## 🎯 开发原则

- **KISS**: 保持简单，不增加不必要的复杂性
- **SOLID**: 单一职责，开闭原则
- **YAGNI**: 不实现不需要的功能
# FastAPI Backend 重构文档

## 项目概述

这是Django项目向FastAPI的增量式重构版本，保持与原Django项目的数据结构和业务逻辑兼容。

## 重构原则

- **KISS原则**: 保持简单，不过度设计
- **YAGNI原则**: 只实现当前需要的功能
- **SOLID原则**: 单一职责，开闭原则，依赖倒置
- **MVP思路**: 优先实现核心功能，逐步完善

## 项目结构

```
fastapi_backend/
├── main.py                 # FastAPI应用入口
├── requirements.txt        # 项目依赖
├── start_dev.sh           # 开发服务器启动脚本
├── app/
│   ├── __init__.py
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   ├── database.py    # 数据库配置
│   │   └── __init__.py
│   ├── models/            # SQLAlchemy模型
│   │   └── __init__.py    # 对应Django models
│   ├── schemas/           # Pydantic schemas
│   │   └── __init__.py    # 请求/响应模型
│   ├── api/               # API路由
│   │   └── v1/
│   │       ├── api.py     # 路由聚合器
│   │       └── endpoints/ # 各功能模块API
│   │           ├── auth.py          # 认证API
│   │           ├── jobs.py          # 工作职位API
│   │           ├── matching.py      # 工作匹配API
│   │           ├── profiles.py      # 用户资料API
│   │           └── applications.py  # 求职申请API
│   └── services/          # 业务逻辑层
│       ├── ai_service.py       # AI服务(基于gemini_utils.py)
│       ├── supabase_service.py # Supabase服务
│       └── __init__.py
```

## 核心功能模块

### 1. 认证模块 (auth.py)
- 用户注册/登录/登出
- JWT token管理
- 用户信息获取
- 对应Django的auth_views.py

### 2. 工作职位模块 (jobs.py)
- 工作职位CRUD操作
- 工作搜索和过滤
- 行业/地区筛选
- 对应Django的job_views.py

### 3. 工作匹配模块 (matching.py)
- 创建匹配会话
- AI工作匹配逻辑
- 匹配历史管理
- 对应Django的main_views.py核心逻辑

### 4. 用户资料模块 (profiles.py)
- 用户个人资料管理
- CV文件上传
- 资料完整度评估
- 改进建议生成
- 对应Django的profile_views.py

### 5. 求职申请模块 (applications.py)
- 保存的工作管理
- 求职信生成
- 定制简历生成
- 申请状态跟踪
- PDF文件下载
- 对应Django的application_views.py

## 数据模型兼容性

### SQLAlchemy vs Django ORM映射

| Django模型 | SQLAlchemy模型 | 表名 | 说明 |
|-----------|---------------|------|------|
| User | User | auth_user | Django默认用户表 |
| UserProfile | UserProfile | matcher_userprofile | 用户个人资料 |
| JobListing | JobListing | matcher_joblisting | 工作职位信息 |
| MatchSession | MatchSession | matcher_matchsession | 匹配会话 |
| MatchedJob | MatchedJob | matcher_matchedjob | 匹配结果 |
| SavedJob | SavedJob | matcher_savedjob | 保存的工作 |
| CoverLetter | CoverLetter | matcher_coverletter | 求职信 |
| CustomResume | CustomResume | matcher_customresume | 定制简历 |

### 关键字段映射
- 保持Django的主键结构（如JobListing使用字符串ID）
- 保持Django的外键关系
- 保持Django的字段类型和约束
- UUID字段使用字符串存储保持兼容

## AI服务兼容性

### AI功能模块
1. **用户资料提取** (`extract_user_profile`)
   - 从CV文本提取结构化信息
   - 支持技能、经验、教育背景解析

2. **工作匹配** (`match_jobs`)
   - 基于结构化用户资料匹配工作
   - 生成匹配分数和原因
   - 提供申请建议和洞察

3. **求职信生成** (`generate_cover_letter`)
   - 基于用户技能和工作描述生成求职信
   - 个性化内容定制

4. **简历定制** (`generate_custom_resume`)
   - 针对特定工作优化简历内容
   - 保持原有格式和结构

### 模拟模式
- 支持AI模拟模式，用于开发和测试
- 通过`USE_SIMULATION_ENV`环境变量控制
- 模拟数据保持与真实API相同的数据结构

## Supabase集成

### 数据源
- 工作职位数据从Supabase获取
- 异常分析数据集成
- 保持与Django版本相同的Supabase表结构

### 主要功能
- 获取今日工作职位
- 工作异常分析数据
- 工作职位搜索和过滤

## 配置管理

### 环境变量
```env
# 基础配置
DEBUG=True
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=sqlite:///./job_hunting.db

# AI配置
USE_SIMULATION_ENV=True
GEMINI_API_KEY=your-gemini-api-key

# Supabase配置
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# OAuth配置
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 开发指南

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动开发服务器
```bash
# 使用启动脚本
./start_dev.sh

# 或直接使用uvicorn
uvicorn main:app --reload
```

### API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 数据库迁移
```bash
# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

## 重构进度

### ✅ 已完成
1. **项目骨架搭建**
   - FastAPI应用结构
   - 配置管理系统
   - 数据库连接配置

2. **数据模型层**
   - SQLAlchemy模型定义
   - Pydantic schemas定义
   - Django兼容的表结构

3. **API路由层**
   - 五大功能模块API设计
   - 请求/响应模型定义
   - 错误处理机制

4. **服务层**
   - AI服务模块重构
   - Supabase集成服务
   - 业务逻辑封装

### 🚧 下一步计划
1. **认证系统完善**
   - JWT token实现
   - OAuth集成
   - 权限控制

2. **数据库迁移**
   - Alembic配置
   - 数据迁移脚本
   - 兼容性测试

3. **集成测试**
   - API端点测试
   - 业务逻辑测试
   - 性能测试

4. **前端接口对接**
   - API规范文档
   - 错误码标准化
   - 响应格式统一

### 🔄 长期规划
1. **性能优化**
   - 数据库查询优化
   - 缓存机制
   - 异步处理

2. **监控和日志**
   - 应用监控
   - 错误追踪
   - 性能指标

3. **部署和CI/CD**
   - Docker化
   - 自动化部署
   - 环境隔离

## 注意事项

1. **数据一致性**: 确保与Django版本的数据结构完全兼容
2. **API兼容性**: 保持响应格式与前端期望一致
3. **错误处理**: 提供清晰的错误信息和状态码
4. **性能考虑**: 注意数据库查询效率和响应时间
5. **安全性**: 实现适当的认证和授权机制

## 贡献指南

1. 遵循现有代码风格和架构模式
2. 添加适当的类型注解和文档字符串
3. 编写单元测试覆盖新功能
4. 更新相关文档和API规范
5. 确保与Django版本的兼容性

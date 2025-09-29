"""
API v1版本路由聚合
对应Django的URL配置
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, jobs, matching, profiles, applications, sync

api_router = APIRouter()

# 注册所有路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(sync.router, prefix="/sync", tags=["data-sync"])

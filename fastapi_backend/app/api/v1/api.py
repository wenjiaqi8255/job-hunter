"""
API v1版本路由聚合
对应Django的URL配置
"""
from fastapi import APIRouter

from .endpoints import jobs, matching, auth, profiles, applications

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["user-profiles"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["job-listings"])
api_router.include_router(matching.router, prefix="/matching", tags=["job-matching"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])

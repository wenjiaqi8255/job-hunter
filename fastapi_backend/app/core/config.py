"""
应用配置管理
基于现有Django settings重构
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    app_name: str = "Job Hunting API"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    version: str = "1.0.0"
    
    # 数据库配置 - 初期使用SQLite保持兼容
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./job_hunting.db")
    
    # AI配置 - 对应Django的USE_AI_SIMULATION
    use_ai_simulation: bool = os.getenv("USE_SIMULATION_ENV", "True").lower() != "false"
    
    # Supabase配置
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # OAuth配置
    google_client_id: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # JWT配置
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 文件上传配置
    media_root: str = os.getenv("MEDIA_ROOT", "./media")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        case_sensitive = False

# 全局配置实例
settings = Settings()

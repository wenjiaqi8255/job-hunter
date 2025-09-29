"""
认证相关API
对应Django的auth_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ....core.database import get_db
from ....schemas import User, UserCreate
from ....models import User as UserModel

router = APIRouter()
security = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册
    对应Django的register_view
    """
    # 检查用户名是否已存在
    existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 创建新用户（简化版，生产环境需要密码哈希）
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password  # 注意：实际应用中需要哈希处理
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    对应Django的login视图
    """
    # 简化的认证逻辑，实际应用中需要JWT token
    user = db.query(UserModel).filter(
        UserModel.email == login_data.email
    ).first()

    if not user or user.password != login_data.password:  # 实际应用中需要验证哈希密码
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 返回用户信息和简单的session token（开发环境用）
    session_token = f"session_{user.id}"  # 简化的token，实际应用中应该使用JWT
    return {
        "message": "Login successful",
        "user_id": user.id,
        "session_token": session_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "date_joined": user.date_joined
        }
    }

@router.get("/me", response_model=User)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    对应Django的get_current_user_info
    """
    # 简化的用户验证，支持多种认证方式
    user = None

    # 方式1: 通过Bearer token（实际应用中应该使用JWT）
    if credentials:
        # 这里应该从JWT token中解析用户ID
        # 暂时返回第一个用户作为示例
        user = db.query(UserModel).first()

    # 方式2: 通过查询参数user_id（简化版）
    elif user_id:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

    # 方式3: 如果都没有认证，返回第一个用户（开发环境简化）
    else:
        user = db.query(UserModel).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.post("/logout")
async def logout():
    """
    用户登出
    对应Django的logout视图
    """
    return {"message": "Logout successful"}

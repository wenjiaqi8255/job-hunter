"""
认证相关API
对应Django的auth_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ....core.database import get_db
from ....schemas import User, UserCreate
from ....models import User as UserModel

router = APIRouter()
security = HTTPBearer(auto_error=False)

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
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    用户登录
    对应Django的login视图
    """
    # 简化的认证逻辑，实际应用中需要JWT token
    user = db.query(UserModel).filter(
        UserModel.username == username
    ).first()
    
    if not user or user.password != password:  # 实际应用中需要验证哈希密码
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 这里应该生成JWT token
    return {"message": "Login successful", "user_id": user.id}

@router.get("/me", response_model=User)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    对应Django的get_current_user_info
    """
    # 简化的用户验证，实际应用中需要JWT验证
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # 这里应该从JWT token中解析用户ID
    # 暂时返回第一个用户作为示例
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

"""
用户个人资料相关API
对应Django的profile_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os

from ....core.database import get_db
from ....core.config import settings
from ....schemas import UserProfile, UserProfileCreate, UserProfileUpdate
from ....models import UserProfile as UserProfileModel, User as UserModel

router = APIRouter()

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取用户个人资料
    对应Django的profile_page GET请求
    """
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        # 如果不存在则创建一个空的profile
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = UserProfileModel(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.post("/", response_model=UserProfile)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    创建用户个人资料
    """
    # 检查用户是否存在
    user = db.query(UserModel).filter(UserModel.id == profile_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查是否已有profile
    existing_profile = db.query(UserProfileModel).filter(
        UserProfileModel.user_id == profile_data.user_id
    ).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # 创建新profile
    profile_dict = profile_data.dict()
    new_profile = UserProfileModel(**profile_dict)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return new_profile

@router.put("/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    更新用户个人资料
    对应Django的profile_page POST请求
    """
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 更新字段
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.post("/{user_id}/upload-cv")
async def upload_cv_file(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传简历文件
    对应Django的CV文件上传逻辑
    """
    # 验证文件类型
    allowed_types = ['application/pdf', 'text/plain', 'application/msword']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Only PDF, TXT, and DOC files are allowed"
        )
    
    # 验证文件大小
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_file_size} bytes"
        )
    
    # 获取用户profile
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 保存文件
    upload_dir = os.path.join(settings.media_root, "user_cvs", str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 更新profile中的文件路径
    # 注意：这里简化处理，实际应用中可能需要提取文件内容到user_cv_text
    return {"message": "CV uploaded successfully", "file_path": file_path}

@router.delete("/{user_id}")
async def delete_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    删除用户个人资料
    """
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted successfully"}

@router.get("/{user_id}/tips")
async def get_improvement_tips(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取个人资料改进建议
    对应Django的tips_to_improve_page
    """
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 这里应该调用AI服务生成改进建议
    # 暂时返回模拟数据
    tips = [
        "Add more specific technical skills to your CV",
        "Include quantifiable achievements in your work experience", 
        "Update your CV with recent certifications or training",
        "Add keywords relevant to your target industry"
    ]
    
    return {"tips": tips, "profile_completeness": calculate_profile_completeness(profile)}

def calculate_profile_completeness(profile: UserProfileModel) -> float:
    """计算个人资料完整度"""
    total_fields = 3  # user_cv_text, user_preferences_text, user_email
    completed_fields = 0
    
    if profile.user_cv_text:
        completed_fields += 1
    if profile.user_preferences_text:
        completed_fields += 1
    if profile.user_email:
        completed_fields += 1
    
    return (completed_fields / total_fields) * 100

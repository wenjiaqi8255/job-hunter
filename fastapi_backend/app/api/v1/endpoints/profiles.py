"""
用户个人资料相关API
对应Django的profile_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import fitz  # PyMuPDF for PDF text extraction
import docx  # python-docx for DOCX files
import io

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
    allowed_types = ['application/pdf', 'text/plain', 'application/msword',
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, DOC, and DOCX files are allowed"
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
    
    # 读取文件内容
    content = await file.read()

    # 提取文本内容
    extracted_text = ""
    try:
        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(content)
        elif file.content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            extracted_text = extract_text_from_docx(content)
        elif file.content_type == 'text/plain':
            extracted_text = content.decode('utf-8')

        # 清理文本
        extracted_text = clean_extracted_text(extracted_text)

    except Exception as e:
        print(f"ERROR: Could not extract text from uploaded file: {e}")
        # 即使文本提取失败，也保存文件
        extracted_text = ""

    # 保存文件到磁盘
    upload_dir = os.path.join(settings.media_root, "user_cvs", str(user_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # 更新profile中的CV文本内容
    if extracted_text:
        profile.user_cv_text = extracted_text
        db.commit()
        db.refresh(profile)

    return {
        "message": "CV uploaded successfully",
        "file_path": file_path,
        "text_extracted": len(extracted_text) > 0,
        "text_length": len(extracted_text)
    }

# ========== 文本提取辅助函数 ==========
def extract_text_from_pdf(pdf_content: bytes) -> str:
    """使用PyMuPDF从PDF文件中提取文本"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"ERROR: PDF text extraction failed: {e}")
        return ""

def extract_text_from_docx(docx_content: bytes) -> str:
    """从DOCX文件中提取文本"""
    try:
        doc = docx.Document(io.BytesIO(docx_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"ERROR: DOCX text extraction failed: {e}")
        return ""

def clean_extracted_text(text: str) -> str:
    """清理提取的文本"""
    if not text:
        return ""

    # 移除多余的空白字符
    text = " ".join(text.split())

    # 移除特殊字符但保留基本的标点
    import re
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\@\#\$\%\^\&\*\+\=\~\`]', '', text)

    # 规范化换行
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 移除过多的空行
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)

    return text.strip()

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

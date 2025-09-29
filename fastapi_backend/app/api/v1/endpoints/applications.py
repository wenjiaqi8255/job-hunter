"""
求职申请相关API
对应Django的application_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import textwrap
from fastapi.exceptions import RequestValidationError
from fastapi import Request

from ....core.database import get_db
from ....schemas import (
    SavedJob, SavedJobCreate, SavedJobUpdate,
    CoverLetter, CoverLetterCreate, CoverLetterUpdate,
    CustomResume, CustomResumeCreate, CustomResumeUpdate,
    SavedJobStatus
)
from ....models import (
    SavedJob as SavedJobModel,
    CoverLetter as CoverLetterModel,
    CustomResume as CustomResumeModel,
    JobListing as JobListingModel,
    UserProfile as UserProfileModel
)
from ....services import ai_service

router = APIRouter()

# ========== SavedJob相关API ==========
@router.get("/saved-jobs", response_model=List[SavedJob])
async def get_user_saved_jobs(
    user_id: int,
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取用户保存的工作申请
    对应Django的my_applications_page
    """
    query = db.query(SavedJobModel).filter(SavedJobModel.user_id == user_id)
    
    # 状态过滤
    if status:
        query = query.filter(SavedJobModel.status == status)
    
    # 排序和分页
    saved_jobs = query.order_by(SavedJobModel.updated_at.desc()).offset(skip).limit(limit).all()
    return saved_jobs

@router.post("/saved-jobs", response_model=SavedJob)
async def save_job_application(
    job_data: SavedJobCreate,
    db: Session = Depends(get_db)
):
    """
    保存工作申请
    对应Django的job_detail_page POST请求
    """
    # 验证用户ID
    if not job_data.user_id or job_data.user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valid user ID is required"
        )

    # 检查工作是否存在
    job = db.query(JobListingModel).filter(JobListingModel.id == job_data.job_listing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")

    # 检查是否已经保存过
    existing_saved_job = db.query(SavedJobModel).filter(
        SavedJobModel.user_id == job_data.user_id,
        SavedJobModel.job_listing_id == job_data.job_listing_id
    ).first()

    if existing_saved_job:
        raise HTTPException(status_code=400, detail="Job already saved")

    try:
        # 创建新的保存记录
        saved_job_dict = job_data.dict()
        new_saved_job = SavedJobModel(**saved_job_dict)
        db.add(new_saved_job)
        db.commit()
        db.refresh(new_saved_job)

        return new_saved_job

    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to save job application: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save job application. Please try again."
        )

@router.put("/saved-jobs/{saved_job_id}", response_model=SavedJob)
async def update_saved_job_status(
    saved_job_id: int,
    job_data: SavedJobUpdate,
    db: Session = Depends(get_db)
):
    """
    更新保存工作的状态
    对应Django的update_job_application_status
    """
    saved_job = db.query(SavedJobModel).filter(SavedJobModel.id == saved_job_id).first()
    if not saved_job:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    # 更新字段
    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(saved_job, field, value)
    
    db.commit()
    db.refresh(saved_job)
    return saved_job

@router.delete("/saved-jobs/{saved_job_id}")
async def delete_saved_job(
    saved_job_id: int,
    db: Session = Depends(get_db)
):
    """
    删除保存的工作申请
    """
    saved_job = db.query(SavedJobModel).filter(SavedJobModel.id == saved_job_id).first()
    if not saved_job:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    db.delete(saved_job)
    db.commit()
    return {"message": "Saved job deleted successfully"}

# ========== CoverLetter相关API ==========
@router.post("/cover-letters", response_model=CoverLetter)
async def generate_cover_letter(
    cover_letter_data: CoverLetterCreate,
    db: Session = Depends(get_db)
):
    """
    生成求职信
    对应Django的generate_cover_letter_page
    """
    # 检查saved_job是否存在
    saved_job = db.query(SavedJobModel).filter(SavedJobModel.id == cover_letter_data.saved_job_id).first()
    if not saved_job:
        raise HTTPException(status_code=404, detail="Saved job not found")

    # 获取用户个人资料
    user_profile = db.query(UserProfileModel).filter(
        UserProfileModel.user_id == saved_job.user_id
    ).first()

    if not user_profile or not user_profile.user_cv_text:
        raise HTTPException(
            status_code=400,
            detail="User profile or CV not found. Please complete your profile first."
        )

    # 获取工作详情
    job = db.query(JobListingModel).filter(JobListingModel.id == saved_job.job_listing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")

    # 使用AI服务生成求职信内容
    try:
        # 提取用户技能（从CV中提取关键技能）
        skills_text = user_profile.user_cv_text

        # 构建工作信息字典
        job_dict = {
            'job_title': job.job_title,
            'company_name': job.company_name,
            'level': job.level,
            'description': job.description,
            'location': job.location,
            'industry': job.industry
        }

        # 调用AI服务生成求职信
        generated_content = ai_service.generate_cover_letter(skills_text, job_dict)

        # 检查是否已有求职信
        existing_cover_letter = db.query(CoverLetterModel).filter(
            CoverLetterModel.saved_job_id == cover_letter_data.saved_job_id
        ).first()

        if existing_cover_letter:
            # 更新现有求职信
            existing_cover_letter.content = generated_content
            db.commit()
            db.refresh(existing_cover_letter)
            return existing_cover_letter
        else:
            # 创建新求职信
            new_cover_letter = CoverLetterModel(
                saved_job_id=cover_letter_data.saved_job_id,
                content=generated_content
            )
            db.add(new_cover_letter)
            db.commit()
            db.refresh(new_cover_letter)
            return new_cover_letter

    except Exception as e:
        print(f"ERROR: Failed to generate cover letter: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate cover letter. Please try again later."
        )

@router.get("/cover-letters/{saved_job_id}", response_model=CoverLetter)
async def get_cover_letter(
    saved_job_id: int,
    db: Session = Depends(get_db)
):
    """
    获取求职信
    """
    cover_letter = db.query(CoverLetterModel).filter(
        CoverLetterModel.saved_job_id == saved_job_id
    ).first()
    
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    return cover_letter

@router.get("/cover-letters/{saved_job_id}/download")
async def download_cover_letter(
    saved_job_id: int,
    db: Session = Depends(get_db)
):
    """
    下载求职信PDF
    对应Django的download_cover_letter
    """
    cover_letter = db.query(CoverLetterModel).filter(
        CoverLetterModel.saved_job_id == saved_job_id
    ).first()
    
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    # 生成PDF
    pdf_buffer = generate_pdf_from_text(cover_letter.content, "Cover Letter")
    
    return StreamingResponse(
        BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cover_letter_{saved_job_id}.pdf"}
    )

# ========== CustomResume相关API ==========
@router.post("/custom-resumes", response_model=CustomResume)
async def generate_custom_resume(
    resume_data: CustomResumeCreate,
    db: Session = Depends(get_db)
):
    """
    生成定制简历
    对应Django的generate_custom_resume_page
    """
    # 获取用户个人资料
    user_profile = db.query(UserProfileModel).filter(
        UserProfileModel.user_id == resume_data.user_id
    ).first()

    if not user_profile or not user_profile.user_cv_text:
        raise HTTPException(
            status_code=400,
            detail="User profile or CV not found. Please complete your profile first."
        )

    # 获取工作详情
    job = db.query(JobListingModel).filter(JobListingModel.id == resume_data.job_listing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")

    # 使用AI服务生成定制简历内容
    try:
        # 构建工作信息字典
        job_dict = {
            'job_title': job.job_title,
            'company_name': job.company_name,
            'level': job.level,
            'description': job.description,
            'location': job.location,
            'industry': job.industry
        }

        # 调用AI服务生成定制简历
        generated_content = ai_service.generate_custom_resume(user_profile.user_cv_text, job_dict)

        # 检查是否已有定制简历
        existing_resume = db.query(CustomResumeModel).filter(
            CustomResumeModel.user_id == resume_data.user_id,
            CustomResumeModel.job_listing_id == resume_data.job_listing_id
        ).first()

        if existing_resume:
            # 更新现有简历
            existing_resume.content = generated_content
            db.commit()
            db.refresh(existing_resume)
            return existing_resume
        else:
            # 创建新简历
            new_resume = CustomResumeModel(
                user_id=resume_data.user_id,
                job_listing_id=resume_data.job_listing_id,
                content=generated_content
            )
            db.add(new_resume)
            db.commit()
            db.refresh(new_resume)
            return new_resume

    except Exception as e:
        print(f"ERROR: Failed to generate custom resume: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate custom resume. Please try again later."
        )

@router.get("/custom-resumes/{user_id}/{job_listing_id}", response_model=CustomResume)
async def get_custom_resume(
    user_id: int,
    job_listing_id: str,
    db: Session = Depends(get_db)
):
    """
    获取定制简历
    """
    custom_resume = db.query(CustomResumeModel).filter(
        CustomResumeModel.user_id == user_id,
        CustomResumeModel.job_listing_id == job_listing_id
    ).first()
    
    if not custom_resume:
        raise HTTPException(status_code=404, detail="Custom resume not found")
    
    return custom_resume

@router.get("/custom-resumes/{user_id}/{job_listing_id}/download")
async def download_custom_resume(
    user_id: int,
    job_listing_id: str,
    db: Session = Depends(get_db)
):
    """
    下载定制简历PDF
    对应Django的download_custom_resume
    """
    custom_resume = db.query(CustomResumeModel).filter(
        CustomResumeModel.user_id == user_id,
        CustomResumeModel.job_listing_id == job_listing_id
    ).first()
    
    if not custom_resume:
        raise HTTPException(status_code=404, detail="Custom resume not found")
    
    # 生成PDF
    pdf_buffer = generate_pdf_from_text(custom_resume.content, "Custom Resume")
    
    return StreamingResponse(
        BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=custom_resume_{job_listing_id}.pdf"}
    )

@router.get("/status-choices")
async def get_status_choices():
    """
    获取申请状态选项
    对应Django的SavedJob.STATUS_CHOICES
    """
    return {
        "status_choices": [
            {"value": "not_applied", "label": "Not Applied"},
            {"value": "viewed", "label": "Viewed"},
            {"value": "applied", "label": "Applied"},
            {"value": "interviewing", "label": "Interviewing"},
            {"value": "offer", "label": "Offer"},
            {"value": "rejected", "label": "Rejected"},
        ]
    }

# ========== 辅助函数 ==========
def generate_pdf_from_text(text: str, title: str = "Document") -> bytes:
    """
    使用reportlab从文本生成PDF
    对应Django的PDF生成逻辑
    """
    buffer = io.BytesIO()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # 获取样式
    styles = getSampleStyleSheet()

    # 创建自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # 居中
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leading=14
    )

    # 构建内容
    story = []

    # 添加标题
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))

    # 处理文本内容
    if text:
        # 将文本按段落分割
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            if paragraph.strip():
                # 清理文本并处理长段落
                cleaned_text = paragraph.strip()
                if len(cleaned_text) > 0:
                    # 使用textwrap处理长段落
                    wrapped_lines = textwrap.wrap(cleaned_text, width=80)
                    for line in wrapped_lines:
                        if line.strip():
                            story.append(Paragraph(line, normal_style))

                    # 段落间添加间距
                    story.append(Spacer(1, 6))

    # 构建PDF
    doc.build(story)

    # 获取PDF内容
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content

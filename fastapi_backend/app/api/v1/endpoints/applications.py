"""
求职申请相关API
对应Django的application_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO

from ....core.database import get_db
from ....schemas import (
    SavedJob, SavedJobCreate, SavedJobUpdate,
    CoverLetter, CoverLetterCreate, CoverLetterUpdate,
    CustomResume, CustomResumeCreate, CustomResumeUpdate
)
from ....models import (
    SavedJob as SavedJobModel,
    CoverLetter as CoverLetterModel,
    CustomResume as CustomResumeModel,
    JobListing as JobListingModel
)

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
    # 检查是否已经保存过
    existing_saved_job = db.query(SavedJobModel).filter(
        SavedJobModel.user_id == job_data.user_id,
        SavedJobModel.job_listing_id == job_data.job_listing_id
    ).first()
    
    if existing_saved_job:
        raise HTTPException(status_code=400, detail="Job already saved")
    
    # 创建新的保存记录
    saved_job_dict = job_data.dict()
    new_saved_job = SavedJobModel(**saved_job_dict)
    db.add(new_saved_job)
    db.commit()
    db.refresh(new_saved_job)
    
    return new_saved_job

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
    
    # 检查是否已有求职信
    existing_cover_letter = db.query(CoverLetterModel).filter(
        CoverLetterModel.saved_job_id == cover_letter_data.saved_job_id
    ).first()
    
    if existing_cover_letter:
        # 更新现有求职信
        existing_cover_letter.content = cover_letter_data.content
        db.commit()
        db.refresh(existing_cover_letter)
        return existing_cover_letter
    else:
        # 创建新求职信
        cover_letter_dict = cover_letter_data.dict()
        new_cover_letter = CoverLetterModel(**cover_letter_dict)
        db.add(new_cover_letter)
        db.commit()
        db.refresh(new_cover_letter)
        return new_cover_letter

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
    
    # 生成PDF（简化实现）
    pdf_buffer = generate_pdf_from_text(cover_letter.content)
    
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
    # 检查是否已有定制简历
    existing_resume = db.query(CustomResumeModel).filter(
        CustomResumeModel.user_id == resume_data.user_id,
        CustomResumeModel.job_listing_id == resume_data.job_listing_id
    ).first()
    
    if existing_resume:
        # 更新现有简历
        existing_resume.content = resume_data.content
        db.commit()
        db.refresh(existing_resume)
        return existing_resume
    else:
        # 创建新简历
        resume_dict = resume_data.dict()
        new_resume = CustomResumeModel(**resume_dict)
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume

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
    pdf_buffer = generate_pdf_from_text(custom_resume.content)
    
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
def generate_pdf_from_text(text: str) -> bytes:
    """
    从文本生成PDF
    简化实现，实际应用中应使用reportlab等库
    """
    # 这里应该使用reportlab生成PDF
    # 暂时返回模拟的PDF内容
    return b"PDF content placeholder"

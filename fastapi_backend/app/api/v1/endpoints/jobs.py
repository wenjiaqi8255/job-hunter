"""
工作职位相关API
对应Django的job_views.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ....core.database import get_db
from ....schemas import JobListing, JobListingCreate, JobListingUpdate
from ....models import JobListing as JobListingModel

router = APIRouter()

@router.get("/", response_model=List[JobListing])
async def get_all_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    industry: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取所有工作职位列表
    对应Django main_views中的all_jobs_annotated逻辑
    """
    query = db.query(JobListingModel)
    
    # 添加过滤条件
    if industry:
        query = query.filter(JobListingModel.industry == industry)
    if location:
        query = query.filter(JobListingModel.location.contains(location))
    
    # 分页
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobListing)
async def get_job_detail(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    获取工作详情
    对应Django的job_detail_page
    """
    job = db.query(JobListingModel).filter(JobListingModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/", response_model=JobListing)
async def create_job(
    job_data: JobListingCreate,
    db: Session = Depends(get_db)
):
    """
    创建新工作职位
    对应Django中_save_job_matches_to_db的逻辑
    """
    # 检查ID是否已存在
    existing_job = db.query(JobListingModel).filter(JobListingModel.id == job_data.id).first()
    if existing_job:
        raise HTTPException(status_code=400, detail="Job with this ID already exists")
    
    # 创建新工作
    job_dict = job_data.dict()
    new_job = JobListingModel(**job_dict)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return new_job

@router.put("/{job_id}", response_model=JobListing)
async def update_job(
    job_id: str,
    job_data: JobListingUpdate,
    db: Session = Depends(get_db)
):
    """
    更新工作职位信息
    """
    job = db.query(JobListingModel).filter(JobListingModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 更新字段
    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    删除工作职位
    """
    job = db.query(JobListingModel).filter(JobListingModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}

@router.get("/search/industries")
async def get_industries(db: Session = Depends(get_db)):
    """
    获取所有行业列表
    """
    industries = db.query(JobListingModel.industry).distinct().all()
    return [industry[0] for industry in industries if industry[0]]

@router.get("/search/locations")
async def get_locations(db: Session = Depends(get_db)):
    """
    获取所有地区列表
    """
    locations = db.query(JobListingModel.location).distinct().all()
    return [location[0] for location in locations if location[0]]

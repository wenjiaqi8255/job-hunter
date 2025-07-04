"""
工作详情页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse

from uuid import UUID

from ..models import JobListing, MatchSession, MatchedJob, SavedJob, UserProfile
from ..utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis
from ..services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status
)
from ..services.job_listing_service import fetch_anomaly_analysis_for_jobs_from_supabase


def job_detail_page(request, job_id, match_session_id=None):
    """工作详情页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    job = get_object_or_404(JobListing, id=job_id)
    
    # 基础状态选择（公开数据）
    status_choices = [
        ('not_applied', 'Not Applied'),
        ('viewed', 'Viewed'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
    ]
    
    # 简化的上下文，不包含用户特定数据
    context = {
        'job': job,
        'supa_saved_job': None,  # 前端将通过API获取
        'status_choices': status_choices,
        'active_match_session': None,  # 前端将通过API获取
        'reason_for_match': None,  # 前端将通过API获取
        'tips_for_match': None,  # 前端将通过API获取
        'parsed_insights_list': [],  # 前端将通过API获取
        'job_anomalies': [],  # 前端将通过API获取
        'user_cv_text': "",  # 前端将通过API获取
        'current_match_session_id_for_url': None,  # 前端将通过API获取
    }
    return render(request, 'matcher/job_detail.html', context)

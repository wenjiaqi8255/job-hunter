"""
求职申请相关视图
包括求职信生成、简历定制、申请管理等
使用纯后端 Supabase 认证
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.conf import settings
from supabase import create_client, Client

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import json
import textwrap

from ..models import JobListing, SavedJob, CoverLetter, CustomResume
from .. import gemini_utils
from ..services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status,
    list_supabase_saved_jobs
)
from .auth_views import token_required


def generate_cover_letter_page(request, job_id):
    """生成求职信页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    job = get_object_or_404(JobListing, id=job_id)
    
    # 简化的上下文，不包含用户特定数据
    context = {
        'job': job,
        'cover_letter_content': "",  # 前端将通过API获取
        'generation_error': False,
        'has_existing_cover_letter': False,  # 前端将通过API获取
        'user_cv_text': "",  # 前端将通过API获取
    }
    return render(request, 'matcher/generate_cover_letter.html', context)


def generate_custom_resume_page(request, job_id):
    """生成定制简历页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    job = get_object_or_404(JobListing, id=job_id)
    
    # 简化的上下文，不包含用户特定数据
    context = {
        'job': job,
        'custom_resume_content': "",  # 前端将通过API获取
        'generation_error': False,
        'has_existing_resume': False,  # 前端将通过API获取
        'user_cv_text': "",  # 前端将通过API获取
    }
    return render(request, 'matcher/generate_custom_resume.html', context)


def download_custom_resume(request, job_id):
    """下载定制简历PDF - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    job = get_object_or_404(JobListing, id=job_id)
    
    # 简化处理，返回错误页面让前端处理
    return render(request, 'matcher/error.html', {
        'error_message': 'Please log in to download custom resume',
        'job': job
    })

def my_applications_page(request):
    """
    显示用户保存的工作列表页面 - 页面渲染，认证状态由前端管理
    """
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    # 简化的上下文，不包含用户特定数据
    status_choices = [
        ('applied', 'Applied'),
        ('viewed', 'Viewed'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
        ('not_applied', 'Not Applied'),
    ]
    
    context = {
        'saved_jobs': [],  # 前端将通过API获取
        'status_choices': status_choices,
        'selected_status': 'applied',
        'status_counts': {status: 0 for status, _ in status_choices},  # 前端将通过API获取
    }
    return render(request, 'matcher/my_applications.html', context)
    return render(request, 'matcher/my_applications.html', context)


@token_required
def update_job_application_status(request, job_id):
    """更新工作申请状态 - API端点"""
    # 使用token认证
    user_info = request.supabase_user
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

    if new_status and new_status in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
        job = get_object_or_404(JobListing, id=job_id)
        
        # 创建已认证的Supabase客户端
        try:
            from ..services.supabase_auth_helper import create_authed_supabase_client
            
            # 获取用户token
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
            
            if not user_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing user token'
                }, status=401)
            
            # 创建已认证的客户端
            supabase = create_authed_supabase_client(user_token)
            
            supa_saved_job = get_supabase_saved_job(supabase, job_id)
            
            if supa_saved_job:
                # 更新现有记录
                update_supabase_saved_job_status(supabase, job_id, new_status=new_status)
            else:
                # 创建新记录
                create_data = {
                    "status": new_status,
                    "original_job_id": job.id,
                    "company_name": job.company_name,
                    "job_title": job.job_title,
                    "job_description": job.description,
                    "application_url": job.application_url,
                    "location": job.location,
                    "salary_range": job.salary_range,
                    "industry": job.industry,
                }
                create_supabase_saved_job(supabase, create_data)
            
            mapping = dict(SavedJob.STATUS_CHOICES)
            return JsonResponse({
                    'success': True, 
                    'new_status_display': mapping.get(new_status, new_status), 
                    'new_status': new_status
                })
        except Exception as e:
            print(f"[DEBUG] Error updating job status: {str(e)}")
            return JsonResponse({'success': False, 'error': '更新状态时出错'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)

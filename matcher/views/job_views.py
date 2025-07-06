"""
工作详情页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from uuid import UUID

from ..models import JobListing, MatchSession, MatchedJob, SavedJob, UserProfile
from ..utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis
from ..services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status
)
from ..services.job_listing_service import fetch_anomaly_analysis_for_jobs_from_supabase
from .auth_views import token_required

logger = logging.getLogger(__name__)


def job_detail_page(request, job_id, match_session_id=None):
    """工作详情页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    job = get_object_or_404(JobListing, id=job_id)
    
    # 基础状态选择（公开数据）
    status_choices = [
        ('not_applied', 'Not Applied'),
        ('bookmarked', 'Bookmarked'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offer_received', 'Offer Received'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    # 准备模板上下文
    context = {
        'job': job,
        'status_choices': status_choices,
        'match_session_id': match_session_id,
        'n8n_chat_url': getattr(settings, 'N8N_CHAT_URL', ''),
        'is_from_match_session': bool(match_session_id),
        'user_saved_job': None,  # 前端会通过API获取
        'user_status': 'not_applied',  # 前端会通过API获取
        'user_notes': '',  # 前端会通过API获取
        'anomaly_analysis': None,  # 前端会通过API获取
        'insights': [],  # 前端会通过API获取
    }
    
    return render(request, 'matcher/job_detail.html', context)


# ==========================================================================
# 工作相关API端点
# ==========================================================================

def api_jobs_list(request):
    """
    获取工作列表 - API端点
    公开访问，不需要认证，但会根据认证状态返回不同的数据
    """
    try:
        from ..models import JobListing
        
        # 获取所有工作
        jobs = JobListing.objects.all().order_by('-created_at')
        
        # 转换为API格式
        jobs_data = []
        for job in jobs:
            job_data = {
                'id': job.id,
                'title': job.job_title,
                'company': job.company_name,
                'location': job.location,
                'level': job.level,
                'industry': job.industry,
                'flexibility': job.flexibility,
                'salaryRange': job.salary_range,
                'description': job.description,
                'applicationUrl': job.application_url,
                'createdAt': job.created_at.isoformat() if job.created_at else None,
                # 静态匹配数据，后续可以根据用户情况计算
                'matchScore': None,
                'matchReason': None,
                'insights': []
            }
            jobs_data.append(job_data)
        
        return JsonResponse({
            'success': True,
            'jobs': jobs_data,
            'count': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"API jobs list error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@token_required
def api_save_job(request):
    """
    保存工作API - 简单粗暴的实现
    """
    print(f"[api_save_job] 接收到请求，方法: {request.method}")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_info = request.supabase_user
        print(f"[api_save_job] 获取用户信息: {user_info.get('id') if user_info else 'None'}")
        
        data = json.loads(request.body)
        print(f"[api_save_job] 解析请求数据: {data}")
        
        job_id = data.get('job_id')
        status = data.get('status', 'viewed')
        notes = data.get('notes', '')
        
        if not job_id:
            print(f"[api_save_job] 错误: 缺少 job_id")
            return JsonResponse({'error': 'job_id is required'}, status=400)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        print(f"[api_save_job] 用户令牌存在: {bool(user_token)}")
        
        if not user_token:
            print(f"[api_save_job] 错误: 缺少用户令牌")
            return JsonResponse({
                'success': False,
                'error': 'Missing user token'
            }, status=401)
        
        # 创建已认证的客户端
        supabase = create_authed_supabase_client(user_token)
        print(f"[api_save_job] Supabase客户端创建完成")
        
        # 验证工作是否存在于Supabase
        try:
            job_response = supabase.table('job_listings').select('*').eq('id', job_id).execute()
            if not job_response.data:
                return JsonResponse({'error': 'Job not found'}, status=404)
            
            job_data = job_response.data[0]  # 获取工作基本信息
        except Exception as e:
            logger.error(f"Error fetching job from Supabase: {str(e)}")
            return JsonResponse({'error': 'Failed to verify job'}, status=500)
        
        # 尝试保存到Supabase
        from ..services.supabase_saved_job_service import (
            get_supabase_saved_job,
            create_supabase_saved_job,
            update_supabase_saved_job_status
        )
        
        # 检查是否已存在
        existing_job = get_supabase_saved_job(supabase, job_id)
        if existing_job:
            # 更新状态
            update_supabase_saved_job_status(supabase, job_id, status, notes)
            return JsonResponse({
                'success': True,
                'message': 'Job status updated',
                'job_id': job_id,
                'status': status
            })
        else:
            # 创建新记录
            create_data = {
                "status": status,
                "notes": notes,
                "original_job_id": job_id,
                "company_name": job_data.get('company_name', ''),
                "job_title": job_data.get('job_title', ''),
                "job_description": job_data.get('description', ''),
                "application_url": job_data.get('application_url', ''),
                "location": job_data.get('location', ''),
            }
            # ✅ 正确：传递user_id，让RLS验证权限
            print(f"[api_save_job] 调用 create_supabase_saved_job，user_id: {user_info.get('id')}")
            result = create_supabase_saved_job(supabase, create_data, user_info.get('id'))
            print(f"[api_save_job] create_supabase_saved_job 结果: {result}")
            return JsonResponse({
                'success': True,
                'message': 'Job saved successfully',
                'job_id': job_id,
                'status': status
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@token_required  
def api_saved_jobs(request):
    """
    获取保存的工作列表API - 简单粗暴的实现
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_info = request.supabase_user
        
        # 创建已认证的Supabase客户端
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
        
        # 获取保存的工作
        from ..services.supabase_saved_job_service import list_supabase_saved_jobs
        saved_jobs = list_supabase_saved_jobs(supabase)
        
        return JsonResponse({
            'success': True,
            'jobs': saved_jobs or [],
            'count': len(saved_jobs) if saved_jobs else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_job_detail(request, job_id):
    """
    获取单个工作详情 - API端点
    公开访问，不需要认证
    从 Supabase 获取数据
    """
    try:
        # 从 Supabase 获取工作数据
        from supabase import create_client
        from django.conf import settings
        
        # 创建公共Supabase客户端（job_listings表是公开访问的）
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # 查询工作信息
        job_response = supabase.table('job_listings').select('*').eq('id', job_id).execute()
        
        if not job_response.data:
            return JsonResponse({
                'success': False,
                'error': 'Job not found'
            }, status=404)
        
        job = job_response.data[0]
        
        # 转换为API格式
        job_data = {
            'id': job['id'],
            'title': job['job_title'],
            'company': job['company_name'],
            'location': job['location'],
            'level': job['level'],
            'industry': job['industry'],
            'flexibility': job['flexibility'],
            'salaryRange': job['salary_range'],
            'description': job['description'],
            'applicationUrl': job['application_url'],
            'createdAt': job['created_at'],
            'processed_at': job['processed_at'],
            # 静态匹配数据，后续可以根据用户情况计算
            'matchScore': None,
            'matchReason': None,
            'insights': [],
            'applicationTips': None,
            'status': None
        }
        
        return JsonResponse({
            'success': True,
            'job': job_data
        })
        
    except Exception as e:
        logger.error(f"API job detail error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@token_required  
def api_job_saved_status(request, job_id):
    """
    获取单个工作的保存状态API - 用于工作详情页面
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_info = request.supabase_user
        
        # 创建已认证的Supabase客户端
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
        
        # 获取单个工作的保存状态
        from ..services.supabase_saved_job_service import get_supabase_saved_job
        saved_job = get_supabase_saved_job(supabase, job_id)
        
        if saved_job:
            return JsonResponse({
                'success': True,
                'job_saved': True,
                'status': saved_job.get('status', 'not_applied'),
                'notes': saved_job.get('notes', ''),
                'updated_at': saved_job.get('updated_at')
            })
        else:
            return JsonResponse({
                'success': True,
                'job_saved': False,
                'status': 'not_applied',
                'notes': '',
                'updated_at': None
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==========================================================================
# 现有的API端点
# ==========================================================================


"""
主页视图 - 简化版本
只负责页面渲染，动态内容通过API获取
"""
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings

from datetime import date

from ..models import JobListing


def main_page(request): 
    """
    主页视图 - 简化版本，只负责页面渲染
    认证状态由前端JavaScript管理，动态内容通过API获取
    """
    print(f"[DEBUG] Main page accessed - URL: {request.build_absolute_uri()}")
    
    # 页面渲染不处理认证，所有用户都可以访问主页
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    # 获取所有工作列表（公开数据）
    all_jobs = JobListing.objects.all().order_by('company_name', 'job_title')
    
    # 简化的工作列表，不包含用户特定数据
    all_jobs_simple = []
    for job in all_jobs:
        all_jobs_simple.append({
            'job_object': job,
            'saved_status': None  # 用户特定状态由前端API获取
        })
    
    # 准备基本上下文（不包含用户特定数据）
    context = {
        'user_cv_text': "",  # 前端将通过API获取
        'user_preferences_text': "",  # 前端将通过API获取
        'processed_job_matches': [],  # 前端将通过API获取
        'all_jobs_annotated': all_jobs_simple,
        'all_jobs_count': len(all_jobs),
        'current_match_session_id': None,
        'selected_session_object': None,
        'match_history': [],  # 前端将通过API获取
        'today_date_str': date.today().isoformat(),
        'no_match_reason': None,
    }
    
    return render(request, 'matcher/main_page.html', context)

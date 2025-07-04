"""
用户个人资料相关视图 - 简化版本
只负责页面渲染，动态内容通过API获取
"""
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings


def profile_page(request):
    """
    用户个人资料页面 - 简化版本，只负责页面渲染
    认证状态由前端JavaScript管理，用户数据通过API获取
    """
    # 页面渲染不处理认证，前端会检查认证状态
    # 如果未认证，前端会重定向到登录页面
    
    # 准备基本上下文（不包含用户特定数据）
    context = {
        'username': '',  # 前端将通过API获取
        'job_matches_count': 0,  # 前端将通过API获取
        'already_saved_minutes': 0,  # 前端将通过API计算
        'application_count': 0,  # 前端将通过API获取
        'user_cv_text': '',  # 前端将通过API获取
        'user_preferences_text': '',  # 前端将通过API获取
        'experiences': [],  # 前端将通过API获取
        'experience_count': 0,  # 前端将通过API计算
        'tips_to_improve_count': 0,  # 前端将通过API计算
        'n8n_chat_url': getattr(settings, 'N8N_CHAT_URL', ''),
    }
    
    return render(request, 'matcher/profile_page.html', context)

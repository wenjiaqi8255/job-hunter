"""
工作经验相关视图
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

import json

from ..services.experience_service import get_user_experiences, delete_experience as delete_experience_from_supabase
from .auth_views import token_required


def experience_list(request):
    """经验列表页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    # 简化的上下文，不包含用户特定数据
    context = {
        'experiences': [],  # 前端将通过API获取
        'n8n_chat_url': "",  # 前端将通过API获取
    }
    return render(request, 'matcher/experience_list.html', context)


def experience_delete(request, experience_id):
    """删除工作经验页面 - 页面渲染，认证状态由前端管理"""
    # 页面渲染不处理认证，所有用户都可以访问页面
    # 认证状态和用户特定内容由前端JavaScript通过API获取
    
    # 简化处理，返回错误页面让前端处理
    return render(request, 'matcher/error.html', {
        'error_message': 'Please log in to delete experience',
        'experience_id': experience_id
    })


@csrf_exempt
@require_POST
def experience_completed_callback(request):
    """
    N8n calls this webhook when an experience has been successfully created.
    This can be used to trigger frontend updates, like showing a notification.
    For now, it just returns a success response.
    """
    # We could potentially use this to clear a cache or send a push notification
    # to the user via websockets in a more advanced implementation.
    data = json.loads(request.body)
    print(f"Received callback from N8n for session_id: {data.get('session_id')}")
    return JsonResponse({'success': True, 'message': 'Callback received.'})


@token_required
def api_user_experiences(request):
    """
    获取用户工作经验的API端点 - 使用token认证
    """
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
        
        # 调用服务获取用户经验
        from ..services.experience_service import get_user_experiences
        experiences = get_user_experiences(supabase)
        
        return JsonResponse({
            'success': True,
            'user_id': user_info.get('id'),
            'experiences': experiences,
            'message': 'Experiences retrieved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

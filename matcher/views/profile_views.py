"""
用户个人资料相关视图 - 简化版本
只负责页面渲染，动态内容通过API获取
"""
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from .auth_views import verify_supabase_token, token_required

logger = logging.getLogger(__name__)


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


# ==========================================================================
# 用户相关API端点
# ==========================================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_user_profile(request):
    """
    用户个人资料API端点 - 支持双写机制
    GET: 获取用户资料（自动同步）
    POST: 更新用户资料（双写到Django和Supabase）
    """
    # 简单粗暴的token验证，遵循现有设计
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)

    token = auth_header.split(' ')[1]
    is_valid, user_info, error = verify_supabase_token(token)
    
    if not is_valid or not user_info:
        return JsonResponse({
            'success': False,
            'error': error or 'Invalid token'
        }, status=401)
    
    user_id = user_info.get('id')
    
    try:
        if request.method == 'GET':
            # 获取用户资料，自动处理同步 - 传递用户JWT给服务
            from ..services.supabase_user_profile_service import get_or_create_user_profile
            
            # 关键：传递用户的JWT token，让Supabase服务使用认证客户端
            profile_data = get_or_create_user_profile(user_id, user_jwt_token=token)
            
            if profile_data is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to load user profile'
                }, status=500)
            
            return JsonResponse({
                'success': True,
                'profile': {
                    'user_id': user_id,
                    'email': user_info.get('email'),
                    'name': user_info.get('user_metadata', {}).get('full_name', ''),
                    'cv_text': profile_data.get('cv_text', ''),
                    'preferences_text': profile_data.get('preferences_text', ''),
                    'structured_profile': profile_data.get('structured_profile', {}),
                    'created_at': profile_data.get('created_at'),
                    'updated_at': profile_data.get('last_synced')
                }
            })
            
        elif request.method == 'POST':
            # 更新用户资料 - 使用views_old的逻辑
            data = json.loads(request.body)
            cv_text = data.get('cv_text', '')
            preferences_text = data.get('preferences_text', '')
            
            if cv_text or preferences_text:
                # 调用AI分析 - 复用views_old的gemini_utils调用模式
                from .. import gemini_utils
                
                logger.info(f"Starting AI analysis for user {user_id}")
                structured_profile = gemini_utils.extract_user_profile(cv_text, preferences_text)
                
                # 双写到Django和Supabase - 关键：传递用户JWT token
                from ..services.supabase_user_profile_service import update_user_profile_with_analysis
                
                success = update_user_profile_with_analysis(
                    user_id=user_id,
                    cv_text=cv_text,
                    preferences_text=preferences_text,
                    structured_profile=structured_profile,
                    user_jwt_token=token  # 关键：传递用户JWT，遵循RLS
                )
                
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': 'Profile updated successfully',
                        'profile': {
                            'id': user_id,
                            'email': user_info.get('email'),
                            'name': user_info.get('user_metadata', {}).get('full_name', ''),
                            'cv_text': cv_text,
                            'preferences_text': preferences_text,
                            'structured_profile': structured_profile
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to update profile'
                    }, status=500)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No CV or preferences provided'
                }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"API user profile error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_user_cv_analysis(request):
    """
    用户CV分析API端点
    接受CV文本和偏好，返回AI分析结果
    简单粗暴，不过度设计
    """
    # 复用现有的简单token验证
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)

    token = auth_header.split(' ')[1]
    is_valid, user_info, error = verify_supabase_token(token)
    
    if not is_valid or not user_info:
        return JsonResponse({
            'success': False,
            'error': error or 'Invalid token'
        }, status=401)
    
    user_id = user_info.get('id')
    
    try:
        data = json.loads(request.body)
        cv_text = data.get('cv_text', '')
        preferences_text = data.get('preferences_text', '')
        
        if not cv_text:
            return JsonResponse({
                'success': False,
                'error': 'CV text is required'
            }, status=400)
        
        # 调用AI分析 - 复用views_old的模式
        from .. import gemini_utils
        
        logger.info(f"Starting AI analysis for user {user_id}")
        structured_profile = gemini_utils.extract_user_profile(cv_text, preferences_text)
        
        # 缓存分析结果 - 双写机制，关键：传递用户JWT token
        from ..services.supabase_user_profile_service import update_user_profile_with_analysis
        
        cache_success = update_user_profile_with_analysis(
            user_id=user_id,
            cv_text=cv_text,
            preferences_text=preferences_text,
            structured_profile=structured_profile,
            user_jwt_token=token  # 关键：传递用户JWT，遵循RLS
        )
        
        return JsonResponse({
            'success': True,
            'message': 'CV analysis completed successfully',
            'analysis': structured_profile,
            'cached': cache_success
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"API CV analysis error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@token_required
def api_user_status(request):
    """
    获取用户状态API - 返回用户基本信息和认证状态
    简单粗暴，不过度设计
    """
    try:
        user_info = request.supabase_user
        
        # 基本用户信息
        user_status = {
            'authenticated': True,
            'user_id': user_info.get('id'),
            'email': user_info.get('email'),
            'full_name': user_info.get('user_metadata', {}).get('full_name', ''),
            'avatar_url': user_info.get('user_metadata', {}).get('avatar_url', ''),
        }
        
        return JsonResponse({
            'success': True,
            'user': user_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def api_user_status_public(request):
    """
    公开的用户状态检查API - 不需要认证
    用于检查是否有有效的认证状态
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # 简单检查Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'authenticated': False,
            'message': 'No valid token'
        })
    
    # 这里可以简单验证token格式，但不做复杂验证
    return JsonResponse({
        'authenticated': True,
        'message': 'Token present'
    })


@token_required
def api_user_saved_jobs(request):
    """
    获取用户保存的工作状态 - API端点
    """
    try:
        user_info = request.supabase_user
        
        # 这里应该调用服务获取用户保存的工作
        # 暂时返回空字典，后续可以实现具体逻辑
        saved_jobs_status = {}
        
        return JsonResponse({
            'success': True,
            'user_id': user_info.get('id'),
            'saved_jobs_status': saved_jobs_status,
            'message': 'User saved jobs retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"API user saved jobs error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

"""
认证相关的视图 - 纯前端Supabase认证
只负责token验证，不处理OAuth流程
"""
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

def login_page(request):
    """
    登录页面视图 - 只负责显示登录页面
    认证流程由前端Supabase客户端处理
    """
    # 调试信息
    if not settings.GOOGLE_CLIENT_ID:
        logger.warning("GOOGLE_CLIENT_ID is not set in environment variables")
        print("WARNING: GOOGLE_CLIENT_ID is not set in environment variables")
    else:
        logger.info(f"Google Client ID configured: {settings.GOOGLE_CLIENT_ID[:20]}...")
        print(f"[DEBUG] Google Client ID configured: {settings.GOOGLE_CLIENT_ID[:20]}...")
    
    return render(request, 'matcher/login.html')

def verify_supabase_token(token):
    """
    验证Supabase JWT token的有效性
    返回：(is_valid, user_info, error_message)
    """
    try:
        # 调用Supabase API验证token
        headers = {
            'Authorization': f'Bearer {token}',
            'apikey': settings.SUPABASE_KEY
        }
        
        response = requests.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers=headers
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data, None
        else:
            return False, None, f"Token verification failed: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return False, None, f"Token verification error: {str(e)}"

@csrf_exempt
@require_http_methods(["POST"])
def api_verify_token(request):
    """
    验证Supabase token的API端点
    """
    try:
        # 获取token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'authenticated': False,
                'error': 'Missing or invalid Authorization header'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        # 验证token
        is_valid, user_info, error = verify_supabase_token(token)
        
        if is_valid and user_info:
            return JsonResponse({
                'authenticated': True,
                'user': {
                    'id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'name': user_info.get('user_metadata', {}).get('full_name', '')
                }
            })
        else:
            return JsonResponse({
                'authenticated': False,
                'error': error or 'Invalid token'
            }, status=401)
            
    except Exception as e:
        logger.error(f"API verify token error: {str(e)}")
        return JsonResponse({
            'authenticated': False,
            'error': 'Internal server error'
        }, status=500)

def token_required(view_func):
    """
    装饰器：要求有效的Supabase token
    替代传统的@login_required装饰器
    """
    def wrapper(request, *args, **kwargs):
        # 获取Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'authenticated': False,
                'error': 'Authentication required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        # 验证token
        is_valid, user_info, error = verify_supabase_token(token)
        
        if not is_valid or not user_info:
            return JsonResponse({
                'authenticated': False,
                'error': error or 'Invalid token'
            }, status=401)
        
        # 将用户信息添加到request对象
        request.supabase_user = user_info
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def get_user_from_token(request):
    """
    从token中获取用户信息
    替代传统的get_current_user函数
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    is_valid, user_info, error = verify_supabase_token(token)
    
    return user_info if is_valid else None

@token_required
def api_test_protected(request):
    """
    测试受保护的API端点
    """
    user_info = request.supabase_user
    
    return JsonResponse({
        'success': True,
        'message': 'Access granted to protected API',
        'user': {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('user_metadata', {}).get('full_name', '')
        }
    })

# 简化版本的认证辅助函数
def get_current_user(request):
    """
    获取当前用户信息 - 简化版本，只用于页面渲染
    对于API调用，应该使用get_user_from_token
    """
    # 对于页面渲染，我们先简单返回None
    # 所有的认证状态将由前端JavaScript管理
    return None

def api_test_page(request):
    """
    API测试页面 - 用于测试API调用拦截器
    """
    return render(request, 'matcher/api_test.html')

@csrf_exempt
@require_http_methods(["GET"])
def api_public_test(request):
    """
    公开的API端点 - 不需要认证
    """
    return JsonResponse({
        'success': True,
        'message': 'Public API endpoint accessed successfully',
        'timestamp': str(datetime.now()),
        'has_auth_header': bool(request.META.get('HTTP_AUTHORIZATION'))
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
def api_save_job(request):
    """
    保存工作API - 简单粗暴的实现
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_info = request.supabase_user
        data = json.loads(request.body)
        
        job_id = data.get('job_id')
        status = data.get('status', 'viewed')
        notes = data.get('notes', '')
        
        if not job_id:
            return JsonResponse({'error': 'job_id is required'}, status=400)
        
        # 获取工作信息
        from ..models import JobListing
        job = JobListing.objects.filter(id=job_id).first()
        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)
        
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
        
        # 尝试保存到Supabase
        from ..services.supabase_saved_job_service import (
            get_supabase_saved_job,
            create_supabase_saved_job,
            update_supabase_saved_job_status
        )
        
        # 检查是否已存在
        existing_job = get_supabase_saved_job(supabase, job.id)
        if existing_job:
            # 更新状态
            update_supabase_saved_job_status(supabase, job.id, status, notes)
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
                "original_job_id": job.id,
                "company_name": job.company_name,
                "job_title": job.job_title,
                "job_description": job.description,
                "application_url": job.application_url,
                "location": job.location,
            }
            create_supabase_saved_job(supabase, create_data)
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

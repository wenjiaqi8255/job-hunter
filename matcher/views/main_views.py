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

"""
AI匹配相关API端点
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import uuid
import logging
from datetime import datetime, timezone

from ..views.auth_views import verify_supabase_token
from ..models import JobListing, MatchSession, MatchedJob
from .. import gemini_utils
from ..services.supabase_user_profile_service import get_or_create_user_profile

logger = logging.getLogger(__name__)

def get_supabase_client():
    """获取Supabase客户端 - 复用views_old的逻辑"""
    from supabase import create_client, Client
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        print("Supabase URL or Key not configured.")
        return None
    return create_client(url, key)

def fetch_todays_job_listings_from_supabase():
    """从Supabase获取今日工作列表 - 复用views_old的逻辑"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        # 获取所有工作列表
        response = supabase.table('job_listings').select('*').execute()
        
        if response.data:
            # 适配数据格式为gemini_utils期望的格式
            adapted_jobs = []
            for job_data in response.data:
                adapted_job = {
                    'id': job_data['id'],
                    'company_name': job_data['company_name'],
                    'job_title': job_data['job_title'],
                    'description': job_data.get('description', ''),
                    'application_url': job_data.get('application_url', ''),
                    'location': job_data.get('location', ''),
                    'industry': job_data['industry'],
                    'flexibility': job_data.get('flexibility', ''),
                    'salary_range': job_data.get('salary_range', ''),
                    'level': job_data.get('level', ''),
                }
                adapted_jobs.append(adapted_job)
            return adapted_jobs
        else:
            return []
    except Exception as e:
        print(f"Error fetching jobs from Supabase: {e}")
        return []

@csrf_exempt
@require_http_methods(["POST"])
def api_trigger_match(request):
    """
    触发AI匹配API端点 - 语义化命名
    替换假匹配算法为真实的AI匹配系统
    复用views_old中的业务逻辑
    """
    # 简单token验证
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
        # 获取用户资料数据（包含缓存的分析结果）- 传递用户JWT
        profile_data = get_or_create_user_profile(user_id, user_jwt_token=token)
        
        if not profile_data:
            return JsonResponse({
                'success': False,
                'error': 'Failed to load user profile'
            }, status=500)
        
        cv_text = profile_data.get('cv_text', '')
        preferences_text = profile_data.get('preferences_text', '')
        
        if not cv_text:
            return JsonResponse({
                'success': False,
                'error': 'CV is required for matching. Please update your profile first.',
                'redirect_to_profile': True
            }, status=400)
        
        # 阶段1：如果没有缓存的分析结果，先进行用户画像分析
        structured_profile = profile_data.get('structured_profile', {})
        if not structured_profile:
            logger.info(f"No cached profile analysis found for user {user_id}, running AI analysis")
            structured_profile = gemini_utils.extract_user_profile(cv_text, preferences_text)
            
            # 更新缓存 - 关键：传递用户JWT token
            from ..services.supabase_user_profile_service import update_user_profile_with_analysis
            update_user_profile_with_analysis(user_id, cv_text, preferences_text, structured_profile, user_jwt_token=token)
        
        # 阶段2：获取今日工作列表
        job_listings_for_api = fetch_todays_job_listings_from_supabase()
        
        if not job_listings_for_api:
            return JsonResponse({
                'success': True,
                'jobs': [],
                'message': 'No job listings available for matching today',
                'match_session_id': None
            })
        
        # 阶段3：进行AI匹配 - 复用views_old的逻辑
        max_jobs_for_testing = 10  # 限制处理的工作数量
        logger.info(f"Starting AI job matching for user {user_id} with {len(job_listings_for_api)} jobs")
        
        job_matches_from_api = gemini_utils.match_jobs(
            structured_profile, 
            job_listings_for_api,
            max_jobs_to_process=max_jobs_for_testing
        )
        
        # 阶段4：保存匹配会话到Supabase（一步到位迁移）
        current_match_session_id = None
        supabase_save_success = False
        
        try:
            # 使用新的纯Supabase服务
            from ..services.supabase_match_service import supabase_match_service
            
            # 准备会话数据
            session_data = {
                'user_id': user_id,
                'skills_text': cv_text,
                'user_preferences_text': preferences_text,
                'structured_user_profile_json': structured_profile,
                'jobs': job_matches_from_api
            }
            
            # 直接保存到Supabase
            supabase_result = supabase_match_service.save_match_session(
                session_data, token
            )
            
            if supabase_result['success']:
                current_match_session_id = supabase_result['session_id']
                supabase_save_success = True
                logger.info(f"Successfully saved match session {current_match_session_id} to Supabase with {supabase_result['saved_jobs']} jobs")
            else:
                logger.error(f"Failed to save match session to Supabase: {supabase_result['error']}")
                
        except Exception as e:
            logger.error(f"Failed to save match session: {str(e)}")
            current_match_session_id = None
        
        # 格式化返回数据 - 使用JSONB结构
        formatted_jobs = []
        for match_item in job_matches_from_api:
            job = match_item['job']
            
            # 如果AI输出已经是JSONB格式，直接使用；否则创建基本结构
            if 'analysis' in match_item and 'application_tips' in match_item:
                analysis_data = match_item['analysis']
                application_tips = match_item['application_tips']
            else:
                # 创建基本的分析数据结构
                analysis_data = {
                    'reasoning': match_item.get('reason', ''),
                    'pros': [],
                    'cons': [],
                    'key_insights': [match_item.get('insights', '')]
                }
                application_tips = {
                    'specific_advice': match_item.get('tips', ''),
                    'tips': [],
                    'recommendations': []
                }
            
            formatted_job = {
                'id': job['id'],
                'title': job['job_title'],
                'company': job['company_name'],
                'location': job.get('location', ''),
                'level': job.get('level', ''),
                'industry': job['industry'],
                'flexibility': job.get('flexibility', ''),
                'salaryRange': job.get('salary_range', ''),
                'description': job.get('description', ''),
                'applicationUrl': job.get('application_url', ''),
                
                # 新的JSONB格式匹配数据 - 使用正确的字段名匹配Supabase数据库
                'matchScore': match_item['score'],
                'analysis': analysis_data,      # 修复：匹配数据库字段名
                'application_tips': application_tips, # 修复：匹配数据库字段名
                
                # 为了向后兼容，保留一些旧字段
                'matchReason': analysis_data.get('reasoning', ''),
                'insights': [{
                    'category': 'AI Analysis',
                    'content': '. '.join(analysis_data.get('key_insights', [])),
                    'pros': analysis_data.get('pros', []),
                    'cons': analysis_data.get('cons', [])
                }],
                'tips': application_tips.get('tips', []),
                'recommendations': application_tips.get('recommendations', [])
            }
            formatted_jobs.append(formatted_job)
        
        return JsonResponse({
            'success': True,
            'jobs': formatted_jobs,
            'count': len(formatted_jobs),
            'match_session_id': current_match_session_id,
            'supabase_saved': supabase_save_success,
            'message': f'Found {len(formatted_jobs)} AI-matched jobs' + (
                ' (saved to Supabase)' if supabase_save_success else ' (Supabase save failed)'
            ),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"API match jobs error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error during job matching'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_sync_health_check(request):
    """
    数据同步健康检查API端点
    检查Django和Supabase的连接状态
    """
    try:
        health_status = {
            'django_db': False,
            'supabase_connection': False,
            'job_listings_count': 0,
            'supabase_job_count': 0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 检查Django数据库连接
        try:
            job_count = JobListing.objects.count()
            health_status['django_db'] = True
            health_status['job_listings_count'] = job_count
        except Exception as e:
            logger.error(f"Django DB check failed: {str(e)}")
        
        # 检查Supabase连接
        try:
            supabase = get_supabase_client()
            if supabase:
                response = supabase.table('job_listings').select('id').execute()
                if response.data:
                    health_status['supabase_connection'] = True
                    health_status['supabase_job_count'] = len(response.data)
        except Exception as e:
            logger.error(f"Supabase connection check failed: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'health_status': health_status,
            'overall_healthy': health_status['django_db'] and health_status['supabase_connection']
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Health check failed'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_match_history(request):
    """
    获取用户匹配历史的API端点
    从Supabase读取匹配历史数据
    """
    # 简单token验证
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
        # 使用纯Supabase匹配服务获取匹配历史
        from ..services.supabase_match_service import supabase_match_service
        
        # 获取查询参数
        limit = int(request.GET.get('limit', 10))
        
        # 从Supabase获取匹配历史
        result = supabase_match_service.get_match_history(user_id, token, limit)
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to fetch match history')
            }, status=500)
        
        # 格式化数据以匹配前端期望的格式
        formatted_sessions = []
        for session in result['sessions']:
            formatted_jobs = []
            for job in session.get('matched_jobs', []):
                # 基本工作信息
                job_info = {
                    'id': job.get('job_id', job.get('id')),
                    'matchScore': job.get('score', 0),
                    'status': job.get('status', 'new'),
                    'created_at': job.get('created_at', '')
                }
                
                # 添加结构化的分析数据
                if job.get('analysis'):
                    analysis = job['analysis']
                    job_info.update({
                        'matchReason': analysis.get('reasoning', ''),
                        'pros': analysis.get('pros', []),
                        'cons': analysis.get('cons', []),
                        'insights': [{
                            'category': 'AI Analysis',
                            'content': '. '.join(analysis.get('key_insights', []))
                        }]
                    })
                
                # 添加申请建议
                if job.get('application_tips'):
                    tips = job['application_tips']
                    job_info.update({
                        'application_tips': tips.get('specific_advice', ''),
                        'tips': tips.get('tips', []),
                        'recommendations': tips.get('recommendations', [])
                    })
                
                formatted_jobs.append(job_info)
            
            formatted_session = {
                'id': session['id'],
                'matched_at': session['matched_at'],
                'created_at': session['created_at'],
                'skills_text': session.get('skills_text', ''),
                'user_preferences_text': session.get('user_preferences_text', ''),
                'structured_user_profile_json': session.get('structured_user_profile_json', {}),
                'matched_jobs': formatted_jobs,
                'job_count': len(formatted_jobs)
            }
            formatted_sessions.append(formatted_session)
        
        return JsonResponse({
            'success': True,
            'sessions': formatted_sessions,
            'count': len(formatted_sessions),
            'message': f'Found {len(formatted_sessions)} match sessions',
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"API match history error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error while fetching match history'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_match_session(request, job_match_id):
    """
    获取特定匹配工作的详细信息
    """
    # 简单token验证
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
        # 创建认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase_client = create_authed_supabase_client(token)
        
        # 获取匹配工作详情
        job_response = supabase_client.table('matched_jobs').select(
            'id, job_id, score, status, analysis_data, application_tips, created_at'
        ).eq('id', job_match_id).execute()
        
        if not job_response.data:
            return JsonResponse({
                'success': False,
                'error': 'Match job not found'
            }, status=404)
        
        job = job_response.data[0]
        
        # 获取关联的工作信息
        job_info = None
        try:
            from ..services.supabase_auth_helper import create_authed_supabase_client
            supabase_job_client = create_authed_supabase_client(token)
            job_response = supabase_job_client.table('job_listings').select('*').eq('id', job['job_id']).execute()
            if job_response.data:
                job_info = job_response.data[0]
        except Exception as e:
            logger.warning(f"Failed to fetch job info for {job['job_id']}: {str(e)}")
            job_info = None
        
        # 构造详细信息
        detailed_job = {
            'id': job['job_id'],
            'match_id': job['id'],
            'matchScore': job['score'],
            'status': job['status'],
            'created_at': job['created_at']
        }
        
        # 添加工作基本信息
        if job_info:
            detailed_job.update({
                'title': job_info.get('job_title', ''),
                'company': job_info.get('company_name', ''),
                'location': job_info.get('location', ''),
                'level': job_info.get('level', ''),
                'industry': job_info.get('industry', ''),
                'flexibility': job_info.get('flexibility', ''),
                'salaryRange': job_info.get('salary_range', ''),
                'description': job_info.get('description', ''),
                'applicationUrl': job_info.get('application_url', '')
            })
        
        # 添加结构化的分析数据
        if job.get('analysis_data'):
            analysis = job['analysis_data']
            detailed_job.update({
                'matchReason': analysis.get('reasoning', ''),
                'pros': analysis.get('pros', []),
                'cons': analysis.get('cons', []),
                'keyInsights': analysis.get('key_insights', []),
                'matchDetails': analysis.get('match_details', {})
            })
        
        # 添加申请建议
        if job.get('application_tips'):
            tips = job['application_tips']
            detailed_job.update({
                'application_tips': tips.get('specific_advice', ''),  # 修复：使用下划线命名
                'tips': tips.get('tips', []),
                'recommendations': tips.get('recommendations', []),
                'coverLetterSuggestions': tips.get('cover_letter_suggestions', []),
                'interviewPreparation': tips.get('interview_preparation', [])
            })
        
        return JsonResponse({
            'success': True,
            'job': detailed_job,
            'message': 'Job details retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"API match job details error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error while fetching job details'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_latest_match(request):
    """
    获取最新匹配结果API端点 - 使用纯Supabase服务
    """
    # 简单token验证
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
        # 使用新的纯Supabase服务
        from ..services.supabase_match_service import supabase_match_service
        
        result = supabase_match_service.get_latest_match(user_id, token)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'jobs': result['jobs'],
                'count': result['count'],
                'user_id': result['user_id'],
                'session_id': result.get('session_id'),
                'matched_at': result.get('matched_at')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
        
    except Exception as e:
        logger.error(f"API get latest match error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_session_by_id(request, session_id):
    """
    通过会话ID获取特定会话的详细信息
    """
    # 简单token验证
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
        # 使用纯Supabase匹配服务获取特定会话
        from ..services.supabase_match_service import supabase_match_service
        
        # 获取特定会话的详细信息
        result = supabase_match_service.get_session_by_id(session_id, user_id, token)
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to fetch session')
            }, status=500)
        
        if not result.get('session'):
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)
        
        # 格式化会话数据
        session = result['session']
        formatted_jobs = []
        
        for job in session.get('matched_jobs', []):
            # 基本工作信息
            job_info = {
                'id': job.get('job_id', job.get('id')),
                'matchScore': job.get('score', 0),
                'status': job.get('status', 'new'),
                'created_at': job.get('created_at', '')
            }
            
            # 添加结构化的分析数据
            if job.get('analysis'):
                job_info['analysis'] = job['analysis']
                job_info['matchReason'] = job['analysis'].get('reasoning', '')
            
            # 添加申请建议
            if job.get('application_tips'):
                job_info['application_tips'] = job['application_tips']
                job_info['applicationTips'] = job['application_tips'].get('specific_advice', '')
            
            # 添加工作基本信息（从job_listings表获取）
            job_listing = job.get('job_listing', {})
            job_info.update({
                'title': job_listing.get('job_title', ''),
                'company': job_listing.get('company_name', ''),
                'location': job_listing.get('location', ''),
                'description': job_listing.get('description', ''),
                'level': job_listing.get('level', ''),
                'industry': job_listing.get('industry', ''),
                'flexibility': job_listing.get('flexibility', ''),
                'salaryRange': job_listing.get('salary_range', ''),
                'applicationUrl': job_listing.get('application_url', ''),
            })
            
            formatted_jobs.append(job_info)
        
        formatted_session = {
            'id': session.get('id'),
            'user_id': session.get('user_id'),
            'matched_at': session.get('matched_at'),
            'created_at': session.get('created_at'),
            'matched_jobs': formatted_jobs,
            'job_count': len(formatted_jobs)
        }
        
        return JsonResponse({
            'success': True,
            'session': formatted_session,
            'count': len(formatted_jobs)
        })
        
    except Exception as e:
        logger.error(f"获取会话详情时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'内部服务器错误: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_jobs_for_session(request, session_id):
    """
    通过会话ID获取特定匹配会话的所有工作岗位。
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    token = auth_header.split(' ')[1]
    is_valid, user_info, error = verify_supabase_token(token)
    if not is_valid or not user_info:
        return JsonResponse({'success': False, 'error': error or 'Invalid token'}, status=401)
    
    user_id = user_info.get('id')
    
    try:
        from ..services.supabase_match_service import supabase_match_service
        
        result = supabase_match_service.get_session_by_id(session_id, user_id, token)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Failed to fetch session details')}, status=result.get('status', 500))

        if not result.get('session'):
            return JsonResponse({'success': False, 'error': 'Session not found or you do not have permission to view it.'}, status=404)

        session = result['session']
        formatted_jobs = []
        for job in session.get('matched_jobs', []):
            job_listing = job.get('job_listing', {})
            job_info = {
                'id': job.get('job_id', job.get('id')),
                'title': job_listing.get('job_title', ''),
                'company': job_listing.get('company_name', ''),
                'location': job_listing.get('location', ''),
                'description': job_listing.get('description', ''),
                'level': job_listing.get('level', ''),
                'industry': job_listing.get('industry', ''),
                'flexibility': job_listing.get('flexibility', ''),
                'salaryRange': job_listing.get('salary_range', ''),
                'applicationUrl': job_listing.get('application_url', ''),
                'created_at': job_listing.get('created_at'),
                'updated_at': job.get('created_at'),
                'score': job.get('score', 0),
                'status': job.get('status', 'new'),
                'analysis': job.get('analysis'),
                'application_tips': job.get('application_tips'),
            }
            formatted_jobs.append(job_info)

        return JsonResponse({
            'success': True,
            'jobs': formatted_jobs,
            'count': len(formatted_jobs),
            'session_id': session.get('id'),
            'matched_at': session.get('matched_at'),
            'user_id': session.get('user_id'),
        })

    except Exception as e:
        logger.error(f"Error fetching jobs for session {session_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

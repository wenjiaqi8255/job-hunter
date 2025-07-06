"""
求职申请相关视图
包括求职信生成、简历定制、申请管理等
使用纯后端 Supabase 认证
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
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
                create_supabase_saved_job(supabase, create_data, user_info.get('id'))
            
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


@csrf_exempt
@token_required
def api_generate_cover_letter(request, job_id):
    """生成求职信 - API端点"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 获取工作信息 - 从Supabase获取
        job_response = supabase.table('job_listings').select('*').eq('id', job_id).execute()
        print(f"[DEBUG] Job response: {job_response}")
        
        if not job_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'Job not found'
            }, status=404)
        
        job = job_response.data[0]
        print(f"[DEBUG] Job data: {job}")
        
        # 获取用户CV
        user_profile_response = supabase.table('user_profiles').select('cv_text').eq('user_id', user_id).execute()
        print(f"[DEBUG] User profile response: {user_profile_response}")
        
        if not user_profile_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'Please upload your CV first'
            }, status=400)
        
        cv_text = user_profile_response.data[0].get('cv_text', '')
        if not cv_text:
            return JsonResponse({
                'success': False, 
                'error': 'CV content is empty. Please update your profile.'
            }, status=400)
        
        # 准备工作信息字典
        job_dict = {
            'job_title': job['job_title'],
            'company_name': job['company_name'],
            'level': job['level'],
            'description': job['description'],
            'location': job['location'],
            'industry': job['industry']
        }
        
        # 生成求职信
        from .. import gemini_utils
        print(f"[DEBUG] Generating cover letter with CV: {cv_text[:100]}...")
        print(f"[DEBUG] Job dict: {job_dict}")
        cover_letter_content = gemini_utils.generate_cover_letter(cv_text, job_dict)
        print(f"[DEBUG] Generated cover letter content: {cover_letter_content[:100]}...")
        
        # 检查是否已有求职信
        existing_cover_letter = supabase.table('cover_letters').select('id').eq('user_id', user_id).eq('original_job_id', job_id).execute()
        print(f"[DEBUG] Existing cover letter check: {existing_cover_letter}")
        
        if existing_cover_letter.data:
            # 更新现有求职信
            from datetime import datetime
            update_response = supabase.table('cover_letters').update({
                'content': cover_letter_content,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', existing_cover_letter.data[0]['id']).execute()
            print(f"[DEBUG] Update response: {update_response}")
        else:
            # 创建新求职信
            import uuid
            from datetime import datetime
            insert_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'original_job_id': job_id,
                'company_name': job['company_name'],
                'job_title': job['job_title'],
                'content': cover_letter_content,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            print(f"[DEBUG] Insert data: {insert_data}")
            insert_response = supabase.table('cover_letters').insert(insert_data).execute()
            print(f"[DEBUG] Insert response: {insert_response}")
        
        return JsonResponse({
            'success': True,
            'cover_letter': {
                'content': cover_letter_content,
                'job_title': job['job_title'],
                'company_name': job['company_name'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Error generating cover letter: {str(e)}")
        return JsonResponse({'success': False, 'error': '生成求职信时出错'}, status=500)


@csrf_exempt
@token_required
def api_get_cover_letter(request, job_id):
    """获取求职信 - API端点"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 获取求职信
        cover_letter_response = supabase.table('cover_letters').select('*').eq('user_id', user_id).eq('original_job_id', job_id).execute()
        print(f"[DEBUG] Get cover letter response: {cover_letter_response}")
        
        if not cover_letter_response.data:
            return JsonResponse({
                'success': False,
                'error': 'No cover letter found for this job'
            }, status=404)
        
        cover_letter = cover_letter_response.data[0]
        
        return JsonResponse({
            'success': True,
            'cover_letter': {
                'content': cover_letter['content'],
                'job_title': cover_letter['job_title'],
                'company_name': cover_letter['company_name'],
                'created_at': cover_letter['created_at'],
                'updated_at': cover_letter['updated_at']
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Error getting cover letter: {str(e)}")
        return JsonResponse({'success': False, 'error': '获取求职信时出错'}, status=500)


@csrf_exempt
@token_required
def api_update_cover_letter(request, job_id):
    """更新求职信内容 - API端点"""
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        # 解析请求数据
        data = json.loads(request.body)
        content = data.get('content', '')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 检查求职信是否存在
        existing_cover_letter = supabase.table('cover_letters').select('id').eq('user_id', user_id).eq('original_job_id', job_id).execute()
        print(f"[DEBUG] Existing cover letter query: {existing_cover_letter}")
        
        if not existing_cover_letter.data:
            return JsonResponse({
                'success': False,
                'error': 'Cover letter not found. Please generate one first.'
            }, status=404)
        
        # 更新求职信内容
        from datetime import datetime
        update_response = supabase.table('cover_letters').update({
            'content': content,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', existing_cover_letter.data[0]['id']).execute()
        print(f"[DEBUG] Update response: {update_response}")
        
        if update_response.data:
            return JsonResponse({
                'success': True,
                'message': 'Cover letter updated successfully',
                'cover_letter': {
                    'content': content,
                    'updated_at': update_response.data[0]['updated_at']
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to update cover letter'}, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"[DEBUG] Error updating cover letter: {str(e)}")
        return JsonResponse({'success': False, 'error': '更新求职信时出错'}, status=500)


@csrf_exempt
@token_required
def api_generate_custom_cv(request, job_id):
    """生成定制简历 - API端点"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 获取工作信息 - 从Supabase获取
        job_response = supabase.table('job_listings').select('*').eq('id', job_id).execute()
        print(f"[DEBUG] Job response for custom CV: {job_response}")
        
        if not job_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'Job not found'
            }, status=404)
        
        job = job_response.data[0]
        print(f"[DEBUG] Job data for custom CV: {job}")
        
        # 获取用户CV
        user_profile_response = supabase.table('user_profiles').select('cv_text').eq('user_id', user_id).execute()
        print(f"[DEBUG] User profile response for custom CV: {user_profile_response}")
        
        if not user_profile_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'Please upload your CV first'
            }, status=400)
        
        cv_text = user_profile_response.data[0].get('cv_text', '')
        if not cv_text:
            return JsonResponse({
                'success': False, 
                'error': 'CV content is empty. Please update your profile.'
            }, status=400)
        
        # 准备工作信息字典
        job_dict = {
            'job_title': job['job_title'],
            'company_name': job['company_name'],
            'level': job['level'],
            'description': job['description'],
            'location': job['location'],
            'industry': job['industry']
        }
        
        # 生成定制简历
        from .. import gemini_utils
        print(f"[DEBUG] Generating custom CV with CV: {cv_text[:100]}...")
        print(f"[DEBUG] Job dict for custom CV: {job_dict}")
        custom_cv_content = gemini_utils.generate_custom_resume(cv_text, job_dict)
        print(f"[DEBUG] Generated custom CV content: {custom_cv_content[:100]}...")
        
        # 检查是否已有定制简历
        existing_custom_cv = supabase.table('custom_cvs').select('id').eq('user_id', user_id).eq('job_id', job_id).execute()
        print(f"[DEBUG] Existing custom CV check: {existing_custom_cv}")
        
        if existing_custom_cv.data:
            # 更新现有定制简历
            from datetime import datetime
            update_response = supabase.table('custom_cvs').update({
                'customized_cv_content': custom_cv_content,
                'created_at': datetime.utcnow().isoformat()
            }).eq('id', existing_custom_cv.data[0]['id']).execute()
            print(f"[DEBUG] Update custom CV response: {update_response}")
        else:
            # 创建新定制简历
            import uuid
            from datetime import datetime
            insert_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'job_id': job_id,
                'customized_cv_content': custom_cv_content,
                'customization_notes': None,
                'created_at': datetime.utcnow().isoformat()
            }
            print(f"[DEBUG] Insert custom CV data: {insert_data}")
            insert_response = supabase.table('custom_cvs').insert(insert_data).execute()
            print(f"[DEBUG] Insert custom CV response: {insert_response}")
        
        return JsonResponse({
            'success': True,
            'custom_cv': {
                'content': custom_cv_content,
                'job_title': job['job_title'],
                'company_name': job['company_name'],
                'created_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Error generating custom CV: {str(e)}")
        return JsonResponse({'success': False, 'error': '生成定制简历时出错'}, status=500)


@csrf_exempt
@token_required
def api_get_custom_cv(request, job_id):
    """获取定制简历 - API端点"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 获取定制简历
        custom_cv_response = supabase.table('custom_cvs').select('*').eq('user_id', user_id).eq('job_id', job_id).execute()
        print(f"[DEBUG] Get custom CV response: {custom_cv_response}")
        
        if not custom_cv_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'No custom CV found for this job'
            }, status=404)
        
        custom_cv = custom_cv_response.data[0]
        
        # 获取工作信息
        job_response = supabase.table('job_listings').select('job_title, company_name').eq('id', job_id).execute()
        job_info = job_response.data[0] if job_response.data else {}
        
        return JsonResponse({
            'success': True,
            'custom_cv': {
                'content': custom_cv['customized_cv_content'],
                'customization_notes': custom_cv.get('customization_notes'),
                'job_title': job_info.get('job_title', ''),
                'company_name': job_info.get('company_name', ''),
                'created_at': custom_cv['created_at']
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Error getting custom CV: {str(e)}")
        return JsonResponse({'success': False, 'error': '获取定制简历时出错'}, status=500)


@csrf_exempt
@token_required
def api_update_custom_cv(request, job_id):
    """更新定制简历 - API端点"""
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user_info = request.supabase_user
    user_id = user_info.get('id')
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        customization_notes = data.get('customization_notes', '')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        # 获取用户token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        user_token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not user_token:
            return JsonResponse({'success': False, 'error': 'Missing user token'}, status=401)
        
        # 创建已认证的Supabase客户端
        from ..services.supabase_auth_helper import create_authed_supabase_client
        supabase = create_authed_supabase_client(user_token)
        
        # 更新定制简历
        from datetime import datetime
        update_response = supabase.table('custom_cvs').update({
            'customized_cv_content': content,
            'customization_notes': customization_notes,
            'created_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).eq('job_id', job_id).execute()
        
        print(f"[DEBUG] Update custom CV response: {update_response}")
        
        if not update_response.data:
            return JsonResponse({
                'success': False, 
                'error': 'Custom CV not found or update failed'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Custom CV updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"[DEBUG] Error updating custom CV: {str(e)}")
        return JsonResponse({'success': False, 'error': '更新定制简历时出错'}, status=500)

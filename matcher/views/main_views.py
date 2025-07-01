"""
主页视图
处理工作匹配的核心逻辑
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from datetime import date
from uuid import UUID
import json

from supabase import create_client, Client

from ..models import (
    JobListing, MatchSession, MatchedJob, SavedJob, 
    UserProfile
)
from .. import gemini_utils
from ..utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis
from ..services.supabase_saved_job_service import list_supabase_saved_jobs
from ..services.job_listing_service import (
    fetch_todays_job_listings_from_supabase,
    fetch_anomaly_analysis_for_jobs_from_supabase
)
from .auth_views import get_current_user_info


def main_page(request):
    """
    Renders the main page, handling job matching and user interactions.
    Allows anonymous users to view a limited version of the page.
    Also handles OAuth callbacks if they arrive here.
    """
    # ===================================
    # 调试：打印所有请求参数
    # ===================================
    print(f"[DEBUG] Main page accessed - URL: {request.build_absolute_uri()}")
    print(f"[DEBUG] GET parameters: {dict(request.GET)}")
    print(f"[DEBUG] User authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"[DEBUG] Current user: {request.user.username}")
    
    # ===================================
    # 处理 OAuth 回调（如果直接重定向到首页）
    # ===================================
    oauth_handled = _handle_oauth_callback_on_main_page(request)
    if oauth_handled:
        return oauth_handled
    
    # ===================================
    # 正常的 main_page 逻辑继续
    # ===================================
    user = request.user
    user_profile = None
    match_history = []
    supa_saved_jobs = []
    supa_status_map = {}

    if user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        # Fetch match history for the sidebar, ordered by most recent
        match_history = MatchSession.objects.filter(user=user).order_by('-matched_at')
        # Use the user's ID (which is the Supabase user ID) to fetch their saved jobs
        # The user_id is now handled by RLS via the authenticated supabase client
        supa_saved_jobs = list_supabase_saved_jobs(request.supabase)
        supa_status_map = {sj['original_job_id']: sj['status'] for sj in supa_saved_jobs}

    current_match_session_id_str = request.GET.get('session_id')
    processed_job_matches = []
    selected_session_object = None
    no_match_reason = None

    if request.method == 'POST':
        return _handle_job_matching_post(request, user, user_profile)

    if current_match_session_id_str:
        return _handle_session_view_get(
            request, current_match_session_id_str, user, user_profile, supa_status_map
        )

    # Fetch all job listings for the "All Available Job Listings" section
    all_jobs = JobListing.objects.all().order_by('company_name', 'job_title')
    
    # Annotate all jobs with their saved status for the current user
    all_jobs_annotated = []
    for job in all_jobs:
        # supa_status_map is empty for anonymous users, so status will be None
        supa_status = supa_status_map.get(str(job.id)) # Use string of job.id for matching
        all_jobs_annotated.append({
            'job_object': job,
            'saved_status': supa_status or None
        })

    # Fetch today's job listings count for display
    all_jobs_count = len(all_jobs)
    
    # Prepare context for rendering
    context = {
        'user_cv_text': user_profile.user_cv_text if user_profile else "",
        'user_preferences_text': user_profile.user_preferences_text if user_profile else "",
        'processed_job_matches': processed_job_matches,
        'all_jobs_annotated': all_jobs_annotated,
        'all_jobs_count': all_jobs_count,
        'current_match_session_id': current_match_session_id_str,
        'selected_session_object': selected_session_object,
        'match_history': match_history,
        'today_date_str': date.today().isoformat(),
        'no_match_reason': no_match_reason,
        'user': request.user,
    }
    return render(request, 'matcher/main_page.html', context)


def _handle_oauth_callback_on_main_page(request):
    """处理在主页上的OAuth回调"""
    oauth_code = request.GET.get('code')
    oauth_error = request.GET.get('error')
    oauth_error_description = request.GET.get('error_description')
    oauth_access_token = request.GET.get('access_token')
    oauth_refresh_token = request.GET.get('refresh_token')
    
    # 检查是否有任何 OAuth 相关参数
    oauth_params_present = any([oauth_code, oauth_error, oauth_access_token, oauth_refresh_token])
    
    if not oauth_params_present:
        return None
        
    print(f"[DEBUG] OAuth callback detected on main page")
    print(f"[DEBUG] Code: {oauth_code[:20] if oauth_code else None}...")
    print(f"[DEBUG] Access token: {oauth_access_token[:20] if oauth_access_token else None}...")
    print(f"[DEBUG] Refresh token: {oauth_refresh_token[:20] if oauth_refresh_token else None}...")
    print(f"[DEBUG] Error: {oauth_error}")
    print(f"[DEBUG] Error description: {oauth_error_description}")
    
    # 检查是否直接收到了 tokens（fragment-based flow）
    if oauth_access_token:
        return _handle_direct_token_auth(request, oauth_access_token, oauth_refresh_token)
    
    if oauth_error:
        return _handle_oauth_error(request, oauth_error, oauth_error_description, oauth_code, oauth_access_token)
    
    if oauth_code:
        return _handle_oauth_code_exchange(request, oauth_code)
    
    return None


def _handle_direct_token_auth(request, access_token, refresh_token):
    """处理直接接收到的token认证"""
    print(f"[DEBUG] Direct token received - processing...")
    
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # 使用 token 获取用户信息
        user_response = supabase.auth.get_user(access_token)
        
        if user_response and user_response.user:
            user = user_response.user
            
            print(f"[DEBUG] User authenticated via token on main page: {user.email if user else 'No user'}")
            
            # 存储用户会话信息到 Django session
            request.session['supabase_access_token'] = access_token
            request.session['supabase_refresh_token'] = refresh_token
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_name'] = user.user_metadata.get('full_name', '')
            request.session['user_avatar'] = user.user_metadata.get('picture', '')
            
            print(f"[DEBUG] Session data stored successfully via token on main page")
            
            # 使用 Django 认证系统
            from job_hunting_project.auth_backend import SupabaseUserBackend
            auth_backend = SupabaseUserBackend()
            django_user = auth_backend.authenticate(request=request, supabase_user=user)
            
            if django_user:
                login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                print(f"[DEBUG] Django user logged in successfully via token on main page: {django_user.username}")
                messages.success(request, "Successfully logged in!")
            else:
                print("[DEBUG] Failed to create/retrieve Django user via token on main page")
                messages.error(request, "Could not complete login. Please try again.")
            
            # 重定向到干净的主页（移除 OAuth 参数）
            return redirect(reverse('matcher:main_page'))
        else:
            print("[DEBUG] No user returned from token validation on main page")
            messages.error(request, "Authentication failed: Could not validate token.")
            
    except Exception as token_exception:
        print(f"[DEBUG] Error processing token on main page: {str(token_exception)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        messages.error(request, f"Authentication failed: {str(token_exception)}")
    
    return None


def _handle_oauth_error(request, oauth_error, oauth_error_description, oauth_code, oauth_access_token):
    """处理OAuth错误"""
    if oauth_error == 'invalid_request' and 'bad_oauth_state' in (oauth_error_description or ''):
        print(f"[DEBUG] Bad OAuth state error - this is expected, proceeding anyway")
        # 即使有 state 错误，如果有 code，我们仍然尝试处理
        if not oauth_code and not oauth_access_token:
            messages.error(request, f"OAuth error: {oauth_error_description or oauth_error}")
            # 清除 URL 参数并重定向到干净的首页
            return redirect(reverse('matcher:main_page'))
    else:
        messages.error(request, f"OAuth error: {oauth_error_description or oauth_error}")
        return redirect(reverse('matcher:main_page'))
    
    return None


def _handle_oauth_code_exchange(request, oauth_code):
    """处理OAuth代码交换"""
    print(f"[DEBUG] Processing OAuth code on main page: {oauth_code[:10]}...")
    
    try:
        # 初始化 Supabase 客户端
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # 使用最新的 exchange_code_for_session 方法
        session_response = supabase.auth.exchange_code_for_session(oauth_code)
        
        if session_response and session_response.session:
            user = session_response.user
            session = session_response.session
            
            print(f"[DEBUG] User authenticated successfully on main page: {user.email if user else 'No user'}")
            
            # 存储用户会话信息到 Django session
            request.session['supabase_access_token'] = session.access_token
            request.session['supabase_refresh_token'] = session.refresh_token
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_name'] = user.user_metadata.get('full_name', '')
            request.session['user_avatar'] = user.user_metadata.get('picture', '')
            
            print(f"[DEBUG] Session data stored successfully on main page")
            
            # 使用 Django 认证系统
            from job_hunting_project.auth_backend import SupabaseUserBackend
            auth_backend = SupabaseUserBackend()
            django_user = auth_backend.authenticate(request=request, supabase_user=user)
            
            if django_user:
                login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                print(f"[DEBUG] Django user logged in successfully on main page: {django_user.username}")
                messages.success(request, "Successfully logged in!")
            else:
                print("[DEBUG] Failed to create/retrieve Django user on main page")
                messages.error(request, "Could not complete login. Please try again.")
            
            # 重定向到干净的主页（移除 OAuth 参数）
            return redirect(reverse('matcher:main_page'))
        else:
            print("[DEBUG] No session returned from code exchange on main page")
            messages.error(request, "Authentication failed: No session returned.")
            return redirect(reverse('matcher:main_page'))
            
    except Exception as oauth_exception:
        print(f"[DEBUG] Error processing OAuth on main page: {str(oauth_exception)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        messages.error(request, f"Authentication failed: {str(oauth_exception)}")
        return redirect(reverse('matcher:main_page'))


def _handle_job_matching_post(request, user, user_profile):
    """处理工作匹配的POST请求"""
    if not user.is_authenticated:
        messages.error(request, "You must be logged in to perform a job match.")
        return redirect(settings.LOGIN_URL)

    print(f"--- [POST] Request received for user {request.user.username}. ---")
    
    if not user_profile or not user_profile.user_cv_text:
        messages.info(request, "Please complete your profile before finding matches.")
        return redirect('matcher:profile_page')
    
    user_cv_text_input = request.POST.get('user_cv_text', '')
    user_preferences_text_input = request.POST.get('user_preferences_text', '')
    
    user_profile.user_cv_text = user_cv_text_input
    user_profile.user_preferences_text = user_preferences_text_input
    user_profile.save()
    cv_preview = user_profile.user_cv_text or ""
    print(f"--- [POST] UserProfile updated. New CV: '{cv_preview[:70]}' ---")

    if not user_cv_text_input:
        messages.error(request, "Your CV is empty. Please update your profile before matching jobs.")
        return redirect('matcher:profile_page')

    structured_profile_dict = gemini_utils.extract_user_profile(user_cv_text_input, user_preferences_text_input)
    
    job_listings_for_api = fetch_todays_job_listings_from_supabase(request.supabase)
    
    no_match_reason = None
    if not job_listings_for_api:
        no_match_reason = "No new job listings found for today. Matching cannot proceed with current day's data."
    
    max_jobs_for_testing = 10
    job_matches_from_api = gemini_utils.match_jobs(
        structured_profile_dict, 
        job_listings_for_api,
        max_jobs_to_process=max_jobs_for_testing
    )

    new_match_session = MatchSession.objects.create(
        user=request.user, # Associate with the logged-in user
        skills_text=user_cv_text_input,
        user_preferences_text=user_preferences_text_input,
        structured_user_profile_json=structured_profile_dict
    )
    current_match_session_id_str = str(new_match_session.id)
    print(f"--- [POST] New MatchSession '{current_match_session_id_str}' created. ---")
    request.session['last_match_session_id'] = current_match_session_id_str

    _save_job_matches_to_db(request, job_matches_from_api, new_match_session)
    
    if no_match_reason:
        request.session['no_match_reason'] = no_match_reason
    else:
        request.session.pop('no_match_reason', None)
    return redirect(f"{reverse('matcher:main_page')}?session_id={current_match_session_id_str}")


def _save_job_matches_to_db(request, job_matches_from_api, new_match_session):
    """保存工作匹配结果到数据库"""
    with transaction.atomic():
        for match_item in job_matches_from_api:
            job_data_from_api = match_item['job']

            if not job_data_from_api or 'id' not in job_data_from_api:
                print(f"Skipping match item due to missing job data or ID: {match_item}")
                continue

            if 'anomaly_analysis' in job_data_from_api:
                if not hasattr(request, '_temp_anomaly_data'):
                    request._temp_anomaly_data = {}
                request._temp_anomaly_data[job_data_from_api['id']] = job_data_from_api['anomaly_analysis']

            job_listing_obj, created = JobListing.objects.update_or_create(
                id=job_data_from_api['id'],
                defaults={
                    'company_name': job_data_from_api.get('company_name', 'N/A'),
                    'job_title': job_data_from_api.get('job_title', 'N/A'),
                    'description': job_data_from_api.get('description'),
                    'translated_description': job_data_from_api.get('translated_description'),
                    'application_url': job_data_from_api.get('application_url'),
                    'location': job_data_from_api.get('location'),
                    'industry': job_data_from_api.get('industry', 'Unknown'),
                    'flexibility': job_data_from_api.get('flexibility'),
                    'salary_range': job_data_from_api.get('salary_range'),
                    'level': job_data_from_api.get('level'),
                }
            )
            if created:
                print(f"Created local JobListing stub for ID: {job_listing_obj.id} from Supabase data.")

            MatchedJob.objects.create(
                match_session=new_match_session,
                job_listing=job_listing_obj,
                score=match_item['score'], 
                reason=match_item['reason'],
                insights=match_item.get('insights'), 
                tips=match_item.get('tips')    
            )


def _handle_session_view_get(request, current_match_session_id_str, user, user_profile, supa_status_map):
    """处理查看特定匹配会话的GET请求"""
    if not user.is_authenticated:
        messages.error(request, "You must be logged in to view a specific match session.")
        return redirect(reverse('matcher:main_page'))

    print(f"--- [GET] Request with session_id '{current_match_session_id_str}' received. ---")
    try:
        current_match_session_id_uuid = UUID(current_match_session_id_str)
        # Ensure the session belongs to the current user
        current_match_session = get_object_or_404(MatchSession, id=current_match_session_id_uuid, user=request.user)
        selected_session_object = current_match_session
        
        if user_profile: # Check if user_profile exists
            user_profile.user_cv_text = current_match_session.skills_text
            user_profile.user_preferences_text = current_match_session.user_preferences_text
            user_profile.save()
            cv_preview = user_profile.user_cv_text or ""
            print(f"--- [GET] UserProfile updated from MatchSession. New CV: '{cv_preview[:70]}' ---")
        
        processed_job_matches = _process_matched_jobs_for_session(
            request, current_match_session, supa_status_map
        )
        
        no_match_reason = None
        if not processed_job_matches:
            no_match_reason = request.session.pop('no_match_reason', None)
        
        context = {
            'user_cv_text': user_profile.user_cv_text if user_profile else "",
            'user_preferences_text': user_profile.user_preferences_text if user_profile else "",
            'processed_job_matches': processed_job_matches,
            'all_jobs_annotated': [],
            'all_jobs_count': 0,
            'current_match_session_id': current_match_session_id_str,
            'selected_session_object': selected_session_object,
            'match_history': MatchSession.objects.filter(user=user).order_by('-matched_at'),
            'today_date_str': date.today().isoformat(),
            'no_match_reason': no_match_reason,
            'user': request.user,
        }
        return render(request, 'matcher/main_page.html', context)
        
    except (ValueError, MatchSession.DoesNotExist):
        messages.error(request, "The requested match session was not found or does not belong to you.")
        return redirect(reverse('matcher:main_page'))


def _process_matched_jobs_for_session(request, current_match_session, supa_status_map):
    """处理匹配会话中的工作列表"""
    # WORKAROUND for linter issue: Use direct filter instead of reverse relation
    matched_jobs_for_session = MatchedJob.objects.filter(
        match_session=current_match_session
    ).select_related('job_listing').order_by('-score')

    # Fetch anomaly data from Supabase for all matched jobs at once
    job_ids_for_anomaly_check = [mj.job_listing.id for mj in matched_jobs_for_session]
    anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase(request.supabase, job_ids_for_anomaly_check)
    
    # Check if we have temporary anomaly data from simulation mode
    temp_anomaly_data = getattr(request, '_temp_anomaly_data', {})
    
    processed_job_matches = []
    for mj in matched_jobs_for_session:
        parsed_insights_for_table = parse_and_prepare_insights_for_template(mj.insights)
        # 用 Supabase 状态
        supa_status = supa_status_map.get(mj.job_listing.id)
        
        # Parse anomaly data from Supabase data or temp simulation data
        job_anomalies = []
        analysis_data = anomaly_data_map.get(str(mj.job_listing.id)) or temp_anomaly_data.get(str(mj.job_listing.id))
        print(f"DEBUG: Job ID {mj.job_listing.id}, analysis_data: {analysis_data}")
        if analysis_data:
            job_anomalies = parse_anomaly_analysis(analysis_data)
            print(f"DEBUG: Parsed anomalies for job {mj.job_listing.id}: {job_anomalies}")

        processed_job_matches.append({
            'job': mj.job_listing,
            'score': mj.score, 
            'reason': mj.reason, 
            'parsed_insights_list': parsed_insights_for_table, # New field for structured insights
            'tips': mj.tips,       # Now directly accessing from model
            'saved_status': supa_status or None,
            'anomalies': job_anomalies
        })
    
    return processed_job_matches

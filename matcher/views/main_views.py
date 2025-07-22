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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.cache import cache

from datetime import date
from uuid import UUID
import json

from supabase import create_client, Client

from ..models import (
    JobListing, MatchSession, MatchedJob, SavedJob, 
    UserProfile
)
from .. import gemini_utils
from ..utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis, parse_tips_string
from ..services.job_listing_service import (
    fetch_todays_job_listings_from_supabase,
    fetch_anomaly_analysis_for_jobs_from_supabase
)
from .auth_views import get_current_user_info


def main_page(request):
    """
    Renders the main page, handling job matching and user interactions.
    Accepts an optional session_id to display a specific match session.
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
    saved_job_map = {}

    if user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        # Fetch match history for the sidebar, ordered by most recent
        match_history = MatchSession.objects.filter(user=user).order_by('-matched_at')
        
        # Fetch user's saved jobs and create a status map
        saved_jobs = SavedJob.objects.filter(user=user)
        saved_job_map = {str(sj.job_listing_id): sj.status for sj in saved_jobs}

    current_match_session_id_str = request.GET.get('session_id')
    processed_job_matches = []
    selected_session_object = None
    no_match_reason = None

    if current_match_session_id_str:
        return _handle_session_view_get(
            request, current_match_session_id_str, user, user_profile, saved_job_map
        )

    # Fetch all job listings for the "All Available Job Listings" section
    all_jobs = JobListing.objects.all().order_by('company_name', 'job_title')
    
    # Annotate all jobs with their saved status for the current user
    all_jobs_annotated = []
    for job in all_jobs:
        # saved_job_map is empty for anonymous users, so status will be None
        saved_status = saved_job_map.get(str(job.id))
        all_jobs_annotated.append({
            'job_object': job,
            'saved_status': saved_status
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


@login_required
@require_POST
def start_new_match_session(request):
    """
    Creates a new match session for the logged-in user.
    This view handles the core job matching logic.
    Implements 30秒防抖，防止重复请求。
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if not user_profile.user_cv_text:
        messages.info(request, "Please complete your profile with a CV before starting a match.")
        return redirect('matcher:profile_page')

    # 防抖逻辑：30秒内只允许一次请求
    cache_key = f"matching_in_progress_{request.user.id}"
    existing_session_id = cache.get(cache_key)
    if existing_session_id:
        # 检查该session是否还存在（已被处理完则允许新建）
        try:
            session_obj = MatchSession.objects.get(id=existing_session_id, user=request.user)
            # 直接重定向到该session
            messages.info(request, "已有匹配请求正在进行，请勿重复提交。")
            return redirect(f"{reverse('matcher:main_page')}?session_id={session_obj.id}&in_progress=1")
        except MatchSession.DoesNotExist:
            # session已被处理完，允许新建
            pass
    # 设置防抖标记，有效期30秒
    # 先创建session对象，后续如有异常可清理
    # Use the CV and preferences stored in the user's profile
    user_cv_text = user_profile.user_cv_text
    user_preferences_text = user_profile.user_preferences_text
    structured_profile_dict = gemini_utils.extract_user_profile(user_cv_text, user_preferences_text)
    job_listings_for_api = fetch_todays_job_listings_from_supabase(request.supabase)
    if not job_listings_for_api:
        messages.warning(request, "There are no new job listings to match against today. Please try again later.")
        return redirect('matcher:main_page')
    no_match_reason = None
    job_matches_from_api = gemini_utils.match_jobs(
        structured_profile_dict, 
        job_listings_for_api,
        max_jobs_to_process=36  # Keeping this low for testing
    )
    with transaction.atomic():
        new_match_session = MatchSession.objects.create(
            user=request.user,
            skills_text=user_cv_text,
            user_preferences_text=user_preferences_text,
            structured_user_profile_json=structured_profile_dict
        )
        _save_job_matches_to_db(request, job_matches_from_api, new_match_session)
        # 设置防抖cache，30秒
        cache.set(cache_key, str(new_match_session.id), timeout=30)
    if no_match_reason:
        messages.warning(request, no_match_reason)
    return redirect(f"{reverse('matcher:main_page')}?session_id={new_match_session.id}")


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


def _handle_session_view_get(request, current_match_session_id_str, user, user_profile, saved_job_map):
    """处理查看特定匹配会话的GET请求"""
    if not user.is_authenticated:
        messages.error(request, "You must be logged in to view a specific match session.")
        return redirect(reverse('matcher:main_page'))

    print(f"--- [GET] Request with session_id '{current_match_session_id_str}' received. ---")
    try:
        # Handle both UUID objects (from URL) and strings (from GET params)
        if isinstance(current_match_session_id_str, UUID):
            current_match_session_id = current_match_session_id_str
        else:
            current_match_session_id = UUID(str(current_match_session_id_str))

        query_conditions = Q(id=current_match_session_id)
        if user.is_authenticated:
            query_conditions &= Q(user=user)
        else:
            query_conditions &= Q(user__isnull=True)
            # Potentially add session_key check here if needed for anonymous users in future
            
        selected_session_object = get_object_or_404(MatchSession, query_conditions)
        
        if user_profile: # Check if user_profile exists
            user_profile.user_cv_text = selected_session_object.skills_text
            user_profile.user_preferences_text = selected_session_object.user_preferences_text
            user_profile.save()
            cv_preview = user_profile.user_cv_text or ""
            print(f"--- [GET] UserProfile updated from MatchSession. New CV: '{cv_preview[:70]}' ---")
        
        processed_job_matches, no_match_reason = _process_matched_jobs_for_session(request, selected_session_object, saved_job_map)
        
        # Fetch all job listings (this might be redundant if only showing matched jobs)
        all_jobs_annotated = []
        all_jobs = JobListing.objects.all().order_by('company_name', 'job_title')
        for job in all_jobs:
            saved_status = saved_job_map.get(str(job.id))
            all_jobs_annotated.append({
                'job_object': job,
                'saved_status': saved_status
            })
        all_jobs_count = len(all_jobs)

        match_history = []
        if user.is_authenticated:
            match_history = MatchSession.objects.filter(user=user).order_by('-matched_at')

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
        
    except (ValueError, MatchSession.DoesNotExist):
        messages.error(request, "The requested match session was not found or does not belong to you.")
        return redirect(reverse('matcher:main_page'))


def _process_matched_jobs_for_session(request, current_match_session, saved_job_map):
    """
    Processes matched jobs for a given session, annotating them with insights and saved status.
    """
    if not current_match_session:
        return [], "No session provided."

    matched_jobs_query = MatchedJob.objects.filter(
        match_session=current_match_session
    ).select_related('job_listing').order_by('-score')

    processed_job_matches = []
    
    if not matched_jobs_query.exists():
        return [], "No jobs were matched in this session. Try adjusting your CV or preferences."

    job_ids = [mj.job_listing.id for mj in matched_jobs_query]
    
    # Fetch anomaly analysis for all matched jobs in one go
    anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase(request.supabase, job_ids)

    for job_match in matched_jobs_query:
        job = job_match.job_listing
        parsed_insights = parse_and_prepare_insights_for_template(job_match.insights)
        
        # Parse anomaly data if available
        job_anomalies = []
        analysis_row = anomaly_data_map.get(str(job.id))
        if analysis_row and 'analysis_data' in analysis_row:
            analysis_data = analysis_row['analysis_data']
            job_anomalies = parse_anomaly_analysis(analysis_data)
            
        # Parse tips into a list
        parsed_tips = parse_tips_string(job_match.tips) if job_match.tips else []
        
        # Get saved status from the map
        saved_status = saved_job_map.get(str(job.id))

        processed_job_matches.append({
            'job_object': job,
            'reason': job_match.reason,
            'score': job_match.score,
            'tips': job_match.tips,
            'parsed_tips_list': parsed_tips,
            'parsed_insights_list': parsed_insights,
            'job_anomalies': job_anomalies,
            'saved_status': saved_status,
        })
    
    return processed_job_matches, None


@login_required
def all_matches_page(request):
    """
    Displays a paginated list of all past match sessions for the logged-in user.
    """
    match_sessions_list = MatchSession.objects.filter(user=request.user).order_by('-matched_at')
    
    paginator = Paginator(match_sessions_list, 10)  # Show 10 sessions per page
    page_number = request.GET.get('page')
    
    try:
        match_sessions = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        match_sessions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        match_sessions = paginator.page(paginator.num_pages)

    context = {
        'page_title': 'All Your Job Matches',
        'match_sessions': match_sessions,
        'has_sessions': match_sessions_list.exists(),
        'active_nav': 'matches'  # For the new sidebar navigation
    }
    return render(request, 'matcher/all_matches.html', context)


def upload_cv_and_match(request):
    """
    """

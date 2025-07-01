from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse # Import reverse for redirect
from .models import JobListing, MatchSession, MatchedJob, SavedJob, CoverLetter, UserProfile, CustomResume, JobAnomalyAnalysis
from .forms import SavedJobForm
from . import gemini_utils
from django.db import transaction
import uuid # For validating UUID from GET param
from django.utils import timezone
from django.contrib import messages
import json # For storing profile as JSON
from django.db.models import Prefetch, OuterRef, Subquery, Exists, Q, Count # Added Count
from uuid import UUID # For validating UUIDs
import random # Added for random sampling
import os # Added for environment variables
from django.conf import settings # Added for Supabase settings
from supabase import create_client, Client # Added for Supabase
from datetime import datetime, date, time # Added for date calculations
from django.http import JsonResponse, FileResponse, HttpResponse, HttpResponseRedirect # Added for JSON response and FileResponse
from django.views.decorators.http import require_POST # Added for POST requests only
from django.views.decorators.csrf import csrf_exempt # Consider CSRF implications, ensure frontend sends token
import itertools # Added for zip_longest
import fitz # PyMuPDF
import secrets # Added for PKCE code_verifier
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
import secrets
import hashlib
import base64
import urllib.parse # Added for URL encoding
from django.core.cache import cache  # Add cache import

from .utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis
from .services.experience_service import get_user_experiences, delete_experience as delete_experience_from_supabase
from .services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status,
    list_supabase_saved_jobs,
)
from .services.job_listing_service import fetch_todays_job_listings_from_supabase, fetch_anomaly_analysis_for_jobs_from_supabase

# # Configure logging
# logger = logging.getLogger(__name__)

# Create your views here.

# 添加调试代码到views.py
def google_login(request):
    """
    启动 Google OAuth 登录流程 - 修正版本（使用 Supabase 默认重定向）
    """
    try:
        print(f"[DEBUG] Starting Google OAuth login with Supabase default redirect")
        
        # 不使用自定义 redirect_to，让 Supabase 使用 Dashboard 中配置的 Site URL
        # 这样 OAuth 回调会直接到达首页，我们在首页处理 OAuth 参数
        
        oauth_params = {
            'provider': 'google',
            # 不设置 redirect_to 和 state，避免 bad_oauth_state 错误
        }
        
        # 构建完整的 OAuth URL
        base_oauth_url = f"{settings.SUPABASE_URL}/auth/v1/authorize"
        oauth_url = f"{base_oauth_url}?" + urllib.parse.urlencode(oauth_params)
        
        print(f"[DEBUG] Redirecting to OAuth URL (using Supabase default): {oauth_url}")
        print(f"[DEBUG] OAuth 成功后将重定向到 Supabase Dashboard 中配置的 Site URL")
        
        return redirect(oauth_url)
        
    except Exception as e:
        print(f"[DEBUG] Error in google_login: {str(e)}")
        messages.error(request, f"OAuth login failed: {str(e)}")
        return redirect('matcher:login_page')
def google_callback(request):
    """
    处理 Google OAuth 回调 - 最新最佳实践
    使用最新的 exchange_code_for_session 方法
    """
    try:
        print(f"[DEBUG] === OAuth Callback Debug ===")
        print(f"[DEBUG] Full URL: {request.build_absolute_uri()}")
        print(f"[DEBUG] Method: {request.method}")
        print(f"[DEBUG] GET params: {dict(request.GET)}")
        print(f"[DEBUG] ========================================")
        
        # 1. 获取参数
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        print(f"[DEBUG] Extracted - code: {code[:20] if code else None}...")
        print(f"[DEBUG] Extracted - state: {state}")
        print(f"[DEBUG] Extracted - error: {error}")
        print(f"[DEBUG] Extracted - error_description: {error_description}")
        
        # 2. 错误处理
        if error:
            print(f"[DEBUG] OAuth error: {error} - {error_description}")
            messages.error(request, f"OAuth error: {error_description or error}")
            return redirect('matcher:login_page')
        
        if not code:
            print("[DEBUG] No authorization code received")
            messages.error(request, "Authentication failed: No authorization code received.")
            return redirect('matcher:login_page')
        
        # 3. 验证 state（如果有）
        if state:
            cached_state = cache.get(f"oauth_state_{state}")
            if not cached_state:
                print("[DEBUG] Invalid or expired state parameter")
                messages.error(request, "Authentication failed: Invalid state parameter.")
                return redirect('matcher:login_page')
            cache.delete(f"oauth_state_{state}")
            print("[DEBUG] State parameter validated successfully")
        
        # 4. 使用最新的 exchange_code_for_session 方法
        print(f"[DEBUG] Exchanging code for session: {code[:10]}...")
        
        # 初始化 Supabase 客户端
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # 这是最新的推荐方法 - 只传递授权码
            session_response = supabase.auth.exchange_code_for_session(code)
            
            if session_response and session_response.session:
                user = session_response.user
                session = session_response.session
                
                print(f"[DEBUG] User authenticated successfully: {user.email if user else 'No user'}")
                
                # 5. 存储用户会话信息到 Django session（最佳实践）
                request.session['supabase_access_token'] = session.access_token
                request.session['supabase_refresh_token'] = session.refresh_token
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully")
                
                # 6. 使用 Django 认证系统（可选，如果你需要的话）
                from job_hunting_project.auth_backend import SupabaseUserBackend
                auth_backend = SupabaseUserBackend()
                django_user = auth_backend.authenticate(request=request, supabase_user=user)
                
                if django_user:
                    login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                    print(f"[DEBUG] Django user logged in successfully: {django_user.username}")
                    messages.success(request, "Successfully logged in!")
                else:
                    print("[DEBUG] Failed to create/retrieve Django user")
                    messages.error(request, "Could not complete login. Please try again.")
                    return redirect('matcher:login_page')
                
                print(f"[DEBUG] Redirecting to main page")
                return redirect(reverse('matcher:main_page'))
            else:
                print("[DEBUG] No session returned from code exchange")
                messages.error(request, "Authentication failed: No session returned.")
                return redirect('matcher:login_page')
                
        except Exception as exchange_error:
            print(f"[DEBUG] Error exchanging code for session: {str(exchange_error)}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            messages.error(request, f"Authentication failed: {str(exchange_error)}")
            return redirect('matcher:login_page')
            
    except Exception as e:
        print(f"[DEBUG] Error in google_callback: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        messages.error(request, "An error occurred during authentication.")
        return redirect('matcher:login_page')


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
    oauth_code = request.GET.get('code')
    oauth_error = request.GET.get('error')
    oauth_error_description = request.GET.get('error_description')
    oauth_access_token = request.GET.get('access_token')  # 添加检查 access_token
    oauth_refresh_token = request.GET.get('refresh_token')  # 添加检查 refresh_token
    
    # 检查是否有任何 OAuth 相关参数
    oauth_params_present = any([oauth_code, oauth_error, oauth_access_token, oauth_refresh_token])
    
    if oauth_params_present:
        print(f"[DEBUG] OAuth callback detected on main page")
        print(f"[DEBUG] Code: {oauth_code[:20] if oauth_code else None}...")
        print(f"[DEBUG] Access token: {oauth_access_token[:20] if oauth_access_token else None}...")
        print(f"[DEBUG] Refresh token: {oauth_refresh_token[:20] if oauth_refresh_token else None}...")
        print(f"[DEBUG] Error: {oauth_error}")
        print(f"[DEBUG] Error description: {oauth_error_description}")
        
        # 检查是否直接收到了 tokens（fragment-based flow）
        if oauth_access_token:
            print(f"[DEBUG] Direct token received - processing...")
            
            try:
                # 直接使用 access_token 获取用户信息
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                # 设置 session
                fake_session = type('Session', (), {
                    'access_token': oauth_access_token,
                    'refresh_token': oauth_refresh_token,
                    'token_type': 'bearer'
                })()
                
                # 使用 token 获取用户信息
                user_response = supabase.auth.get_user(oauth_access_token)
                
                if user_response and user_response.user:
                    user = user_response.user
                    
                    print(f"[DEBUG] User authenticated via token on main page: {user.email if user else 'No user'}")
                    
                    # 存储用户会话信息到 Django session
                    request.session['supabase_access_token'] = oauth_access_token
                    request.session['supabase_refresh_token'] = oauth_refresh_token
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
        
        if oauth_error:
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
        
        if oauth_code:
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
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to perform a job match.")
            # Assuming you have a login URL name, e.g., 'account_login' from django-allauth
            # or your custom login view.
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
        
        if no_match_reason:
            request.session['no_match_reason'] = no_match_reason
        else:
            request.session.pop('no_match_reason', None)
        return redirect(f"{reverse('matcher:main_page')}?session_id={current_match_session_id_str}")

    if current_match_session_id_str:
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
            
            # WORKAROUND for linter issue: Use direct filter instead of reverse relation
            matched_jobs_for_session = MatchedJob.objects.filter(match_session=current_match_session).select_related('job_listing').order_by('-score')

            # Fetch anomaly data from Supabase for all matched jobs at once
            job_ids_for_anomaly_check = [mj.job_listing.id for mj in matched_jobs_for_session]
            anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase(request.supabase, job_ids_for_anomaly_check)
            
            # Check if we have temporary anomaly data from simulation mode
            temp_anomaly_data = getattr(request, '_temp_anomaly_data', {})
            
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
            if not processed_job_matches:
                no_match_reason = request.session.pop('no_match_reason', None)
        except (ValueError, MatchSession.DoesNotExist):
            messages.error(request, "The requested match session was not found or does not belong to you.")
            return redirect(reverse('matcher:main_page'))

    # If no specific session is selected via GET (i.e., current_match_session_id_str is None),
    # skills_text_from_session and user_preferences_text_from_session will remain empty,
    # and selected_session_object will be None. This is the state for a "New Match".
    # The automatic redirect to last_match_session_id has been removed to allow this.

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

    # If just visiting the main page without a specific session,
    # ensure the profile info is loaded for the initial form display.
    if not current_match_session_id_str and user_profile:
        # This block already correctly uses user_profile which is fetched at the start.
        # No changes needed here, but confirming the logic is sound.
        pass

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
def profile_page(request):
    """
    Renders the user's profile page, allowing them to manage their CV and experiences.
    """
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'cv_form':
            user_profile.user_cv_text = request.POST.get('user_cv_text', user_profile.user_cv_text)
            if 'cv_file' in request.FILES:
                uploaded_file = request.FILES['cv_file']
                user_profile.cv_file = uploaded_file
                # Extract text from PDF
                try:
                    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                        text = ""
                        for page in doc:
                            text += page.get_text('text') # Explicitly get text as plain text
                        user_profile.user_cv_text = text
                    messages.success(request, 'Successfully uploaded and extracted text from your CV.')
                except Exception as e:
                    messages.error(request, f'Error processing PDF file: {e}')
            
            # This is a bit redundant if file is uploaded, but good for text-only update
            elif request.POST.get('user_cv_text'):
                 messages.success(request, 'Your CV text has been updated.')

        elif form_type == 'preferences_form':
            user_profile.user_preferences_text = request.POST.get('user_preferences_text', user_profile.user_preferences_text)
            messages.success(request, 'Your preferences have been updated.')

        user_profile.save()
        return redirect('matcher:profile_page')

    # Fetch work experiences from Supabase for the current user
    experiences = get_user_experiences(request.supabase)
    experience_count = len(experiences) if experiences else 0

    # Fetch saved jobs from Supabase to get an accurate count
    saved_jobs_from_supabase = list_supabase_saved_jobs(request.supabase)
    application_count = len(saved_jobs_from_supabase) if saved_jobs_from_supabase else 0
    already_saved_minutes = application_count * 20
    
    n8n_chat_url = settings.N8N_CHAT_URL
    # Pass user identifier to chat URL
    full_n8n_url = f"{n8n_chat_url}?user_id={request.user.username}" if n8n_chat_url else ""

    context = {
        'username': request.user.username,
        'job_matches_count': application_count,
        'already_saved_minutes': already_saved_minutes,
        'application_count': application_count,
        'user_cv_text': user_profile.user_cv_text or "",
        'user_preferences_text': user_profile.user_preferences_text or "",
        'experiences': experiences,
        'experience_count': experience_count,
        'tips_to_improve_count': experience_count,
        'n8n_chat_url': full_n8n_url,
    }
    return render(request, 'matcher/profile_page.html', context)

def job_detail_page(request, job_id, match_session_id=None):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    user_profile = None
    user_cv_text = ""
    supa_saved_job = None
    active_match_session = None
    reason_for_match = None
    tips_for_match = None
    parsed_insights = []

    if user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_cv_text = user_profile.user_cv_text or ""
        # user.username no longer needed, RLS handles it
        supa_saved_job = get_supabase_saved_job(request.supabase, job.id)

        session_id_to_use = match_session_id or request.session.get('last_match_session_id')

        if session_id_to_use:
            try:
                session_uuid = UUID(str(session_id_to_use))
                active_match_session = get_object_or_404(MatchSession, id=session_uuid, user=request.user)
                
                job_match_analysis = MatchedJob.objects.filter(
                    match_session=active_match_session,
                    job_listing_id=job.id
                ).first()

                if job_match_analysis:
                    reason_for_match = job_match_analysis.reason
                    tips_for_match = job_match_analysis.tips
                    if job_match_analysis.insights:
                        parsed_insights = parse_and_prepare_insights_for_template(job_match_analysis.insights)
            except (ValueError, MatchSession.DoesNotExist, TypeError):
                active_match_session = None

    # Fetch and parse anomaly data - available to all users
    job_anomalies = []
    anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase(request.supabase, [job.id])
    analysis_data = anomaly_data_map.get(str(job.id))
    if analysis_data:
        job_anomalies = parse_anomaly_analysis(analysis_data)

    if request.method == 'POST':
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to save or update job applications.")
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        new_status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        if supa_saved_job:
            # user.username no longer needed
            update_supabase_saved_job_status(request.supabase, job.id, new_status, notes)
            messages.success(request, "Application status updated.")
        else:
            create_data = {
                # "user_id" is now handled by RLS, so it's removed from here
                "status": new_status or 'viewed',
                "notes": notes,
                "original_job_id": job.id,
                "company_name": job.company_name,
                "job_title": job.job_title,
                "job_description": job.description,
                "application_url": job.application_url,
                "location": job.location,
            }
            create_supabase_saved_job(request.supabase, create_data)
            messages.success(request, "Application saved.")
        
        # Sync local SavedJob mirror
        SavedJob.objects.update_or_create(
            user=request.user,
            job_listing=job,
            defaults={'status': new_status or 'viewed', 'notes': notes}
        )
        
        if active_match_session:
            return redirect('matcher:job_detail_page', job_id=job.id, match_session_id=active_match_session.id)
        else:
            return redirect('matcher:job_detail_page_no_session', job_id=job.id)

    # The old SavedJobForm is no longer needed.
    # We now pass the data directly to the template.
    status_choices = [
        ('not_applied', 'Not Applied'),
        ('viewed', 'Viewed'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
    ]

    context = {
        'job': job,
        'supa_saved_job': supa_saved_job,
        'status_choices': status_choices,
        'active_match_session': active_match_session,
        'reason_for_match': reason_for_match,
        'tips_for_match': tips_for_match,
        'parsed_insights_list': parsed_insights,
        'job_anomalies': job_anomalies,
        'user_cv_text': user_cv_text,
        'current_match_session_id_for_url': active_match_session.id if active_match_session else None,
    }
    return render(request, 'matcher/job_detail.html', context)


@login_required
def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    user_cv_text = user_profile.user_cv_text or ""
    cover_letter_content = ""
    generation_error = False
    has_existing_cover_letter = False

    # Ensure the job is saved in Supabase before proceeding
    supa_saved_job = get_supabase_saved_job(request.supabase, job.id)
    if not supa_saved_job:
        create_data = {
            "status": 'viewed',
            "original_job_id": job.id,
            "company_name": job.company_name,
            "job_title": job.job_title,
        }
        create_supabase_saved_job(request.supabase, create_data)

    # Local SavedJob mirror is no longer needed for CoverLetter relationship

    # 构造 job dict
    job_dict = {
        'id': job.id,
        'company_name': job.company_name,
        'job_title': job.job_title,
        'description': job.description,
        'application_url': job.application_url,
        'location': job.location,
        'industry': job.industry,
        'flexibility': job.flexibility,
        'salary_range': job.salary_range,
        'level': job.level,
    }

    from django.urls import reverse
    if request.method == 'POST':
        if not user_cv_text:
            cover_letter_content = "Please complete your CV in your profile before generating a cover letter."
            generation_error = True
        else:
            cover_letter_content = gemini_utils.generate_cover_letter(user_cv_text, job_dict)
            if cover_letter_content.startswith("(Error generating") or \
               cover_letter_content.startswith("Could not generate") or \
               cover_letter_content.startswith("Please enter your skills"):
                generation_error = True
            else:
                CoverLetter.objects.update_or_create(
                    user=user,
                    job_listing=job,
                    defaults={"content": cover_letter_content}
                )
                has_existing_cover_letter = True
    else:
        # GET: 优先查历史
        try:
            cover_letter_obj = CoverLetter.objects.get(user=user, job_listing=job)
            cover_letter_content = cover_letter_obj.content
            has_existing_cover_letter = True
        except CoverLetter.DoesNotExist:
            if not user_cv_text:
                cover_letter_content = "Please complete your CV in your profile before generating a cover letter."
                generation_error = True
            else:
                # If no existing letter, generate one on GET request
                cover_letter_content = gemini_utils.generate_cover_letter(user_cv_text, job_dict)
                if not (cover_letter_content.startswith("(Error generating") or \
                   cover_letter_content.startswith("Could not generate") or \
                   cover_letter_content.startswith("Please enter your skills")):
                    # Save the newly generated letter
                    CoverLetter.objects.create(user=user, job_listing=job, content=cover_letter_content)
                    has_existing_cover_letter = True # It exists now
                else:
                    generation_error = True

    context = {
        'job': job,
        'cover_letter_content': cover_letter_content,
        'generation_error': generation_error,
        'has_existing_cover_letter': has_existing_cover_letter,
        'user_cv_text': user_cv_text, # Pass CV text for display
    }
    return render(request, 'matcher/generate_cover_letter.html', context)

@login_required
def generate_custom_resume_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    user_cv_text = user_profile.user_cv_text or ""
    custom_resume_content = ""
    generation_error = False
    has_existing_resume = False # Initialize flag

    job_dict = {
        'id': job.id,
        'company_name': job.company_name,
        'job_title': job.job_title,
        'description': job.description,
        'application_url': job.application_url,
        'location': job.location,
        'industry': job.industry,
        'flexibility': job.flexibility,
        'salary_range': job.salary_range,
        'level': job.level,
    }

    if request.method == 'POST':
        if not user_cv_text:
            custom_resume_content = "Please complete your CV in your profile before generating a custom resume."
            generation_error = True
        else:
            custom_resume_content = gemini_utils.generate_custom_resume(user_cv_text, job_dict)
            if custom_resume_content.startswith("(Error generating"):
                generation_error = True
            else:
                # Also save the job to Supabase and locally to mark interest
                # user.username no longer needed
                supa_saved_job = get_supabase_saved_job(request.supabase, job.id)
                if not supa_saved_job:
                    create_data = {
                        # "user_id" is now handled by RLS
                        "status": 'viewed',
                        "original_job_id": job.id,
                        "company_name": job.company_name,
                        "job_title": job.job_title,
                    }
                    create_supabase_saved_job(request.supabase, create_data)

                SavedJob.objects.get_or_create(
                    job_listing=job,
                    user=user,
                    defaults={"status": "viewed"}
                )

                # Save the generated resume
                CustomResume.objects.update_or_create(
                    user=user,
                    job_listing=job,
                    defaults={'content': custom_resume_content}
                )
                has_existing_resume = True # It exists now
    else:
        # GET request: check for existing custom resume
        try:
            existing_resume = CustomResume.objects.get(user=user, job_listing=job)
            custom_resume_content = existing_resume.content
            has_existing_resume = True # It exists
        except CustomResume.DoesNotExist:
            # No existing resume, no operation needed on GET
            pass

    context = {
        'job': job,
        'custom_resume_content': custom_resume_content,
        'generation_error': generation_error,
        'user_cv_text': user_cv_text, # Pass CV text for display
        'has_existing_resume': has_existing_resume, # Pass flag to template
    }
    return render(request, 'matcher/generate_custom_resume.html', context)

@login_required
def download_custom_resume(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    custom_resume = get_object_or_404(CustomResume, job_listing=job, user=user)
    custom_resume_content = custom_resume.content

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Simple styling
    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = height - 20 * mm
    bottom_margin = 20 * mm
    line_height = 14

    p.setFont("Helvetica", 11)
    y = top_margin

    import textwrap
    for paragraph in custom_resume_content.split('\n'):
        lines = textwrap.wrap(paragraph, width=90) if paragraph.strip() else ['']
        for line in lines:
            if y < 20 * mm:
                p.showPage()
                y = top_margin
                p.setFont("Helvetica", 11)
            p.drawString(left_margin, y, line)
            y -= line_height
        y -= 4  # extra space between paragraphs

    p.save()
    buffer.seek(0)
    filename = f"custom_resume_{job.id}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)

@login_required
def my_applications_page(request):
    """
    Displays a list of jobs the user has saved, with filtering by status.
    Data is fetched from Supabase.
    """
    selected_status = request.GET.get('status', 'applied') # Default to 'applied'
    # user_id is no longer needed, RLS handles it

    # Fetch all saved jobs for the user from Supabase
    all_saved_jobs = list_supabase_saved_jobs(request.supabase)

    # Define the status choices, matching what's used elsewhere
    status_choices = [
        ('applied', 'Applied'),
        ('viewed', 'Viewed'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
        ('not_applied', 'Not Applied'),
    ]

    # Calculate counts for each status
    status_counts = {status: 0 for status, _ in status_choices}
    if all_saved_jobs:
        for job in all_saved_jobs:
            status = job.get('status', 'not_applied')
            if status in status_counts:
                status_counts[status] += 1

    # Filter jobs based on the selected status
    if selected_status and all_saved_jobs:
        filtered_jobs = [job for job in all_saved_jobs if job.get('status') == selected_status]
    else:
        filtered_jobs = all_saved_jobs or []

    # Check for existing cover letters for the filtered jobs
    job_ids = [job['original_job_id'] for job in filtered_jobs]
    existing_cover_letters = CoverLetter.objects.filter(
        job_listing_id__in=job_ids,
        user=request.user
    ).values_list('job_listing_id', flat=True)

    # Augment the job data with cover letter info
    for job in filtered_jobs:
        job['has_cover_letter'] = job['original_job_id'] in existing_cover_letters

    context = {
        'saved_jobs': filtered_jobs,
        'status_choices': status_choices,
        'selected_status': selected_status,
        'status_counts': status_counts,
    }
    return render(request, 'matcher/my_applications.html', context)


@login_required
def update_job_application_status(request, job_id):
    user = request.user
    # user.username no longer needed
    supa_saved_job = get_supabase_saved_job(request.supabase, job_id)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

    if new_status and new_status in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
        job = get_object_or_404(JobListing, id=job_id) # Get job once.

        if supa_saved_job:
            # user.username no longer needed
            update_supabase_saved_job_status(request.supabase, job_id, new_status=new_status)
        else:
            # If it doesn't exist in Supabase, create it.
            create_data = {
                # "user_id" is now handled by RLS
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
            create_supabase_saved_job(request.supabase, create_data)

        # Sync local SavedJob mirror
        SavedJob.objects.update_or_create(
            user=user,
            job_listing=job,
            defaults={'status': new_status}
        )
        
        mapping = dict(SavedJob.STATUS_CHOICES)
        return JsonResponse({'success': True, 'new_status_display': mapping.get(new_status, new_status), 'new_status': new_status})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)


# ===================================
# Supabase 用户会话管理辅助函数
# ===================================

def get_current_user_info(request):
    """获取当前用户信息"""
    try:
        access_token = request.session.get('supabase_access_token')
        if not access_token:
            return None
        
        # 从 session 获取用户信息（推荐，更快）
        user_info = {
            'id': request.session.get('user_id'),
            'email': request.session.get('user_email'),
            'name': request.session.get('user_name'),
            'avatar': request.session.get('user_avatar'),
        }
        
        if user_info['id']:
            return user_info
        
        return None
        
    except Exception as e:
        print(f"[DEBUG] Error getting current user: {str(e)}")
        return None

def logout_user(request):
    """登出用户"""
    try:
        # 从 Supabase 登出
        access_token = request.session.get('supabase_access_token')
        if access_token:
            try:
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                supabase.auth.sign_out()
            except Exception as e:
                print(f"[DEBUG] Warning: Error signing out from Supabase: {str(e)}")
        
        # 清除 Django session
        request.session.flush()
        
        return redirect('matcher:login_page')
    except Exception as e:
        print(f"[DEBUG] Error during logout: {str(e)}")
        request.session.flush()
        return redirect('matcher:login_page')

# --- Work Experience Views ---
@login_required
def experience_list(request):
    """Lists all work experiences for the current user from Supabase."""
    user = request.user
    # The user object is no longer needed for authorization, RLS handles it
    experiences = get_user_experiences(request.supabase)
    n8n_chat_url = settings.N8N_CHAT_URL
    full_n8n_url = f"{n8n_chat_url}?user_id={user.username}" if n8n_chat_url else ""
    
    context = {
        'experiences': experiences,
        'n8n_chat_url': full_n8n_url,
    }
    return render(request, 'matcher/experience_list.html', context)

@login_required
@require_POST
def experience_delete(request, experience_id):
    """Deletes a work experience from Supabase."""
    try:
        # The user object is no longer needed for authorization, RLS handles it
        delete_experience_from_supabase(request.supabase, experience_id)
        messages.success(request, 'Work experience deleted successfully!')
    except Exception as e:
        messages.error(request, f'Failed to delete experience: {e}')
    
    return redirect('matcher:experience_list')

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

def logout_view(request):
    """登出视图"""
    return logout_user(request)

# 添加API端点用于检查认证状态
def api_check_auth(request):
    """API：检查认证状态"""
    user = get_current_user_info(request)
    return JsonResponse({
        'authenticated': user is not None,
        'user': user
    })

def process_oauth_tokens(request):
    """
    处理从客户端JavaScript发送的OAuth tokens
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        print(f"[DEBUG] Processing OAuth tokens from client")
        
        # 获取tokens
        access_token = request.POST.get('access_token')
        refresh_token = request.POST.get('refresh_token')
        expires_at = request.POST.get('expires_at')
        provider_token = request.POST.get('provider_token')
        
        print(f"[DEBUG] Received tokens - access_token: {access_token[:20] if access_token else None}...")
        print(f"[DEBUG] Received tokens - refresh_token: {refresh_token[:20] if refresh_token else None}...")
        print(f"[DEBUG] Received tokens - expires_at: {expires_at}")
        
        if not access_token:
            return JsonResponse({'error': 'No access token provided'}, status=400)
        
        # 使用access_token获取用户信息
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # 使用access_token获取用户信息
            user_response = supabase.auth.get_user(access_token)
            
            if user_response and user_response.user:
                user = user_response.user
                
                print(f"[DEBUG] User authenticated via client tokens: {user.email if user else 'No user'}")
                
                # 存储用户会话信息到 Django session
                request.session['supabase_access_token'] = access_token
                request.session['supabase_refresh_token'] = refresh_token or ''
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully via client tokens")
                
                # 使用 Django 认证系统
                from job_hunting_project.auth_backend import SupabaseUserBackend
                auth_backend = SupabaseUserBackend()
                django_user = auth_backend.authenticate(request=request, supabase_user=user)
                
                if django_user:
                    login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                    print(f"[DEBUG] Django user logged in successfully via client tokens: {django_user.username}")
                    
                    return JsonResponse({
                        'success': True,
                        'redirect': reverse('matcher:main_page'),
                        'message': 'Successfully logged in!'
                    })
                else:
                    print("[DEBUG] Failed to create/retrieve Django user via client tokens")
                    return JsonResponse({'error': 'Could not complete login'}, status=400)
            else:
                print("[DEBUG] No user returned from token validation via client")
                return JsonResponse({'error': 'Could not validate token'}, status=400)
                
        except Exception as token_error:
            print(f"[DEBUG] Error validating token via client: {str(token_error)}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return JsonResponse({'error': f'Token validation failed: {str(token_error)}'}, status=400)
            
    except Exception as e:
        print(f"[DEBUG] Error in process_oauth_tokens: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
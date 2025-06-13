from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse # Import reverse for redirect
from .models import JobListing, MatchSession, MatchedJob, SavedJob, CoverLetter, UserProfile, CustomResume
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
from django.http import JsonResponse, FileResponse, HttpResponse # Added for JSON response and FileResponse
from django.views.decorators.http import require_POST # Added for POST requests only
from django.views.decorators.csrf import csrf_exempt # Consider CSRF implications, ensure frontend sends token
import itertools # Added for zip_longest
import fitz # PyMuPDF
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
# import logging # Temporarily replaced with print for debugging

from .services.experience_service import get_user_experiences, delete_experience as delete_experience_from_supabase
from .services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status,
    list_supabase_saved_jobs,
)

# # Configure logging
# logger = logging.getLogger(__name__)

# Create your views here.

# Helper to initialize Supabase client
def get_supabase_client():
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        # Handle missing configuration, perhaps log a warning or raise an error
        # For now, returning None, which will be checked by the caller
        print("Supabase URL or Key not configured.")
        return None
    return create_client(url, key)

# Helper to parse insights string into a list of (pro, con) tuples for table display
def parse_and_prepare_insights_for_template(insights_str):
    if not insights_str or insights_str == 'N/A':
        return [] 
    
    pros = []
    cons = []
    # Normalize: remove leading/trailing whitespace, then split by '*'
    # Each item will be like " Pro: text" or " Con: text" or empty string
    items = [item.strip() for item in insights_str.strip().split('*') if item.strip()]
    
    for item in items:
        if item.startswith("Pro:"):
            pros.append(item[len("Pro:"):].strip())
        elif item.startswith("Con:"):
            cons.append(item[len("Con:"):].strip())
        # else:
            # Optionally handle items that don't fit the Pro/Con format
            # print(f"Warning: Unrecognized insight format: {item}")
            
    # Ensure we have at least one pro or con to make a table
    if not pros and not cons:
        return []

    return list(itertools.zip_longest(pros, cons, fillvalue=None))

# Helper to fetch today's jobs from Supabase
def fetch_todays_job_listings_from_supabase():
    supabase = get_supabase_client()
    if not supabase:
        return [] # Return empty list if client can't be initialized

    today = date.today()
    start_of_day_utc = datetime.combine(today, time.min).isoformat()
    end_of_day_utc = datetime.combine(today, time.max).isoformat()
    
    try:
        # Assuming your table name in Supabase is 'job_listings'
        # and it has a 'created_at' column (timestamp with timezone)
        response = (supabase.table('job_listings')
                           .select('*')
                           .gte('created_at', start_of_day_utc)
                           .lte('created_at', end_of_day_utc)
                           .execute())
        if response.data:
            # Adapt Supabase data to a structure usable by gemini_utils.match_jobs
            # We'll create simple objects or dicts that mimic JobListing attributes
            adapted_jobs = []
            for job_data in response.data:
                # Create a dictionary that mimics the JobListing model structure
                # This allows gemini_utils.match_jobs to work with minimal changes
                # if it expects objects with specific attributes.
                # Ensure all fields expected by gemini_utils.match_jobs are present.
                adapted_job = {
                    'id': job_data.get('id'),
                    'company_name': job_data.get('company_name'),
                    'job_title': job_data.get('job_title'),
                    'description': job_data.get('description'),
                    'application_url': job_data.get('application_url'),
                    'location': job_data.get('location'),
                    'industry': job_data.get('industry'),
                    'flexibility': job_data.get('flexibility'),
                    'salary_range': job_data.get('salary_range'),
                    'level': job_data.get('level'), # Make sure 'level' exists in your Supabase table
                    # Add other fields as needed by gemini_utils.match_jobs
                }
                adapted_jobs.append(adapted_job)
            return adapted_jobs
        else:
            return []
    except Exception as e:
        print(f"Error fetching jobs from Supabase: {e}")
        return []

def main_page(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Fetch UserProfile, which holds the single source of truth for CV and preferences
    user_profile, created = UserProfile.objects.get_or_create(session_key=session_key)
    print(f"--- [GET] Initial UserProfile CV for session {session_key}: '{user_profile.user_cv_text[:70] if user_profile.user_cv_text else 'Empty'}' ---")

    current_match_session_id_str = request.GET.get('session_id')
    processed_job_matches = []
    selected_session_object = None
    no_match_reason = None  # 新增变量

    # 一次性查出所有 Supabase 申请记录，构建 {job_id: status} 字典
    supa_saved_jobs = list_supabase_saved_jobs(session_key)
    supa_status_map = {sj['original_job_id']: sj['status'] for sj in supa_saved_jobs}

    if request.method == 'POST':
        print(f"--- [POST] Request received for session {session_key}. ---")
        # The form is submitted from the modal on the main page.
        # We update the profile with this data first, then run the match.
        
        # 如果profile为空，重定向到profile页面
        if not user_profile.user_cv_text:
            messages.info(request, "Please complete your profile before finding matches.")
            return redirect('matcher:profile_page')
        
        user_cv_text_input = request.POST.get('user_cv_text', '')
        user_preferences_text_input = request.POST.get('user_preferences_text', '')
        
        # Update the UserProfile with the latest data from the form
        user_profile.user_cv_text = user_cv_text_input
        user_profile.user_preferences_text = user_preferences_text_input
        user_profile.save()
        print(f"--- [POST] UserProfile updated. New CV: '{user_profile.user_cv_text[:70]}' ---")

        # Check if the profile is empty
        if not user_cv_text_input:
            messages.error(request, "Your CV is empty. Please update your profile before matching jobs.")
            return redirect('matcher:profile_page') # Redirect to profile to add CV

        # Phase 4.1: Extract structured user profile
        structured_profile_dict = gemini_utils.extract_user_profile(user_cv_text_input, user_preferences_text_input)
        
        # NEW: Fetch today's job listings from Supabase
        job_listings_for_api = fetch_todays_job_listings_from_supabase()
        
        if not job_listings_for_api:
            no_match_reason = "No new job listings found for today. Matching cannot proceed with current day's data."
            # 继续后续逻辑，match_jobs会处理空列表
        # The sampling logic might not be necessary if Supabase query is efficient
        # and if the number of daily jobs isn't excessively large.
        # For now, I'm removing the random sampling as we are already filtering by day.
        # if len(all_job_listings) > 10: 
        #     # Development and testing purpose
        #     job_listings_for_api = random.sample(all_job_listings, 10)
        # else:
        #     job_listings_for_api = all_job_listings
        
        # If job_listings_for_api is empty, gemini_utils.match_jobs should ideally handle this gracefully.
        max_jobs_for_testing = 10 # Define the maximum number of jobs for testing #find_max_jobs_to_process
        job_matches_from_api = gemini_utils.match_jobs(
            structured_profile_dict, 
            job_listings_for_api,
            max_jobs_to_process=max_jobs_for_testing # Pass the new parameter
        )

        new_match_session = MatchSession.objects.create(
            skills_text=user_cv_text_input, # Storing CV here
            user_preferences_text=user_preferences_text_input, # Storing preferences
            structured_user_profile_json=structured_profile_dict # Storing structured profile
        )
        current_match_session_id_str = str(new_match_session.id)
        print(f"--- [POST] New MatchSession '{current_match_session_id_str}' created. ---")
        request.session['last_match_session_id'] = current_match_session_id_str

        # When saving MatchedJob, ensure the 'job_listing' foreign key can handle
        # the dictionary structure or find/create a temporary JobListing-like object.
        # This part needs careful handling if gemini_utils.match_jobs returns jobs
        # that are dictionaries and MatchedJob expects a JobListing instance.

        # For now, assuming gemini_utils.match_jobs returns a list of dicts,
        # and each dict contains an 'id' for the job from Supabase.
        # We might need to retrieve the actual JobListing instance if it's stored locally
        # or create a temporary one if not.
        #
        # Given the requirement to use Supabase as the primary source for *matching*,
        # the MatchedJob.job_listing might need to point to a Supabase ID or a local
        # stub if we don't want to duplicate all Supabase jobs into the local Django DB.
        #
        # For simplicity in this step, let's assume `gemini_utils.match_jobs` returns
        # dicts and `match_item['job']` within that list contains the job's 'id' (from Supabase).
        # We will then need to fetch or create a local JobListing stub to satisfy the ForeignKey.
        #
        # ALTERNATIVE: If `MatchedJob`'s `job_listing` FK can be temporarily nullable or point to a text ID,
        # that would simplify. But that's a model change.
        #
        # Let's assume for now, we need to get/create a local JobListing object.
        # This implies jobs from Supabase *might* also need to be synced/replicated to local DB
        # at some point if `MatchedJob` must link to a local `JobListing`.
        #
        # The original requirement stated "The table structure in Supabase is identical to your current Django JobListing model."
        # This is helpful. If a job from Supabase (matched today) does not exist in local Django DB,
        # we should probably create it locally before creating the MatchedJob record.

        with transaction.atomic(): # Ensure all MatchedJob are created or none
            for match_item in job_matches_from_api:
                job_data_from_api = match_item['job'] # This is now expected to be a dict from fetch_todays_job_listings_from_supabase

                # Ensure job_data_from_api is not None and has an 'id'
                if not job_data_from_api or 'id' not in job_data_from_api:
                    print(f"Skipping match item due to missing job data or ID: {match_item}")
                    continue

                # Get or create the JobListing instance in the local Django DB
                # This ensures that MatchedJob.job_listing can point to a valid local record.
                # This also means your local DB will store copies of jobs that were matched.
                job_listing_obj, created = JobListing.objects.update_or_create(
                    id=job_data_from_api['id'], # Assuming 'id' is the primary key and matches Supabase
                    defaults={
                        'company_name': job_data_from_api.get('company_name', 'N/A'),
                        'job_title': job_data_from_api.get('job_title', 'N/A'),
                        'description': job_data_from_api.get('description'),
                        'application_url': job_data_from_api.get('application_url'),
                        'location': job_data_from_api.get('location'),
                        'industry': job_data_from_api.get('industry', 'Unknown'), # Provide default if mandatory
                        'flexibility': job_data_from_api.get('flexibility'),
                        'salary_range': job_data_from_api.get('salary_range'),
                        'level': job_data_from_api.get('level'),
                        # 'source': 'SupabaseToday', # Optional: mark the source
                        # 'status': 'pending_match_evaluation', # Optional: internal status
                        # 'created_at' will be set if 'created' is True and auto_now_add=True
                        # 'processed_at': timezone.now() # Or handle as needed
                    }
                )
                if created:
                    print(f"Created local JobListing stub for ID: {job_listing_obj.id} from Supabase data.")


                MatchedJob.objects.create(
                    match_session=new_match_session,
                    job_listing=job_listing_obj, # Link to the local JobListing instance
                    score=match_item['score'], 
                    reason=match_item['reason'],
                    insights=match_item.get('insights'), 
                    tips=match_item.get('tips')    
                )
        # Redirect to the same page with the new session_id in GET to show results
        # 通过session传递no_match_reason
        if no_match_reason:
            request.session['no_match_reason'] = no_match_reason
        else:
            request.session.pop('no_match_reason', None)
        return redirect(f"{reverse('matcher:main_page')}?session_id={current_match_session_id_str}")

    # Handling GET request or if POST didn't redirect (e.g. initial load)
    if current_match_session_id_str:
        print(f"--- [GET] Request with session_id '{current_match_session_id_str}' received. ---")
        try:
            current_match_session_id_uuid = UUID(current_match_session_id_str)
            current_match_session = get_object_or_404(MatchSession, id=current_match_session_id_uuid)
            selected_session_object = current_match_session # For displaying session date
            user_profile.user_cv_text = current_match_session.skills_text
            user_profile.user_preferences_text = current_match_session.user_preferences_text
            user_profile.save()
            print(f"--- [GET] UserProfile updated from MatchSession. New CV: '{user_profile.user_cv_text[:70]}' ---")
            matched_jobs_for_session = current_match_session.matched_jobs.select_related('job_listing').order_by('-score')
            for mj in matched_jobs_for_session:
                parsed_insights_for_table = parse_and_prepare_insights_for_template(mj.insights)
                # 用 Supabase 状态
                supa_status = supa_status_map.get(mj.job_listing.id)
                processed_job_matches.append({
                    'job': mj.job_listing,
                    'score': mj.score, 
                    'reason': mj.reason, 
                    'parsed_insights_list': parsed_insights_for_table, # New field for structured insights
                    'tips': mj.tips,       # Now directly accessing from model
                    'saved_status': supa_status or None
                })
            if not processed_job_matches:
                no_match_reason = request.session.pop('no_match_reason', None)
        except (ValueError, MatchSession.DoesNotExist):
            return redirect(reverse('matcher:main_page'))
    
    # If no specific session is selected via GET (i.e., current_match_session_id_str is None),
    # skills_text_from_session and user_preferences_text_from_session will remain empty,
    # and selected_session_object will be None. This is the state for a "New Match".
    # The automatic redirect to last_match_session_id has been removed to allow this.

    # Fetch all job listings for the "All Available Job Listings" section
    # Annotate all jobs with their saved status for the current user
    all_jobs = JobListing.objects.all().order_by('company_name', 'job_title')
    
    # Prepare a list of dictionaries or custom objects for `all_jobs_annotated`
    all_jobs_annotated = []
    for job in all_jobs:
        supa_status = supa_status_map.get(job.id)
        all_jobs_annotated.append({
            'job_object': job,
            'saved_status': supa_status or None
        })

    # Fetch match history
    match_history = MatchSession.objects.order_by('-matched_at')[:10] # Last 10 sessions

    context = {
        'processed_job_matches': processed_job_matches,
        'user_cv_text': user_profile.user_cv_text, 
        'user_preferences_text': user_profile.user_preferences_text,
        'current_match_session_id': current_match_session_id_str,
        'selected_session_object': selected_session_object,
        'all_jobs_annotated': all_jobs_annotated,
        'all_jobs_count': all_jobs.count(),
        'match_history': match_history,
        'no_match_reason': no_match_reason,  # 传递到模板
    }

    print(f"--- Final context for render. CV: '{context.get('user_cv_text', '')[:70]}' ---")
    return render(request, 'matcher/main_page.html', context)

def profile_page(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Get or create the UserProfile for the current session
    profile, created = UserProfile.objects.get_or_create(session_key=session_key)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'cv_form':
            # Handle CV text and file upload
            profile.user_cv_text = request.POST.get('user_cv_text', profile.user_cv_text)
            if 'cv_file' in request.FILES:
                uploaded_file = request.FILES['cv_file']
                profile.cv_file = uploaded_file
                # Extract text from PDF
                try:
                    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        profile.user_cv_text = text
                    messages.success(request, 'Successfully uploaded and extracted text from your CV.')
                except Exception as e:
                    messages.error(request, f'Error processing PDF file: {e}')
            
            # This is a bit redundant if file is uploaded, but good for text-only update
            elif request.POST.get('user_cv_text'):
                 messages.success(request, 'Your CV text has been updated.')

        elif form_type == 'preferences_form':
            profile.user_preferences_text = request.POST.get('user_preferences_text', profile.user_preferences_text)
            messages.success(request, 'Your preferences have been updated.')

        elif form_type == 'email_form':
            # Assuming the field name for email is 'user_email_text' in the form
            profile.user_email = request.POST.get('user_email_text', profile.user_email)
            messages.success(request, 'Your email has been updated.')

        profile.save()
        return redirect('matcher:profile_page')

    # Fetch work experiences from Supabase
    experiences = get_user_experiences()
    experience_count = len(experiences) if experiences else 0

    application_count = SavedJob.objects.filter(user_session_key=session_key).count()
    already_saved_minutes = application_count * 20
    
    n8n_chat_url = settings.N8N_CHAT_URL
    full_n8n_url = f"{n8n_chat_url}?session_id={session_key}" if n8n_chat_url else ""

    context = {
        'username': 'Guest',
        'job_matches_count': application_count,
        'already_saved_minutes': already_saved_minutes,
        'application_count': application_count,
        'user_cv_text': profile.user_cv_text,
        'user_preferences_text': profile.user_preferences_text,
        'user_email_text': profile.user_email,
        'experiences': experiences,
        'experience_count': experience_count,
        'tips_to_improve_count': experience_count,
        'n8n_chat_url': full_n8n_url,
    }
    return render(request, 'matcher/profile_page.html', context)

def job_detail_page(request, job_id, match_session_id=None):
    job = get_object_or_404(JobListing, id=job_id)
    # 获取当前session的UserProfile
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    user_profile, _ = UserProfile.objects.get_or_create(session_key=session_key)
    user_cv_text = user_profile.user_cv_text or ""
    saved_job_instance = None  # 不再用本地模型实例
    parsed_insights = [] # Initialize parsed_insights
    
    # Ensure session key exists
    if not request.session.session_key:
        request.session.create()
    user_session_key = request.session.session_key

    # 获取 Supabase 申请记录
    supa_saved_job = get_supabase_saved_job(user_session_key, job.id)

    # Attempt to fetch the specific match details for this job and session
    job_match_analysis = None
    active_match_session = None # To store the MatchSession object for breadcrumb
    session_id_to_use = match_session_id # Prioritize URL parameter
    if not session_id_to_use:
        session_id_to_use = request.session.get('last_match_session_id') # Fallback to session

    if session_id_to_use:
        try:
            # Ensure session_id_to_use is UUID if it came from session (string)
            if isinstance(session_id_to_use, str):
                try:
                    session_id_to_use = UUID(session_id_to_use)
                except ValueError:
                    session_id_to_use = None # Invalid UUID string, treat as no session ID
            
            if isinstance(session_id_to_use, UUID):
                # Fetch the MatchSession object for breadcrumb and analysis
                active_match_session = MatchSession.objects.get(id=session_id_to_use)
                job_match_analysis = MatchedJob.objects.get(
                    match_session=active_match_session, # Use the fetched session object
                    job_listing_id=job.id
                )
                job.reason_for_match = job_match_analysis.reason
                job.insights_for_match = job_match_analysis.insights
                job.tips_for_match = job_match_analysis.tips
                # Parse insights here if job_match_analysis is found
                if job_match_analysis.insights:
                    parsed_insights = parse_and_prepare_insights_for_template(job_match_analysis.insights)
        except MatchSession.DoesNotExist:
            active_match_session = None # Session not found, clear it
            session_id_to_use = None    # Ensure session_id_to_use is also None if session doesn't exist
            # job_match_analysis will remain None
        except MatchedJob.DoesNotExist:
            # MatchedJob not found for this session, but session itself is valid for breadcrumb
            pass # job_match_analysis will remain None, active_match_session is still set
        except TypeError: 
            session_id_to_use = None # Catch if session_id_to_use couldn't be cast to UUID
            active_match_session = None

    # POST: 保存/更新 Supabase 申请记录
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes')
        if supa_saved_job:
            # 更新
            update_supabase_saved_job_status(user_session_key, job.id, new_status, notes)
        else:
            # 创建
            data = {
                "user_session_key": user_session_key,
                "status": new_status or 'not_applied',
                "notes": notes,
                "original_job_id": job.id,
                "company_name": job.company_name,
                "job_title": job.job_title,
                "job_description": job.description,
                "application_url": job.application_url,
                "location": job.location,
                "salary_range": job.salary_range,
                "industry": job.industry,
                # created_at/updated_at 由 Supabase 默认生成
            }
            create_supabase_saved_job(data)
        # 重定向
        if match_session_id:
            return redirect('matcher:job_detail_page', job_id=job.id, match_session_id=match_session_id)
        else:
            return redirect('matcher:job_detail_page_no_session', job_id=job.id)

    # 构造表单初始值（用 dict 模拟 ModelForm）
    class DummySavedJob:
        def __init__(self, d):
            self.status = d.get('status', 'not_applied') if d else 'not_applied'
            self.notes = d.get('notes', '') if d else ''
            self.updated_at = d.get('updated_at') if d else None
        def get_status_display(self):
            # 模拟 Django choices 显示
            mapping = dict(SavedJob.STATUS_CHOICES)
            return mapping.get(self.status, self.status)
    dummy_saved_job = DummySavedJob(supa_saved_job)

    # 用原有表单类渲染，但用 initial/dummy instance
    from .forms import SavedJobForm
    form = SavedJobForm(initial={
        'status': dummy_saved_job.status,
        'notes': dummy_saved_job.notes,
    })
    # 兼容模板对 saved_job_instance 的访问
    saved_job_instance = dummy_saved_job

    # If job_match_analysis was not found,但 job object 可能有 insights_for_match
    if not parsed_insights and hasattr(job, 'insights_for_match') and job.insights_for_match:
        parsed_insights = parse_and_prepare_insights_for_template(job.insights_for_match)

    context = {
        'job': job,
        'skills_text': user_cv_text,
        'saved_job_form': form,
        'saved_job_instance': saved_job_instance, # 用 dummy 替代
        'status_choices': SavedJob.STATUS_CHOICES, # Pass choices for direct iteration if needed
        'job_match_analysis': job_match_analysis,
        'current_match_session_id_for_url': session_id_to_use, 
        'active_match_session': active_match_session, # Pass the session object for breadcrumb
        'parsed_insights_list': parsed_insights # Add parsed insights to context
    }
    return render(request, 'matcher/job_detail.html', context)

def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    user_profile, _ = UserProfile.objects.get_or_create(session_key=session_key)
    user_cv_text = user_profile.user_cv_text or ""
    cover_letter_content = ""
    generation_error = False
    has_existing_cover_letter = False

    # 获取或创建 SavedJob
    saved_job, _ = SavedJob.objects.get_or_create(
        job_listing=job,
        user_session_key=session_key,
        defaults={"status": "not_applied"}
    )

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
                    saved_job=saved_job,
                    defaults={"content": cover_letter_content}
                )
                has_existing_cover_letter = True
    else:
        # GET: 优先查历史
        try:
            cover_letter_obj = CoverLetter.objects.get(saved_job=saved_job)
            cover_letter_content = cover_letter_obj.content
            has_existing_cover_letter = True
        except CoverLetter.DoesNotExist:
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
                    CoverLetter.objects.create(
                        saved_job=saved_job,
                        content=cover_letter_content
                    )
                    has_existing_cover_letter = True

    context = {
        'job': job,
        'cover_letter_content': cover_letter_content,
        'skills_text': user_cv_text,
        'generation_error': generation_error,
        'profile_url': reverse('matcher:profile_page'),
        'has_existing_cover_letter': has_existing_cover_letter,
    }
    return render(request, 'matcher/cover_letter_page.html', context)

def generate_custom_resume_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    user_profile, _ = UserProfile.objects.get_or_create(session_key=session_key)
    user_cv_text = user_profile.user_cv_text or ""
    custom_resume_content = ""
    generation_error = False
    has_existing_resume = False

    # Prepare job dict for AI (mimic fetch_todays_job_listings_from_supabase structure)
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
    # POST: 重新生成
    if request.method == 'POST':
        if not user_cv_text:
            custom_resume_content = "Please complete your CV in your profile before generating a custom resume."
            generation_error = True
        else:
            custom_resume_content = gemini_utils.generate_custom_resume(user_cv_text, job_dict)
            if not custom_resume_content or custom_resume_content.startswith("(Error generating") or custom_resume_content.startswith("Could not generate"):
                generation_error = True
            else:
                # 覆盖或新建
                CustomResume.objects.update_or_create(
                    user_session_key=session_key,
                    job_listing=job,
                    defaults={"content": custom_resume_content}
                )
                has_existing_resume = True
    else:
        # GET: 优先查历史
        try:
            custom_resume_obj = CustomResume.objects.get(user_session_key=session_key, job_listing=job)
            custom_resume_content = custom_resume_obj.content
            has_existing_resume = True
        except CustomResume.DoesNotExist:
            if not user_cv_text:
                custom_resume_content = "Please complete your CV in your profile before generating a custom resume."
                generation_error = True
            else:
                custom_resume_content = gemini_utils.generate_custom_resume(user_cv_text, job_dict)
                if not custom_resume_content or custom_resume_content.startswith("(Error generating") or custom_resume_content.startswith("Could not generate"):
                    generation_error = True
                else:
                    CustomResume.objects.create(
                        user_session_key=session_key,
                        job_listing=job,
                        content=custom_resume_content
                    )
                    has_existing_resume = True

    context = {
        'job': job,
        'custom_resume_content': custom_resume_content,
        'skills_text': user_cv_text,
        'generation_error': generation_error,
        'profile_url': reverse('matcher:profile_page'),
        'has_existing_resume': has_existing_resume,
    }
    return render(request, 'matcher/custom_resume_page.html', context)

def download_custom_resume_pdf(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    user_profile, _ = UserProfile.objects.get_or_create(session_key=session_key)
    user_cv_text = user_profile.user_cv_text or ""

    # Prepare job dict for AI
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

    if not user_cv_text:
        return HttpResponse("No CV found. Please complete your profile.", status=400)

    custom_resume_content = gemini_utils.generate_custom_resume(user_cv_text, job_dict)
    if not custom_resume_content:
        return HttpResponse("Failed to generate custom resume.", status=500)

    # Generate PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left_margin = 20 * mm
    top_margin = height - 20 * mm
    line_height = 12
    max_width = width - 2 * left_margin
    y = top_margin
    p.setFont("Helvetica", 11)

    # Split content into lines, wrap if needed
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

def my_applications_page(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create() # Create session if not exists
        session_key = request.session.session_key
        if not session_key:
            return render(request, 'matcher/my_applications.html', {
                'saved_jobs_with_forms_and_letters': [],
                'status_choices': [('', 'All')] + list(SavedJob.STATUS_CHOICES),
                'selected_status': '',
                'status_counts': {'': 0},
                'page_title': "My Applications",
                'message': "Could not establish a session. Please try again."
            })

    selected_status = request.GET.get('status')
    tab_status_choices = [('', 'All')] + list(SavedJob.STATUS_CHOICES)

    # Supabase 查询所有申请记录
    all_user_saved_jobs = list_supabase_saved_jobs(session_key)
    # 统计各状态数量
    status_counts = {s[0]: 0 for s in SavedJob.STATUS_CHOICES}
    status_counts[''] = len(all_user_saved_jobs)
    for sj in all_user_saved_jobs:
        if sj['status'] in status_counts:
            status_counts[sj['status']] += 1
    # 过滤
    if selected_status and selected_status in [s[0] for s in SavedJob.STATUS_CHOICES]:
        saved_jobs_filtered = [sj for sj in all_user_saved_jobs if sj['status'] == selected_status]
    else:
        selected_status = ''
        saved_jobs_filtered = all_user_saved_jobs

    # 构造表单和 cover_letter（cover_letter 仍查本地）
    from .forms import SavedJobForm
    saved_jobs_with_forms_and_letters = []
    for sj in saved_jobs_filtered:
        # DummySavedJob 用于兼容模板
        class DummySavedJob:
            def __init__(self, d):
                self.status = d.get('status', 'not_applied')
                self.notes = d.get('notes', '')
                self.updated_at = d.get('updated_at')
                self.job_listing = get_object_or_404(JobListing, id=d['original_job_id'])
                self.pk = d.get('id')
            def get_status_display(self):
                mapping = dict(SavedJob.STATUS_CHOICES)
                return mapping.get(self.status, self.status)
        dummy_saved_job = DummySavedJob(sj)
        form = SavedJobForm(initial={
            'status': dummy_saved_job.status,
            'notes': dummy_saved_job.notes,
        })
        # cover_letter 仍查本地
        cover_letter = None
        try:
            cover_letter = CoverLetter.objects.get(saved_job__job_listing=dummy_saved_job.job_listing, saved_job__user_session_key=session_key)
        except CoverLetter.DoesNotExist:
            pass
        saved_jobs_with_forms_and_letters.append({
            'saved_job': dummy_saved_job,
            'form': form,
            'cover_letter': cover_letter
        })

    context = {
        'saved_jobs_with_forms_and_letters': saved_jobs_with_forms_and_letters,
        'status_choices': tab_status_choices,
        'selected_status': selected_status,
        'status_counts': status_counts,
        'page_title': "My Applications"
    }
    return render(request, 'matcher/my_applications.html', context)

@require_POST
# Make sure your JS sends the CSRF token.
def update_job_application_status(request, job_id):
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'success': False, 'error': 'No session found.'}, status=400)
    
    # Supabase: 先查，有则更新，无则插入
    supa_saved_job = get_supabase_saved_job(session_key, job_id)
    new_status = request.POST.get('status')
    if new_status in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
        if supa_saved_job:
            update_supabase_saved_job_status(session_key, job_id, new_status=new_status)
            # 获取 display
            mapping = dict(SavedJob.STATUS_CHOICES)
            return JsonResponse({'success': True, 'new_status_display': mapping.get(new_status, new_status)})
        else:
            # 没有则插入
            job = get_object_or_404(JobListing, id=job_id)
            data = {
                "user_session_key": session_key,
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
            create_supabase_saved_job(data)
            mapping = dict(SavedJob.STATUS_CHOICES)
            return JsonResponse({'success': True, 'new_status_display': mapping.get(new_status, new_status)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)


# --- Work Experience Views ---

def experience_list(request):
    """Lists all work experiences for the current user session from Supabase."""
    session_key = request.session.session_key
    if not session_key:
        return redirect('matcher:profile_page')

    experiences = get_user_experiences()
    n8n_chat_url = settings.N8N_CHAT_URL
    full_n8n_url = f"{n8n_chat_url}?session_id={session_key}" if n8n_chat_url else ""
    
    context = {
        'experiences': experiences,
        'n8n_chat_url': full_n8n_url,
    }
    return render(request, 'matcher/experience_list.html', context)

@require_POST
def experience_delete(request, experience_id):
    """Deletes a work experience from Supabase."""
    try:
        # Deletion no longer requires session_key for authorization.
        delete_experience_from_supabase(experience_id)
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


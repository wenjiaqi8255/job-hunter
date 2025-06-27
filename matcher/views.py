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
from django.http import JsonResponse, FileResponse, HttpResponse # Added for JSON response and FileResponse
from django.views.decorators.http import require_POST # Added for POST requests only
from django.views.decorators.csrf import csrf_exempt # Consider CSRF implications, ensure frontend sends token
import itertools # Added for zip_longest
import fitz # PyMuPDF
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from django.contrib.auth.decorators import login_required

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
@login_required
def main_page(request):
    """
    Renders the main page, handling job matching and user interactions.
    """
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    # Fetch match history for the sidebar, ordered by most recent
    match_history = MatchSession.objects.filter(user=user).order_by('-matched_at')

    current_match_session_id_str = request.GET.get('session_id')
    processed_job_matches = []
    selected_session_object = None
    no_match_reason = None

    # Use the user's ID (which is the Supabase user ID) to fetch their saved jobs
    supa_saved_jobs = list_supabase_saved_jobs(request.user.username)
    supa_status_map = {sj['original_job_id']: sj['status'] for sj in supa_saved_jobs}

    if request.method == 'POST':
        print(f"--- [POST] Request received for user {request.user.username}. ---")
        
        if not user_profile.user_cv_text:
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
        
        job_listings_for_api = fetch_todays_job_listings_from_supabase()
        
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
        print(f"--- [GET] Request with session_id '{current_match_session_id_str}' received. ---")
        try:
            current_match_session_id_uuid = UUID(current_match_session_id_str)
            # Ensure the session belongs to the current user
            current_match_session = get_object_or_404(MatchSession, id=current_match_session_id_uuid, user=request.user)
            selected_session_object = current_match_session
            user_profile.user_cv_text = current_match_session.skills_text
            user_profile.user_preferences_text = current_match_session.user_preferences_text
            user_profile.save()
            cv_preview = user_profile.user_cv_text or ""
            print(f"--- [GET] UserProfile updated from MatchSession. New CV: '{cv_preview[:70]}' ---")
            
            # WORKAROUND for linter issue: Use direct filter instead of reverse relation
            matched_jobs_for_session = MatchedJob.objects.filter(match_session=current_match_session).select_related('job_listing').order_by('-score')

            # Fetch anomaly data from Supabase for all matched jobs at once
            job_ids_for_anomaly_check = [mj.job_listing.id for mj in matched_jobs_for_session]
            anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase(job_ids_for_anomaly_check)
            
            # Check if we have temporary anomaly data from simulation mode
            temp_anomaly_data = getattr(request, '_temp_anomaly_data', {})
            
            for mj in matched_jobs_for_session:
                parsed_insights_for_table = parse_and_prepare_insights_for_template(mj.insights)
                # 用 Supabase 状态
                supa_status = supa_status_map.get(mj.job_listing.id)
                
                # Parse anomaly data from Supabase data or temp simulation data
                job_anomalies = []
                analysis_data = anomaly_data_map.get(mj.job_listing.id) or temp_anomaly_data.get(mj.job_listing.id)
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

    # Fetch match history for the current user
    match_history = MatchSession.objects.filter(user=request.user).order_by('-matched_at')[:10]

    # If just visiting the main page without a specific session,
    # ensure the profile info is loaded for the initial form display.
    if not current_match_session_id_str:
        # This block already correctly uses user_profile which is fetched at the start.
        # No changes needed here, but confirming the logic is sound.
        pass

    # Fetch today's job listings count for display
    all_jobs_count = JobListing.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    # Prepare context for rendering
    context = {
        'user_cv_text': user_profile.user_cv_text,
        'user_preferences_text': user_profile.user_preferences_text,
        'processed_job_matches': processed_job_matches,
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
                            text += page.get_text() # Explicitly get text
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
    experiences = get_user_experiences(request.user)
    experience_count = len(experiences) if experiences else 0

    application_count = SavedJob.objects.filter(user=request.user).count()
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

@login_required
def job_detail_page(request, job_id, match_session_id=None):
    job = get_object_or_404(JobListing, id=job_id)
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_cv_text = user_profile.user_cv_text or ""
    
    supa_saved_job = get_supabase_saved_job(request.user.username, job.id)

    active_match_session = None
    reason_for_match = None
    tips_for_match = None
    parsed_insights = []
    job_anomalies = []

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

    # Fetch and parse anomaly data
    anomaly_data_map = fetch_anomaly_analysis_for_jobs_from_supabase([job.id])
    analysis_data = anomaly_data_map.get(job.id)
    if analysis_data:
        job_anomalies = parse_anomaly_analysis(analysis_data)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        if supa_saved_job:
            update_supabase_saved_job_status(request.user.username, job.id, new_status, notes)
            messages.success(request, "Application status updated.")
        else:
            create_data = {
                "user_id": request.user.username,
                "status": new_status or 'viewed',
                "notes": notes,
                "original_job_id": job.id,
                "company_name": job.company_name,
                "job_title": job.job_title,
                "job_description": job.description,
                "application_url": job.application_url,
                "location": job.location,
            }
            create_supabase_saved_job(create_data)
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

    # Ensure the job is saved in Supabase and locally before proceeding
    supa_saved_job = get_supabase_saved_job(user.username, job.id)
    if not supa_saved_job:
        create_data = {
            "user_id": user.username,
            "status": 'viewed',
            "original_job_id": job.id,
            "company_name": job.company_name,
            "job_title": job.job_title,
        }
        create_supabase_saved_job(create_data)

    # Now, get or create the local mirror for the FK relationship
    saved_job, _ = SavedJob.objects.get_or_create(
        job_listing=job,
        user=user,
        defaults={"status": "viewed"}
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
                # If no existing letter, generate one on GET request
                cover_letter_content = gemini_utils.generate_cover_letter(user_cv_text, job_dict)
                if not (cover_letter_content.startswith("(Error generating") or \
                   cover_letter_content.startswith("Could not generate") or \
                   cover_letter_content.startswith("Please enter your skills")):
                    # Save the newly generated letter
                    CoverLetter.objects.create(saved_job=saved_job, content=cover_letter_content)
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
                supa_saved_job = get_supabase_saved_job(user.username, job.id)
                if not supa_saved_job:
                    create_data = {
                        "user_id": user.username,
                        "status": 'viewed',
                        "original_job_id": job.id,
                        "company_name": job.company_name,
                        "job_title": job.job_title,
                    }
                    create_supabase_saved_job(create_data)

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
    user_id = request.user.username

    # Fetch all saved jobs for the user from Supabase
    all_saved_jobs = list_supabase_saved_jobs(user_id)

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
        saved_job__job_listing_id__in=job_ids,
        saved_job__user=request.user
    ).values_list('saved_job__job_listing_id', flat=True)

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
    supa_saved_job = get_supabase_saved_job(user.username, job_id)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

    if new_status and new_status in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
        job = get_object_or_404(JobListing, id=job_id) # Get job once.

        if supa_saved_job:
            update_supabase_saved_job_status(user.username, job_id, new_status=new_status)
        else:
            # If it doesn't exist in Supabase, create it.
            create_data = {
                "user_id": user.username,
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
            create_supabase_saved_job(create_data)

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


# --- Work Experience Views ---
@login_required
def experience_list(request):
    """Lists all work experiences for the current user from Supabase."""
    user = request.user
    experiences = get_user_experiences(user)
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
        # Pass the user object for authorization
        delete_experience_from_supabase(experience_id, request.user)
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
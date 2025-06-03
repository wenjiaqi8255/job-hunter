from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse # Import reverse for redirect
from .models import JobListing, MatchSession, MatchedJob, SavedJob, CoverLetter # Added CoverLetter
from .forms import SavedJobForm # Corrected import: JobSearchForm and UserProfileForm were not in forms.py
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
from django.http import JsonResponse # Added for JSON response
from django.views.decorators.http import require_POST # Added for POST requests only
from django.views.decorators.csrf import csrf_exempt # Consider CSRF implications, ensure frontend sends token
import itertools # Added for zip_longest

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

    current_match_session_id_str = request.GET.get('session_id')
    current_match_session = None
    skills_text_from_session = "" # Will become user_cv_text
    user_preferences_text_from_session = "" # New
    processed_job_matches = []
    selected_session_object = None

    if request.method == 'POST':
        user_cv_text_input = request.POST.get('user_cv_text', '')
        user_preferences_text_input = request.POST.get('user_preferences_text', '')

        # Phase 4.1: Extract structured user profile
        structured_profile_dict = gemini_utils.extract_user_profile(user_cv_text_input, user_preferences_text_input)
        
        # NEW: Fetch today's job listings from Supabase
        job_listings_for_api = fetch_todays_job_listings_from_supabase()
        
        if not job_listings_for_api:
            # Handle case where no jobs were fetched for today
            # You might want to display a message to the user
            messages.info(request, "No new job listings found for today. Matching cannot proceed with current day's data.")
            # Option 1: Redirect back or render with a message (current approach)
            # To redirect and show the message, we need to ensure messages are displayed on the target template
            # Or, pass a specific context variable to indicate this state.
            # For now, we'll let it proceed to match_jobs with an empty list,
            # which should result in 'No specific matches found'.
            # Or, redirect to avoid unnecessary API calls if gemini_utils.match_jobs can't handle empty list
            # return redirect(reverse('matcher:main_page')) # This might clear POST data.

        # The sampling logic might not be necessary if Supabase query is efficient
        # and if the number of daily jobs isn't excessively large.
        # For now, I'm removing the random sampling as we are already filtering by day.
        # if len(all_job_listings) > 10: 
        #     # Development and testing purpose
        #     job_listings_for_api = random.sample(all_job_listings, 10)
        # else:
        #     job_listings_for_api = all_job_listings
        
        # If job_listings_for_api is empty, gemini_utils.match_jobs should ideally handle this gracefully.
        max_jobs_for_testing = 5 # Define the maximum number of jobs for testing
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
        return redirect(f"{reverse('matcher:main_page')}?session_id={current_match_session_id_str}")

    # Handling GET request or if POST didn't redirect (e.g. initial load)
    if current_match_session_id_str:
        try:
            current_match_session_id_uuid = UUID(current_match_session_id_str)
            current_match_session = get_object_or_404(MatchSession, id=current_match_session_id_uuid)
            selected_session_object = current_match_session # For displaying session date
            
            # Populate textareas with data from this selected session
            skills_text_from_session = current_match_session.skills_text # This is user_cv_text
            user_preferences_text_from_session = current_match_session.user_preferences_text
            
            # Fetch related MatchedJob instances, prefetching JobListing
            matched_jobs_for_session = current_match_session.matched_jobs.select_related('job_listing').order_by('-score')
            
            # Annotate with saved status
            saved_job_subquery = SavedJob.objects.filter(
                job_listing_id=OuterRef('job_listing_id'),
                user_session_key=session_key
            ).values('status')[:1]

            for mj in matched_jobs_for_session: # mj is a MatchedJob instance
                saved_status_result = SavedJob.objects.filter(job_listing=mj.job_listing, user_session_key=session_key).values('status').first()
                
                parsed_insights_for_table = parse_and_prepare_insights_for_template(mj.insights)

                processed_job_matches.append({
                    'job': mj.job_listing,
                    'score': mj.score, 
                    'reason': mj.reason, 
                    'parsed_insights_list': parsed_insights_for_table, # New field for structured insights
                    'tips': mj.tips,       # Now directly accessing from model
                    'saved_status': saved_status_result['status'] if saved_status_result else None
                })

        except (ValueError, MatchSession.DoesNotExist):
            # Invalid UUID or session not found, redirect to main page without session_id
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
        saved_status_result = SavedJob.objects.filter(job_listing=job, user_session_key=session_key).values('status').first()
        all_jobs_annotated.append({
            'job_object': job,
            'saved_status': saved_status_result['status'] if saved_status_result else None
        })

    # Fetch match history
    match_history = MatchSession.objects.order_by('-matched_at')[:10] # Last 10 sessions

    context = {
        'user_cv_text': skills_text_from_session, # Pass CV text to template
        'user_preferences_text': user_preferences_text_from_session, # Pass preferences text
        'processed_job_matches': processed_job_matches,
        'all_jobs_annotated': all_jobs_annotated,
        'all_jobs_count': all_jobs.count(),
        'match_history': match_history,
        'current_match_session_id': current_match_session_id_str,
        'selected_session_object': selected_session_object,
    }
    return render(request, 'matcher/main_page.html', context)

def profile_page(request):
    # Placeholder values, replace with actual logic to retrieve these
    # For example, from a UserProfile model or session
    username = request.user.username if request.user.is_authenticated else "Guest"
    user_cv_text = request.session.get('user_cv_text', '')
    user_preferences_text = request.session.get('user_preferences_text', '')
    user_email_text = request.session.get('user_email_text', '') # Retrieve email from session

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # Always update all three from the POST data, as hidden fields carry them over
        user_cv_text = request.POST.get('user_cv_text', user_cv_text) # Keep existing if not in POST
        user_preferences_text = request.POST.get('user_preferences_text', user_preferences_text)
        user_email_text = request.POST.get('user_email_text', user_email_text)

        # Save to session
        request.session['user_cv_text'] = user_cv_text
        request.session['user_preferences_text'] = user_preferences_text
        request.session['user_email_text'] = user_email_text

        if form_type == 'cv_form':
            # Specific logic for CV form if any, e.g., messages.success(request, "CV updated!")
            # The profile extraction and matching might be better handled in a separate view 
            # or triggered explicitly by a button within this form's modal if it's heavy.
            # For now, just updating session and re-rendering.
            messages.success(request, "CV text updated in session.")
        elif form_type == 'preferences_form':
            messages.success(request, "Preferences updated in session.")
        elif form_type == 'email_form':
            messages.success(request, "Email updated in session.")
        
        # It's generally good practice to redirect after a POST to prevent re-submission
        # However, if you're just updating session and re-rendering the same page, this might be acceptable.
        # If you have more complex logic (like actual profile processing), consider redirecting.
        # return redirect('matcher:profile_page') # Uncomment if you prefer to redirect

    application_count = 0
    already_saved_minutes = 0
    # 获取所有申请的总数 (当前阶段的模拟)
    try:
        # 尝试从 Application 模型获取总数
        application_count = SavedJob.objects.count()
    except Exception: 
        # 如果 Application 模型不存在或有其他问题，则使用占位符
        application_count = 5 # Fallback to placeholder if model doesn't exist or query fails

    already_saved_minutes = application_count * 20

    context = {
        'username': username,
        'job_matches_count': application_count, # Replace with actual data
        'already_saved_minutes': already_saved_minutes, # Replace with actual data
        'application_count': 0, # Replace with actual data
        'tips_to_improve_count': 0, # Replace with actual data
        'user_cv_text': user_cv_text,
        'user_preferences_text': user_preferences_text,
        'user_email_text': user_email_text, # Add email to context
    }
    return render(request, 'matcher/profile_page.html', context)

def job_detail_page(request, job_id, match_session_id=None):
    job = get_object_or_404(JobListing, id=job_id)
    skills_text = request.session.get('skills_text', '')
    saved_job_instance = None
    parsed_insights = [] # Initialize parsed_insights
    
    # Ensure session key exists
    if not request.session.session_key:
        request.session.create()
    user_session_key = request.session.session_key

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

    try:
        saved_job_instance = SavedJob.objects.get(job_listing=job, user_session_key=user_session_key)
    except SavedJob.DoesNotExist:
        # If it doesn't exist, we might want to create one with default 'interested' status
        # Or let the form create it on first POST with a specific action like "Save for later"
        pass # Form will be unbound if instance is None

    if request.method == 'POST':
        # If saved_job_instance is None, a new SavedJob will be created by the form if commit=False is handled correctly
        form = SavedJobForm(request.POST, instance=saved_job_instance)
        if form.is_valid():
            saved_job = form.save(commit=False)
            saved_job.job_listing = job
            saved_job.user_session_key = user_session_key
            # If it's a new instance and status wasn't explicitly set by user, 
            # but they submitted the form, we can default to 'applied' or keep 'interested'
            # For now, the form's default or user's choice will prevail.
            saved_job.save()
            # Optionally, add a success message with Django messages framework
            # Redirect to the correct URL (with or without session_id) based on how the page was accessed
            if match_session_id: # match_session_id is the one passed to the view from URL
                return redirect('matcher:job_detail_page', job_id=job.id, match_session_id=match_session_id)
            else:
                return redirect('matcher:job_detail_page_no_session', job_id=job.id)
    else:
        form = SavedJobForm(instance=saved_job_instance)

    # If job_match_analysis was not found, but job object itself might have insights_for_match
    # (e.g. from a different source or default value), try parsing that.
    if not parsed_insights and hasattr(job, 'insights_for_match') and job.insights_for_match:
        parsed_insights = parse_and_prepare_insights_for_template(job.insights_for_match)

    context = {
        'job': job,
        'skills_text': skills_text,
        'saved_job_form': form,
        'saved_job_instance': saved_job_instance, # For displaying current status if needed outside form
        'status_choices': SavedJob.STATUS_CHOICES, # Pass choices for direct iteration if needed
        'job_match_analysis': job_match_analysis,
        'current_match_session_id_for_url': session_id_to_use, 
        'active_match_session': active_match_session, # Pass the session object for breadcrumb
        'parsed_insights_list': parsed_insights # Add parsed insights to context
    }
    return render(request, 'matcher/job_detail.html', context)

def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    skills_text = request.session.get('skills_text', '')
    cover_letter_content = ""
    generation_error = False

    if not skills_text:
        cover_letter_content = "Please enter your skills on the main page first to generate a more personalized cover letter."
        generation_error = True
    else:
        cover_letter_content = gemini_utils.generate_cover_letter(skills_text, job)
        if not cover_letter_content.startswith("(Error generating") and \
           not cover_letter_content.startswith("Could not generate") and \
           not cover_letter_content.startswith("Please enter your skills"):
            
            if not request.session.session_key:
                request.session.create()
            user_session_key = request.session.session_key

            # First, ensure SavedJob instance exists or create it, and set status to 'applied'
            try:
                saved_job = SavedJob.objects.get(job_listing=job, user_session_key=user_session_key)
            except SavedJob.DoesNotExist:
                saved_job = SavedJob(job_listing=job, user_session_key=user_session_key)
            
            saved_job.status = 'applied' # Explicitly set status
            new_note = f'Cover letter generated on {timezone.now().strftime("%Y-%m-%d %H:%M")}.'
            if saved_job.notes:
                saved_job.notes += f"\n{new_note}"
            else:
                saved_job.notes = new_note
            saved_job.save() # Save SavedJob instance first

            # Now, create or update the CoverLetter instance
            CoverLetter.objects.update_or_create(
                saved_job=saved_job,
                defaults={'content': cover_letter_content}
            )
            # from django.contrib import messages
            # messages.success(request, f"Cover letter generated and saved. Job status updated to 'Applied'.")
        else:
            generation_error = True
            # Further error logging or specific user messages could be added here
    
    context = {
        'job': job,
        'cover_letter_content': cover_letter_content,
        'skills_text': skills_text,
        'generation_error': generation_error
    }
    return render(request, 'matcher/cover_letter_page.html', context)
def my_applications_page(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create() # Create session if not exists
        session_key = request.session.session_key
        # If session_key is still None after create(), no applications can be shown.
        # This scenario is unlikely with standard Django session backends.
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

    # Prepare status choices for tabs, including an "All" option.
    # The value for "All" is an empty string for cleaner URLs (e.g., /my_applications/?status=)
    tab_status_choices = [('', 'All')] + list(SavedJob.STATUS_CHOICES)

    # Fetch all saved jobs for the user to calculate counts for each status
    all_user_saved_jobs = SavedJob.objects.filter(user_session_key=session_key)

    # Calculate counts for each status
    status_counts_data = all_user_saved_jobs.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in status_counts_data}
    status_counts[''] = all_user_saved_jobs.count() # Total count for the 'All' tab

    # Filter jobs based on selected_status
    # If selected_status is None (no query param) or an empty string (from 'All' tab), show all.
    # If selected_status is a specific status, filter by it.
    if selected_status and selected_status in [s[0] for s in SavedJob.STATUS_CHOICES]:
        saved_jobs_query = all_user_saved_jobs.filter(status=selected_status)
    else:
        # If selected_status is not a valid status string (e.g. None, empty, or invalid),
        # default to showing all. And ensure selected_status reflects 'All' for the template.
        selected_status = '' 
        saved_jobs_query = all_user_saved_jobs

    # Apply prefetching and ordering to the (potentially filtered) queryset
    saved_jobs_filtered = saved_jobs_query.select_related('job_listing')\
                                       .prefetch_related(Prefetch('cover_letter', queryset=CoverLetter.objects.all()))\
                                       .order_by('-updated_at')

    saved_jobs_with_forms_and_letters = []
    for saved_job_instance in saved_jobs_filtered:
        form = SavedJobForm(instance=saved_job_instance)
        cover_letter = getattr(saved_job_instance, 'cover_letter', None)
        saved_jobs_with_forms_and_letters.append({
            'saved_job': saved_job_instance,
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
        return JsonResponse({'success': False, 'message': 'Session not found. Please interact with the site first.'}, status=401)

    try:
        data = json.loads(request.body)
        new_status = data.get('status')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload.'}, status=400)

    if not new_status:
        return JsonResponse({'success': False, 'message': 'Status not provided.'}, status=400)

    # Validate if the new_status is a valid choice in SavedJob.STATUS_CHOICES
    valid_statuses = [choice[0] for choice in SavedJob.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'message': f'Invalid status value: {new_status}.'}, status=400)

    try:
        job_listing = get_object_or_404(JobListing, id=job_id)
        
        saved_job, created = SavedJob.objects.update_or_create(
            job_listing=job_listing,
            user_session_key=session_key,
            defaults={'status': new_status}
        )
        
        if created:
            message = f"Status for job '{job_listing.job_title}' set to '{saved_job.get_status_display()}'."
        else:
            message = f"Status for job '{job_listing.job_title}' updated to '{saved_job.get_status_display()}'."
            
        return JsonResponse({'success': True, 'message': message, 'new_status': saved_job.get_status_display(), 'job_id': job_id})

    except JobListing.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Job listing not found.'}, status=404)
    except Exception as e:
        # Log the exception e for server-side review
        print(f"Error updating job status: {e}") # Basic logging
        return JsonResponse({'success': False, 'message': 'An unexpected error occurred while updating status.'}, status=500)


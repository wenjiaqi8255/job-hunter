from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse # Import reverse for redirect
from .models import JobListing, MatchSession, MatchedJob, SavedJob, CoverLetter # Added CoverLetter
from .forms import SavedJobForm # Added SavedJobForm
from . import gemini_utils
from django.db import transaction
import uuid # For validating UUID from GET param
from django.utils import timezone
from django.contrib import messages
import json # For storing profile as JSON
from django.db.models import Prefetch, OuterRef, Subquery, Exists, Q
from uuid import UUID # For validating UUIDs
import random # Added for random sampling

# Create your views here.

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
        
        # Phase 4.1 Step 2: Call the new match_jobs with the structured profile
        # Fetch all jobs first
        all_job_listings = list(JobListing.objects.all())
        
        # Sample 10 random jobs if more than 10 exist, otherwise use all
        if len(all_job_listings) > 10: 
            # Development and testing purpose
            job_listings_for_api = random.sample(all_job_listings, 10)
        else:
            job_listings_for_api = all_job_listings
        
        job_matches_from_api = gemini_utils.match_jobs(structured_profile_dict, job_listings_for_api)

        new_match_session = MatchSession.objects.create(
            skills_text=user_cv_text_input, # Storing CV here
            user_preferences_text=user_preferences_text_input, # Storing preferences
            structured_user_profile_json=structured_profile_dict # Storing structured profile
        )
        current_match_session_id_str = str(new_match_session.id)
        request.session['last_match_session_id'] = current_match_session_id_str

        for match_item in job_matches_from_api:
            MatchedJob.objects.create(
                match_session=new_match_session,
                job_listing=match_item['job'],
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
                processed_job_matches.append({
                    'job': mj.job_listing,
                    'score': mj.score, 
                    'reason': mj.reason, 
                    'insights': mj.insights, # Now directly accessing from model
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

def job_detail_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    skills_text = request.session.get('skills_text', '')
    saved_job_instance = None
    
    # Ensure session key exists
    if not request.session.session_key:
        request.session.create()
    user_session_key = request.session.session_key

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
            return redirect('matcher:job_detail_page', job_id=job.id) # Redirect to same page to show updated data / clear POST
    else:
        form = SavedJobForm(instance=saved_job_instance)

    context = {
        'job': job,
        'skills_text': skills_text,
        'saved_job_form': form,
        'saved_job_instance': saved_job_instance, # For displaying current status if needed outside form
        'status_choices': SavedJob.STATUS_CHOICES # Pass choices for direct iteration if needed
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
    if not request.session.session_key:
        request.session.create() # Ensure session exists
        # If no session, there are no saved jobs for this user yet.
        # Redirect to main page or show a message?
        # For now, proceed, it will just show an empty list.
    user_session_key = request.session.session_key

    saved_jobs_query = SavedJob.objects.filter(user_session_key=user_session_key).select_related(
        'job_listing', 'cover_letter' # Eager load related job and cover letter
    ).order_by('-updated_at')

    selected_status = request.GET.get('status', '')
    if selected_status:
        saved_jobs_query = saved_jobs_query.filter(status=selected_status)
    
    status_choices_for_template = SavedJob.STATUS_CHOICES
    # Add an 'all' option for the filter tabs
    all_statuses_option = [('', 'All Applications')] + list(status_choices_for_template)

    # Count for each status for summary (optional, but good for UI)
    status_counts = {status_val: SavedJob.objects.filter(user_session_key=user_session_key, status=status_val).count() for status_val, _ in status_choices_for_template}
    status_counts[''] = SavedJob.objects.filter(user_session_key=user_session_key).count() # Total count

    context = {
        'saved_jobs': saved_jobs_query,
        'status_choices': all_statuses_option, # For filter tabs
        'selected_status': selected_status,
        'status_counts': status_counts
    }
    return render(request, 'matcher/my_applications.html', context)

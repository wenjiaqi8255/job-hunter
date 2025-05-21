from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse # Import reverse for redirect
from .models import JobListing, MatchSession, MatchedJob
from . import gemini_utils
from django.db import transaction
import uuid # For validating UUID from GET param

# Create your views here.

def main_page(request):
    all_jobs = JobListing.objects.all()
    skills_text_from_session = "" # Default to empty
    processed_job_matches_for_template = []
    current_match_session_id_uuid = None # Store as UUID object for comparison

    # Handle displaying a specific session if session_id is in GET
    session_id_from_get = request.GET.get('session_id')

    if request.method == 'POST':
        skills_text_input = request.POST.get('skills_text', '')
        # Store in Django session for immediate feedback if something goes wrong before redirect
        request.session['skills_text'] = skills_text_input 
        skills_text_from_session = skills_text_input # Use this for the current view rendering before redirect

        raw_matches_from_gemini = gemini_utils.match_jobs(skills_text_input, list(all_jobs))
        new_match_session = None

        if raw_matches_from_gemini:
            try:
                with transaction.atomic():
                    new_match_session = MatchSession.objects.create(skills_text=skills_text_input)
                    
                    for match_data in raw_matches_from_gemini:
                        MatchedJob.objects.create(
                            match_session=new_match_session,
                            job_listing=match_data['job'], 
                            score=match_data['score'],
                            reason=match_data['reason']
                        )
                
                return redirect(reverse('matcher:main_page') + f'?session_id={new_match_session.id}')

            except Exception as e:
                print(f"Error saving match session to database: {e}")
                processed_job_matches_for_template = [] 
                if raw_matches_from_gemini: 
                     for match_data in raw_matches_from_gemini:
                        processed_job_matches_for_template.append({
                            'job': match_data['job'],
                            'score': match_data['score'],
                            'reason': match_data['reason']
                        })
        else: 
            pass
            
    elif session_id_from_get:
        try:
            current_match_session_id_uuid = uuid.UUID(session_id_from_get) 
            selected_session = MatchSession.objects.get(id=current_match_session_id_uuid)
            skills_text_from_session = selected_session.skills_text
            matched_jobs_from_db = selected_session.matched_jobs.all().order_by('-score')
            for mj_db in matched_jobs_from_db:
                processed_job_matches_for_template.append({
                    'job': mj_db.job_listing,
                    'score': mj_db.score,
                    'reason': mj_db.reason
                })
        except (MatchSession.DoesNotExist, ValueError): 
            return redirect(reverse('matcher:main_page'))
    else:
        skills_text_from_session = request.session.get('skills_text', '') 
        processed_job_matches_for_template = []

    match_history_for_sidebar = MatchSession.objects.all().order_by('-matched_at')
    selected_session_object = None
    if current_match_session_id_uuid:
        try:
            selected_session_object = MatchSession.objects.get(id=current_match_session_id_uuid)
        except MatchSession.DoesNotExist:
            pass # Should have been caught earlier, but defensive

    context = {
        'jobs': all_jobs, 
        'processed_job_matches': processed_job_matches_for_template, 
        'skills_text': skills_text_from_session, 
        'match_history': match_history_for_sidebar, 
        'current_match_session_id': str(current_match_session_id_uuid) if current_match_session_id_uuid else None,
        'selected_session_object': selected_session_object,
        'all_jobs_count': all_jobs.count()
    }
    return render(request, 'matcher/main_page.html', context)

def job_detail_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    
    skills_text = request.session.get('skills_text', '')

    context = {
        'job': job,
        'skills_text': skills_text
    }
    return render(request, 'matcher/job_detail.html', context)

def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    skills_text = request.session.get('skills_text', '')

    if not skills_text:
        cover_letter_content = "Please enter your skills on the main page first to generate a more personalized cover letter."
    else:
        cover_letter_content = gemini_utils.generate_cover_letter(skills_text, job)
    
    context = {
        'job': job,
        'cover_letter_content': cover_letter_content,
        'skills_text': skills_text 
    }
    return render(request, 'matcher/cover_letter_page.html', context)

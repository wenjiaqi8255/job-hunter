from django.shortcuts import render, redirect, get_object_or_404
from .models import JobListing
from . import gemini_utils

# Create your views here.

def main_page(request):
    jobs = JobListing.objects.all()
    # This will now hold the direct output from gemini_utils.match_jobs
    # which is a list of dicts: [{'job': job_obj, 'score': score_val, 'reason': reason_str}, ...]
    # It will be sorted by score from gemini_utils
    processed_job_matches = None 

    if request.method == 'POST':
        skills_text = request.POST.get('skills_text', '')
        request.session['skills_text'] = skills_text
        
        # Call the enhanced (simulated) matching function
        processed_job_matches = gemini_utils.match_jobs(skills_text, list(jobs))
        
    context = {
        'jobs': jobs, # Original list of all jobs, for the "All Available Job Listings" section
        'processed_job_matches': processed_job_matches, # Sorted & scored matches from Gemini sim
        'skills_text': request.session.get('skills_text', '')
    }
    return render(request, 'matcher/main_page.html', context)

def job_detail_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    
    # The reason_for_match should ideally come from the matching process if this job was part of a match.
    # If accessed directly, it might be blank unless pre-filled or generated on-the-fly.
    # For now, we retrieve it from the model. If it's blank, the template should handle it.
    
    # We also need the user's skills to potentially pass to cover letter generation
    skills_text = request.session.get('skills_text', '')

    context = {
        'job': job,
        'skills_text': skills_text
        # 'reason_for_match': job.reason_for_match or "Matching analysis not available for this view."
    }
    return render(request, 'matcher/job_detail.html', context)

def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    skills_text = request.session.get('skills_text', '')

    if not skills_text:
        # Maybe redirect to main_page with a message to input skills first
        # For now, just show an error or a very generic letter
        # Or pass a flag to the template to show a message
        cover_letter_content = "Please enter your skills on the main page first to generate a more personalized cover letter."
    else:
        # Call the Gemini util function for cover letter generation
        cover_letter_content = gemini_utils.generate_cover_letter(skills_text, job)
    
    # Store generated letter in session temporarily if needed for other actions (e.g. edit)
    # request.session['last_cover_letter'] = cover_letter_content

    context = {
        'job': job,
        'cover_letter_content': cover_letter_content,
        'skills_text': skills_text # For display or further use
    }
    return render(request, 'matcher/cover_letter_page.html', context)

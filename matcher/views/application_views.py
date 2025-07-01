"""
求职申请相关视图
包括求职信生成、简历定制、申请管理等
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.conf import settings

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import json
import textwrap

from ..models import JobListing, SavedJob, CoverLetter, CustomResume, UserProfile
from .. import gemini_utils
from ..services.supabase_saved_job_service import (
    get_supabase_saved_job,
    create_supabase_saved_job,
    update_supabase_saved_job_status,
    list_supabase_saved_jobs
)


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
                # First ensure we have a SavedJob for this user and job
                saved_job, created = SavedJob.objects.get_or_create(
                    user=user,
                    job_listing=job,
                    defaults={'status': 'viewed'}
                )
                
                # Then create or update the cover letter
                cover_letter, cl_created = CoverLetter.objects.update_or_create(
                    saved_job=saved_job,
                    defaults={"content": cover_letter_content}
                )
                has_existing_cover_letter = True
    else:
        # GET: 优先查历史
        try:
            saved_job = SavedJob.objects.get(user=user, job_listing=job)
            cover_letter_obj = CoverLetter.objects.get(saved_job=saved_job)
            cover_letter_content = cover_letter_obj.content
            has_existing_cover_letter = True
        except (SavedJob.DoesNotExist, CoverLetter.DoesNotExist):
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
                    # First ensure we have a SavedJob
                    saved_job, created = SavedJob.objects.get_or_create(
                        user=user,
                        job_listing=job,
                        defaults={'status': 'viewed'}
                    )
                    
                    # Then create the cover letter
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

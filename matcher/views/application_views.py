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


@login_required
def generate_cover_letter_page(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    user_cv_text = user_profile.user_cv_text or ""
    cover_letter_content = ""
    generation_error = False
    has_existing_cover_letter = False

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
    return render(request, 'matcher/cover_letter_page.html', context)


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
            # No existing resume,自动生成并保存
            if not user_cv_text:
                custom_resume_content = "Please complete your CV in your profile before generating a custom resume."
                generation_error = True
            else:
                custom_resume_content = gemini_utils.generate_custom_resume(user_cv_text, job_dict)
                if not custom_resume_content.startswith("(Error generating"):
                    # Save the newly generated resume
                    CustomResume.objects.create(
                        user=user,
                        job_listing=job,
                        content=custom_resume_content
                    )
                    has_existing_resume = True
                else:
                    generation_error = True

    context = {
        'job': job,
        'custom_resume_content': custom_resume_content,
        'generation_error': generation_error,
        'user_cv_text': user_cv_text, # Pass CV text for display
        'has_existing_resume': has_existing_resume, # Pass flag to template
    }
    return render(request, 'matcher/custom_resume_page.html', context)


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
def download_cover_letter(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    
    # CoverLetter is linked via SavedJob
    saved_job = get_object_or_404(SavedJob, job_listing=job, user=user)
    cover_letter = get_object_or_404(CoverLetter, saved_job=saved_job)
    
    cover_letter_content = cover_letter.content

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

    for paragraph in cover_letter_content.split('\n'):
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
    filename = f"cover_letter_{job.id}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)


@login_required
def my_applications_page(request):
    """
    Displays a list of jobs the user has saved, with filtering by status.
    Now solely relies on the local Django `SavedJob` model.
    """
    status_filter = request.GET.get('status')

    saved_jobs_query = SavedJob.objects.filter(user=request.user).select_related('job_listing')

    if status_filter and status_filter in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
        saved_jobs_query = saved_jobs_query.filter(status=status_filter)

    # Order by updated_at descending to show the most recently updated jobs first
    saved_jobs = saved_jobs_query.order_by('-updated_at')

    status_choices = SavedJob.STATUS_CHOICES
    
    # For the right rail summary
    status_counts = {status[0]: 0 for status in status_choices}
    all_user_jobs = SavedJob.objects.filter(user=request.user)
    for job in all_user_jobs:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1

    context = {
        'saved_jobs': saved_jobs,
        'status_choices': status_choices,
        'current_status': status_filter,
        'status_counts': status_counts,
    }
    return render(request, 'matcher/my_applications.html', context)


@login_required
def update_job_application_status(request, job_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

        job_listing = get_object_or_404(JobListing, id=job_id)

        if not new_status or new_status not in [choice[0] for choice in SavedJob.STATUS_CHOICES]:
            return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)

        saved_job, created = SavedJob.objects.update_or_create(
            user=request.user,
            job_listing=job_listing,
            defaults={'status': 'not_applied'}
        )

        if not created:
            saved_job.status = new_status
            saved_job.save(update_fields=['status'])

        return JsonResponse({
            'success': True, 
            'new_status_display': saved_job.get_status_display(),
            'new_status': saved_job.status
        })
    return JsonResponse({'success': False, 'error': 'Only POST method is allowed.'}, status=405)

"""
工作详情页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from uuid import UUID

from ..models import JobListing, MatchSession, MatchedJob, SavedJob, UserProfile
from ..utils import parse_and_prepare_insights_for_template, parse_anomaly_analysis
from ..services.job_listing_service import fetch_anomaly_analysis_for_jobs_from_supabase


def job_detail_page(request, job_id, match_session_id=None):
    job = get_object_or_404(JobListing, id=job_id)
    user = request.user
    user_profile = None
    user_cv_text = ""
    saved_job = None
    active_match_session = None
    reason_for_match = None
    tips_for_match = None
    parsed_insights = []

    if user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_cv_text = user_profile.user_cv_text or ""
        
        # This is the key logic: when a user views a job, we create a saved record
        # or update its status to 'viewed' if it was 'not_applied'.
        saved_job, created = SavedJob.objects.get_or_create(
            user=user, 
            job_listing=job,
            # Defaults are only used on creation
            defaults={'status': 'viewed'}
        )
        
        # If the job was already saved and its status was 'not_applied', update it to 'viewed'.
        if not created and saved_job.status == 'not_applied':
            saved_job.status = 'viewed'
            saved_job.save(update_fields=['status'])

        session_id_to_use = match_session_id

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
        
        job_listing = get_object_or_404(JobListing, pk=job_id)

        # Use update_or_create to handle both saving and updating
        saved_job, created = SavedJob.objects.update_or_create(
            user=request.user,
            job_listing=job_listing,
            defaults={'status': new_status or 'not_applied', 'notes': notes}
        )
        
        if created:
            messages.success(request, "Application saved.")
        else:
            messages.success(request, "Application status updated.")

        if active_match_session:
            return redirect('matcher:job_detail_page', job_id=job.id, match_session_id=active_match_session.id)
        else:
            return redirect('matcher:job_detail_page_no_session', job_id=job.id)

    status_choices = SavedJob.STATUS_CHOICES

    context = {
        'job': job,
        'saved_job': saved_job,
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

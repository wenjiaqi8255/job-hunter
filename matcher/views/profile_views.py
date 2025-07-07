"""
用户个人资料相关视图
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

import fitz  # PyMuPDF

from ..models import UserProfile, SavedJob
from ..services.experience_service import get_user_experiences


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

    # Fetch saved jobs count from Django's SavedJob model
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

"""
工作经验相关视图
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

import json

from ..services.experience_service import get_user_experiences, delete_experience as delete_experience_from_supabase


@login_required
def experience_list(request):
    """Lists all work experiences for the current user from Supabase."""
    user = request.user
    # The user object is no longer needed for authorization, RLS handles it
    experiences = get_user_experiences(request.supabase)
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
        # The user object is no longer needed for authorization, RLS handles it
        delete_experience_from_supabase(request.supabase, experience_id)
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

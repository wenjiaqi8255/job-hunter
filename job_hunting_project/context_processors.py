"""
Context processors for the job_hunting_project.
"""
from django.conf import settings


def supabase_config(request):
    """
    Context processor to make Supabase configuration available in templates.
    """
    return {
        'supabase_url': getattr(settings, 'SUPABASE_URL', ''),
        'supabase_key': getattr(settings, 'SUPABASE_KEY', ''),
    }

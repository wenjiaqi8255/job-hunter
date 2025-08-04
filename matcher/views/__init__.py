# Views package for the matcher app
from .auth_views import google_login, google_callback, logout_view, api_check_auth, process_oauth_tokens
from .main_views import main_page
from .profile_views import profile_page
from .job_views import job_detail_page
from .application_views import (
    generate_cover_letter_page, 
    generate_custom_resume_page,
    download_custom_resume,
    download_cover_letter,
    my_applications_page,
    update_job_application_status
)

__all__ = [
    'google_login',
    'google_callback', 
    'logout_view',
    'api_check_auth',
    'process_oauth_tokens',
    'main_page',
    'profile_page',
    'job_detail_page',
    'generate_cover_letter_page',
    'generate_custom_resume_page', 
    'download_custom_resume',
    'download_cover_letter',
    'my_applications_page',
    'update_job_application_status'
]

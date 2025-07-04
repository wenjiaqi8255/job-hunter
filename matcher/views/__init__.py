# Views package for the matcher app
from .auth_views import (
    login_page, 
    api_verify_token, api_test_protected, api_public_test, token_required, get_user_from_token,
    api_test_page, api_user_saved_jobs, api_user_profile,
    api_user_status, api_user_status_public, api_save_job, api_saved_jobs
)
from .main_views import main_page
from .profile_views import profile_page
from .job_views import job_detail_page
from .application_views import (
    generate_cover_letter_page, 
    generate_custom_resume_page,
    download_custom_resume,
    my_applications_page,
    update_job_application_status
)
from .experience_views import experience_list, experience_delete, experience_completed_callback, api_user_experiences

__all__ = [
    'login_page',
    'api_verify_token',
    'api_test_protected',
    'api_public_test',
    'token_required',
    'get_user_from_token',
    'api_test_page',
    'api_user_saved_jobs',
    'api_user_profile',
    'api_user_status',
    'api_user_status_public', 
    'api_save_job',
    'api_saved_jobs',
    'main_page',
    'profile_page',
    'job_detail_page',
    'generate_cover_letter_page',
    'generate_custom_resume_page', 
    'download_custom_resume',
    'my_applications_page',
    'update_job_application_status',
    'experience_list',
    'experience_delete',
    'experience_completed_callback',
    'api_user_experiences',
]

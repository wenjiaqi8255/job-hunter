# Views package for the matcher app
from .auth_views import (
    login_page, 
    api_verify_token, api_test_protected, api_public_test, token_required, get_user_from_token,
    api_test_page
)
from .main_views import main_page, api_trigger_match, api_sync_health_check, api_get_match_history, api_get_match_session, api_get_latest_match, api_get_session_by_id
from .profile_views import profile_page
from .job_views import job_detail_page
from .application_views import (
    generate_cover_letter_page, 
    generate_custom_resume_page,
    my_applications_page,
    update_job_application_status,
    api_generate_cover_letter,
    api_get_cover_letter
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
    'main_page',
    'api_trigger_match',
    'api_sync_health_check',
    'api_get_match_history',
    'api_get_match_session',
    'api_get_session_by_id',
    'api_get_latest_match',
    'profile_page',
    'job_detail_page',
    'generate_cover_letter_page',
    'generate_custom_resume_page', 
    'my_applications_page',
    'update_job_application_status',
    'api_generate_cover_letter',
    'api_get_cover_letter',
    'experience_list',
    'experience_delete',
    'experience_completed_callback',
    'api_user_experiences',
]

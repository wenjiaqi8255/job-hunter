from django.urls import path
from . import views
from .views import auth_views as auth_views_module
from .views import profile_views, job_views
from .views import main_views

app_name = 'matcher'

urlpatterns = [
    # 主页面
    path('', views.main_page, name='main_page'),
    
    # 工作相关页面
    path('job/<str:job_id>/session/<uuid:match_session_id>/', job_views.job_detail_page, name='job_detail_page'),
    path('job/<str:job_id>/', job_views.job_detail_page, name='job_detail_page_no_session'),
    path('job/<str:job_id>/generate-cover-letter/', views.generate_cover_letter_page, name='generate_cover_letter_page'),
    path('job/<str:job_id>/generate-custom-resume/', views.generate_custom_resume_page, name='generate_custom_resume_page'),
    path('job/<str:job_id>/update_status/', views.update_job_application_status, name='update_job_application_status'),
    path('job/<str:job_id>/download-custom-resume-pdf/', views.download_custom_resume, name='download_custom_resume_pdf'),
    
    # 用户相关页面
    path('my-applications/', views.my_applications_page, name='my_applications_page'),
    path('profile/', profile_views.profile_page, name='profile_page'),
    
    # 经历相关页面
    path('experiences/', views.experience_list, name='experience_list'),
    path('experiences/<uuid:experience_id>/delete/', views.experience_delete, name='experience_delete'),
    path('api/experience-completed-callback/', views.experience_completed_callback, name='experience_completed_callback'),
    path('api/user-experiences/', views.api_user_experiences, name='api_user_experiences'),
    
    # ==========================================================================
    # 重新组织的API端点 - 按业务领域分组
    # ==========================================================================
    
    # 认证相关API端点 - auth_views.py
    path('api/auth/verify-token/', auth_views_module.api_verify_token, name='api_verify_token'),
    # path('api/auth/test-protected/', auth_views_module.api_test_protected, name='api_test_protected'),
    # path('api/auth/test-public/', auth_views_module.api_public_test, name='api_public_test'),
    # path('api-test/', auth_views_module.api_test_page, name='api_test_page'),
    
    # 用户资料相关API端点 - profile_views.py
    path('api/profile/', profile_views.api_user_profile, name='api_user_profile'),
    path('api/profile/analyze/', profile_views.api_user_cv_analysis, name='api_user_cv_analysis'),
    path('api/profile/status/', profile_views.api_user_status, name='api_user_status'),
    path('api/profile/status-public/', profile_views.api_user_status_public, name='api_user_status_public'),
    path('api/profile/saved-jobs/', profile_views.api_user_saved_jobs, name='api_user_saved_jobs'),
    
    # 工作相关API端点 - job_views.py
    path('api/jobs/', job_views.api_jobs_list, name='api_jobs_list'),
    path('api/jobs/<str:job_id>/', job_views.api_job_detail, name='api_job_detail'),
    path('api/jobs/save/', job_views.api_save_job, name='api_save_job'),
    path('api/jobs/saved/', job_views.api_saved_jobs, name='api_saved_jobs'),
    
    # 匹配相关API端点 - main_views.py (新的语义化命名)
    path('api/match/trigger/', main_views.api_trigger_match, name='api_trigger_match'),
    path('api/match/latest/', main_views.api_get_latest_match, name='api_get_latest_match'),
    path('api/match/history/', main_views.api_get_match_history, name='api_get_match_history'),
    path('api/match/session/<str:job_match_id>/', main_views.api_get_match_session, name='api_get_match_session'),
    path('api/match/sessions/<str:session_id>/', main_views.api_get_session_by_id, name='api_get_session_by_id'),
    
    # 系统监控API端点 - main_views.py
    path('api/sync-health/', main_views.api_sync_health_check, name='api_sync_health_check'),
    
    # ==========================================================================
    # 兼容性保留的旧API端点 - 逐步废弃
    # ==========================================================================
    
    # 旧的API端点，保留以确保向后兼容
    path('api/user-status/', profile_views.api_user_status, name='api_user_status_legacy'),
    path('api/user-status-public/', profile_views.api_user_status_public, name='api_user_status_public_legacy'),
    path('api/user-profile/', profile_views.api_user_profile, name='api_user_profile_legacy'),
    path('api/cv-analysis/', profile_views.api_user_cv_analysis, name='api_user_cv_analysis_legacy'),
    path('api/match-jobs/', main_views.api_trigger_match, name='api_match_jobs_legacy'),  # 重定向到新端点
    path('api/match-history/', main_views.api_get_match_history, name='api_match_history_legacy'),  # 重定向到新端点
    path('api/match-history/job/<str:job_match_id>/', main_views.api_get_match_session, name='api_match_job_details_legacy'),  # 重定向到新端点
]
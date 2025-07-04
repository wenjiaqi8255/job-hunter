from django.urls import path
from . import views
from .views import auth_views as auth_views_module

app_name = 'matcher'

urlpatterns = [
    # 主页面
    path('', views.main_page, name='main_page'),
    
    # 工作相关页面
    path('job/<str:job_id>/session/<uuid:match_session_id>/', views.job_detail_page, name='job_detail_page'),
    path('job/<str:job_id>/', views.job_detail_page, name='job_detail_page_no_session'),
    path('job/<str:job_id>/generate-cover-letter/', views.generate_cover_letter_page, name='generate_cover_letter_page'),
    path('job/<str:job_id>/generate-custom-resume/', views.generate_custom_resume_page, name='generate_custom_resume_page'),
    path('job/<str:job_id>/update_status/', views.update_job_application_status, name='update_job_application_status'),
    path('job/<str:job_id>/download-custom-resume-pdf/', views.download_custom_resume, name='download_custom_resume_pdf'),
    
    # 用户相关页面
    path('my-applications/', views.my_applications_page, name='my_applications_page'),
    path('profile/', views.profile_page, name='profile_page'),
    
    # 经历相关页面
    path('experiences/', views.experience_list, name='experience_list'),
    path('experiences/<uuid:experience_id>/delete/', views.experience_delete, name='experience_delete'),
    path('api/experience-completed-callback/', views.experience_completed_callback, name='experience_completed_callback'),
    path('api/user-experiences/', views.api_user_experiences, name='api_user_experiences'),
    
    # 认证相关API端点
    path('api/verify-token/', auth_views_module.api_verify_token, name='api_verify_token'),
    path('api/test-protected/', auth_views_module.api_test_protected, name='api_test_protected'),
    path('api/test-public/', auth_views_module.api_public_test, name='api_public_test'),
    path('api/user-saved-jobs/', auth_views_module.api_user_saved_jobs, name='api_user_saved_jobs'),
    path('api/user-profile/', auth_views_module.api_user_profile, name='api_user_profile'),
    path('api-test/', auth_views_module.api_test_page, name='api_test_page'),
    
    # 新增的核心API端点
    path('api/user-status/', auth_views_module.api_user_status, name='api_user_status'),
    path('api/user-status-public/', auth_views_module.api_user_status_public, name='api_user_status_public'),
    path('api/jobs/save/', auth_views_module.api_save_job, name='api_save_job'),
    path('api/jobs/saved/', auth_views_module.api_saved_jobs, name='api_saved_jobs'),
]
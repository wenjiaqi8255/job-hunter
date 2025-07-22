from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from matcher.views.main_views import (
    main_page,  
    upload_cv_and_match, 
    start_new_match_session,
    all_matches_page
)
from matcher.views.job_views import job_detail_page
from .views.auth_views import register_view  # 新增注册视图导入
from matcher.views.profile_views import tips_to_improve_page  # 新增tips页面view导入

app_name = 'matcher'

urlpatterns = [
    # URL to display the login page. This is the target for failed auth redirects.
    path('login/', auth_views.LoginView.as_view(template_name='matcher/login.html'), name='login_page'),

    # NOTE: OAuth routes are now defined in the main project urls.py to avoid i18n conflicts

    # Job and session management
    path('', main_page, name='main_page'),
    path('job/<str:job_id>/', job_detail_page, name='job_detail_page_no_session'),
    path('job/<str:job_id>/session/<uuid:match_session_id>/', job_detail_page, name='job_detail_page'),
    path('matches/', all_matches_page, name='all_matches'),

    # Actions
    path('match/new/', start_new_match_session, name='start_new_match_session'),
    path('upload_cv_and_match/', upload_cv_and_match, name='upload_cv_and_match'),
    path('job/<str:job_id>/generate-cover-letter/', views.generate_cover_letter_page, name='generate_cover_letter_page'),
    path('job/<str:job_id>/generate-custom-resume/', views.generate_custom_resume_page, name='generate_custom_resume_page'),
    path('my-applications/', views.my_applications_page, name='my_applications_page'),
    path('job/<str:job_id>/update_status/', views.update_job_application_status, name='update_job_application_status'),
    path('profile/', views.profile_page, name='profile_page'),
    path('tips-to-improve/', tips_to_improve_page, name='tips_to_improve'),  # 新增tips页面路由

    # Experience Pool URLs
    path('experiences/', views.experience_list, name='experience_list'),
    path('experiences/<uuid:experience_id>/delete/', views.experience_delete, name='experience_delete'),
    
    # URL for N8n to call when it's done
    path('api/experience-completed-callback/', views.experience_completed_callback, name='experience_completed_callback'),

    path('job/<str:job_id>/download-custom-resume-pdf/', views.download_custom_resume, name='download_custom_resume_pdf'),
    path('job/<str:job_id>/download-cover-letter-pdf/', views.download_cover_letter, name='download_cover_letter_pdf'),
    
    # API 端点
    path('api/check-auth/', views.api_check_auth, name='api_check_auth'),
    path('register/', register_view, name='register'),  # 新增注册路由
]
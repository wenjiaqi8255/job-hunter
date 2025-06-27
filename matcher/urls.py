from django.urls import path
from . import views

app_name = 'matcher'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('job/<str:job_id>/session/<uuid:match_session_id>/', views.job_detail_page, name='job_detail_page'),
    path('job/<str:job_id>/', views.job_detail_page, name='job_detail_page_no_session'),
    path('job/<str:job_id>/generate-cover-letter/', views.generate_cover_letter_page, name='generate_cover_letter_page'),
    path('job/<str:job_id>/generate-custom-resume/', views.generate_custom_resume_page, name='generate_custom_resume_page'),
    path('my-applications/', views.my_applications_page, name='my_applications_page'),
    path('job/<str:job_id>/update_status/', views.update_job_application_status, name='update_job_application_status'),
    path('profile/', views.profile_page, name='profile_page'),

    # Experience Pool URLs
    path('experiences/', views.experience_list, name='experience_list'),
    path('experiences/<uuid:experience_id>/delete/', views.experience_delete, name='experience_delete'),
    
    # URL for N8n to call when it's done
    path('api/experience-completed-callback/', views.experience_completed_callback, name='experience_completed_callback'),

    path('job/<str:job_id>/download-custom-resume-pdf/', views.download_custom_resume, name='download_custom_resume_pdf'),
]
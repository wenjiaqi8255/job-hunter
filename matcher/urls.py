from django.urls import path
from . import views

app_name = 'matcher'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('job/<str:job_id>/', views.job_detail_page, name='job_detail_page'),
    path('job/<str:job_id>/generate-cover-letter/', views.generate_cover_letter_page, name='generate_cover_letter_page'),
] 
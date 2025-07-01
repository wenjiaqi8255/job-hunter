"""
URL configuration for job_hunting_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from matcher.views.auth_views import google_login, google_callback, process_oauth_tokens  # Import specific auth views

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='matcher/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='matcher:main_page'), name='logout'),
    # OAuth routes should not be internationalized to avoid session issues
    path('auth/login/google/', google_login, name='google_login'),
    path('auth/callback/', google_callback, name='google_callback'),
    path('auth/process-oauth-tokens/', process_oauth_tokens, name='process_oauth_tokens'),
]

urlpatterns += i18n_patterns(
    path("", include("matcher.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

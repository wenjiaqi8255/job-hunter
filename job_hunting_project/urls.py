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
from matcher.views.auth_views import login_page

urlpatterns = [
    path('', include('matcher.urls')),  # 默认路由，指向 matcher 应用的 URL
    path('i18n/', include('django.conf.urls.i18n')),
    path("admin/", admin.site.urls),
    
    # 简化登录页面路由 - 仅用于显示登录页面
    path('login/', login_page, name='login'),
]

urlpatterns += i18n_patterns(
    path("", include("matcher.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

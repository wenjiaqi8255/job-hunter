"""
认证相关的视图
处理传统Django认证登录、注册、登出等功能
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.conf import settings
from matcher.models.forms import RegisterForm
import json
import requests


def login_view(request):
    """登录页面，支持多种方式"""
    if request.user.is_authenticated:
        return redirect('/')
    
    context = {
        'google_client_id': settings.GOOGLE_CLIENT_ID,
        'show_traditional_login': True,  # 可以控制是否显示传统登录
    }
    return render(request, 'matcher/login.html', context)


def register_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data.get('email', '')
            
            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'matcher/register.html', {'form': form})
            
            # 创建用户
            user = User.objects.create_user(
                username=username, 
                password=password,
                email=email
            )
            user.save()
            
            # 自动登录
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome!')
                return redirect('matcher:main_page')
            else:
                messages.error(request, 'Registration succeeded but login failed.')
                return redirect('login')
        else:
            # 表单无效，回显错误
            return render(request, 'matcher/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'matcher/register.html', {'form': form})


def logout_view(request):
    """登出视图"""
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('login')


# ===================================
# Google OAuth Server-Side Flow
# ===================================

def google_login(request):
    """
    Redirects the user to Google's authentication page.
    """
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile"
    )
    return redirect(auth_url)


def google_callback(request):
    """
    Handles the callback from Google after user authentication.
    """
    code = request.GET.get('code')
    if not code:
        messages.error(request, "Authentication failed: No code provided.")
        return redirect('login')

    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    access_token = token_json.get('access_token')
    if not access_token:
        messages.error(request, "Failed to retrieve access token from Google.")
        return redirect('login')

    # Get user info
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    user_info_response = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
    user_info = user_info_response.json()

    # Get or create user
    user = get_or_create_google_user(user_info)

    if user:
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! You have successfully logged in with Google.")
        return redirect('matcher:main_page')
    else:
        messages.error(request, "Could not log in with Google. Please try again.")
        return redirect('login')


def get_or_create_google_user(google_user_info):
    """获取或创建Google用户"""
    try:
        email = google_user_info.get('email')
        name = google_user_info.get('name', '')
        picture = google_user_info.get('picture', '')
        
        if not email:
            return None
        
        # 尝试通过email查找用户
        user = User.objects.filter(email=email).first()
        
        if not user:
            # 创建新用户
            username = email.split('@')[0]  # 使用email前缀作为用户名
            # 确保用户名唯一
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
            )
            user.set_unusable_password()  # Google用户不需要密码
            user.save()
        
        return user
    except Exception as e:
        print(f"User creation error: {str(e)}")
        return None


def api_check_auth(request):
    """API：检查认证状态"""
    user_info = get_current_user_info(request)
    return JsonResponse({
        'authenticated': user_info is not None,
        'user': user_info
    })


# ===================================
# 用户会话管理辅助函数
# ===================================

def get_current_user_info(request):
    """获取当前用户信息"""
    try:
        if request.user.is_authenticated:
            return {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'avatar': '',  # Django User模型没有头像字段
            }
        return None
        
    except Exception as e:
        print(f"[DEBUG] Error getting current user: {str(e)}")
        return None

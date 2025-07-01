"""
认证相关的视图
处理 OAuth 登录、回调、登出等功能
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache

from supabase import create_client, Client
import json
import secrets
import urllib.parse


def google_login(request):
    """
    启动 Google OAuth 登录流程 - 修正版本（使用 Supabase 默认重定向）
    """
    try:
        print(f"[DEBUG] Starting Google OAuth login with Supabase default redirect")
        
        # 不使用自定义 redirect_to，让 Supabase 使用 Dashboard 中配置的 Site URL
        # 这样 OAuth 回调会直接到达首页，我们在首页处理 OAuth 参数
        
        oauth_params = {
            'provider': 'google',
            # 不设置 redirect_to 和 state，避免 bad_oauth_state 错误
        }
        
        # 构建完整的 OAuth URL
        base_oauth_url = f"{settings.SUPABASE_URL}/auth/v1/authorize"
        oauth_url = f"{base_oauth_url}?" + urllib.parse.urlencode(oauth_params)
        
        print(f"[DEBUG] Redirecting to OAuth URL (using Supabase default): {oauth_url}")
        print(f"[DEBUG] OAuth 成功后将重定向到 Supabase Dashboard 中配置的 Site URL")
        
        return redirect(oauth_url)
        
    except Exception as e:
        print(f"[DEBUG] Error in google_login: {str(e)}")
        messages.error(request, f"OAuth login failed: {str(e)}")
        return redirect('matcher:login_page')


def google_callback(request):
    """
    处理 Google OAuth 回调 - 最新最佳实践
    使用最新的 exchange_code_for_session 方法
    """
    try:
        print(f"[DEBUG] === OAuth Callback Debug ===")
        print(f"[DEBUG] Full URL: {request.build_absolute_uri()}")
        print(f"[DEBUG] Method: {request.method}")
        print(f"[DEBUG] GET params: {dict(request.GET)}")
        print(f"[DEBUG] ========================================")
        
        # 1. 获取参数
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        print(f"[DEBUG] Extracted - code: {code[:20] if code else None}...")
        print(f"[DEBUG] Extracted - state: {state}")
        print(f"[DEBUG] Extracted - error: {error}")
        print(f"[DEBUG] Extracted - error_description: {error_description}")
        
        # 2. 错误处理
        if error:
            print(f"[DEBUG] OAuth error: {error} - {error_description}")
            messages.error(request, f"OAuth error: {error_description or error}")
            return redirect('matcher:login_page')
        
        if not code:
            print("[DEBUG] No authorization code received")
            messages.error(request, "Authentication failed: No authorization code received.")
            return redirect('matcher:login_page')
        
        # 3. 验证 state（如果有）
        if state:
            cached_state = cache.get(f"oauth_state_{state}")
            if not cached_state:
                print("[DEBUG] Invalid or expired state parameter")
                messages.error(request, "Authentication failed: Invalid state parameter.")
                return redirect('matcher:login_page')
            cache.delete(f"oauth_state_{state}")
            print("[DEBUG] State parameter validated successfully")
        
        # 4. 使用最新的 exchange_code_for_session 方法
        print(f"[DEBUG] Exchanging code for session: {code[:10]}...")
        
        # 初始化 Supabase 客户端
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # 这是最新的推荐方法 - 只传递授权码
            session_response = supabase.auth.exchange_code_for_session(code)
            
            if session_response and session_response.session:
                user = session_response.user
                session = session_response.session
                
                print(f"[DEBUG] User authenticated successfully: {user.email if user else 'No user'}")
                
                # 5. 存储用户会话信息到 Django session（最佳实践）
                request.session['supabase_access_token'] = session.access_token
                request.session['supabase_refresh_token'] = session.refresh_token
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully")
                
                # 6. 使用 Django 认证系统（可选，如果你需要的话）
                from job_hunting_project.auth_backend import SupabaseUserBackend
                auth_backend = SupabaseUserBackend()
                django_user = auth_backend.authenticate(request=request, supabase_user=user)
                
                if django_user:
                    login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                    print(f"[DEBUG] Django user logged in successfully: {django_user.username}")
                    messages.success(request, "Successfully logged in!")
                else:
                    print("[DEBUG] Failed to create/retrieve Django user")
                    messages.error(request, "Could not complete login. Please try again.")
                    return redirect('matcher:login_page')
                
                print(f"[DEBUG] Redirecting to main page")
                return redirect(reverse('matcher:main_page'))
            else:
                print("[DEBUG] No session returned from code exchange")
                messages.error(request, "Authentication failed: No session returned.")
                return redirect('matcher:login_page')
                
        except Exception as exchange_error:
            print(f"[DEBUG] Error exchanging code for session: {str(exchange_error)}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            messages.error(request, f"Authentication failed: {str(exchange_error)}")
            return redirect('matcher:login_page')
            
    except Exception as e:
        print(f"[DEBUG] Error in google_callback: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        messages.error(request, "An error occurred during authentication.")
        return redirect('matcher:login_page')


def logout_view(request):
    """登出视图"""
    return logout_user(request)


def api_check_auth(request):
    """API：检查认证状态"""
    user = get_current_user_info(request)
    return JsonResponse({
        'authenticated': user is not None,
        'user': user
    })


@csrf_exempt
@require_POST
def process_oauth_tokens(request):
    """
    处理从客户端JavaScript发送的OAuth tokens
    """
    try:
        print(f"[DEBUG] Processing OAuth tokens from client")
        
        # 获取tokens
        access_token = request.POST.get('access_token')
        refresh_token = request.POST.get('refresh_token')
        expires_at = request.POST.get('expires_at')
        provider_token = request.POST.get('provider_token')
        
        print(f"[DEBUG] Received tokens - access_token: {access_token[:20] if access_token else None}...")
        print(f"[DEBUG] Received tokens - refresh_token: {refresh_token[:20] if refresh_token else None}...")
        print(f"[DEBUG] Received tokens - expires_at: {expires_at}")
        
        if not access_token:
            return JsonResponse({'error': 'No access token provided'}, status=400)
        
        # 使用access_token获取用户信息
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # 使用access_token获取用户信息
            user_response = supabase.auth.get_user(access_token)
            
            if user_response and user_response.user:
                user = user_response.user
                
                print(f"[DEBUG] User authenticated via client tokens: {user.email if user else 'No user'}")
                
                # 存储用户会话信息到 Django session
                request.session['supabase_access_token'] = access_token
                request.session['supabase_refresh_token'] = refresh_token or ''
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully via client tokens")
                
                # 使用 Django 认证系统
                from job_hunting_project.auth_backend import SupabaseUserBackend
                auth_backend = SupabaseUserBackend()
                django_user = auth_backend.authenticate(request=request, supabase_user=user)
                
                if django_user:
                    login(request, django_user, backend='job_hunting_project.auth_backend.SupabaseUserBackend')
                    print(f"[DEBUG] Django user logged in successfully via client tokens: {django_user.username}")
                    
                    return JsonResponse({
                        'success': True,
                        'redirect': reverse('matcher:main_page'),
                        'message': 'Successfully logged in!'
                    })
                else:
                    print("[DEBUG] Failed to create/retrieve Django user via client tokens")
                    return JsonResponse({'error': 'Could not complete login'}, status=400)
            else:
                print("[DEBUG] No user returned from token validation via client")
                return JsonResponse({'error': 'Could not validate token'}, status=400)
                
        except Exception as token_error:
            print(f"[DEBUG] Error validating token via client: {str(token_error)}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return JsonResponse({'error': f'Token validation failed: {str(token_error)}'}, status=400)
            
    except Exception as e:
        print(f"[DEBUG] Error in process_oauth_tokens: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# ===================================
# Supabase 用户会话管理辅助函数
# ===================================

def get_current_user_info(request):
    """获取当前用户信息"""
    try:
        access_token = request.session.get('supabase_access_token')
        if not access_token:
            return None
        
        # 从 session 获取用户信息（推荐，更快）
        user_info = {
            'id': request.session.get('user_id'),
            'email': request.session.get('user_email'),
            'name': request.session.get('user_name'),
            'avatar': request.session.get('user_avatar'),
        }
        
        if user_info['id']:
            return user_info
        
        return None
        
    except Exception as e:
        print(f"[DEBUG] Error getting current user: {str(e)}")
        return None


def logout_user(request):
    """登出用户"""
    try:
        # 从 Supabase 登出
        access_token = request.session.get('supabase_access_token')
        if access_token:
            try:
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                supabase.auth.sign_out()
            except Exception as e:
                print(f"[DEBUG] Warning: Error signing out from Supabase: {str(e)}")
        
        # 清除 Django session
        request.session.flush()
        
        return redirect('matcher:login_page')
    except Exception as e:
        print(f"[DEBUG] Error during logout: {str(e)}")
        request.session.flush()
        return redirect('matcher:login_page')

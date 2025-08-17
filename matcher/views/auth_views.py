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
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from matcher.forms import RegisterForm

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
        
        # Don't use custom redirect_to, let Supabase use the Site URL configured in Dashboard
        # This way, OAuth callback will directly reach the homepage, and we handle OAuth parameters there
        
        oauth_params = {
            'provider': 'google',
            # Don't set redirect_to and state to avoid bad_oauth_state error
        }
        
        # Build the complete OAuth URL
        base_oauth_url = f"{settings.SUPABASE_URL}/auth/v1/authorize"
        oauth_url = f"{base_oauth_url}?" + urllib.parse.urlencode(oauth_params)
        
        print(f"[DEBUG] Redirecting to OAuth URL (using Supabase default): {oauth_url}")
        print(f"[DEBUG] After OAuth success, will redirect to the Site URL configured in Supabase Dashboard")
        
        return redirect(oauth_url)
        
    except Exception as e:
        print(f"[DEBUG] Error in google_login: {str(e)}")
        messages.error(request, f"OAuth login failed: {str(e)}")
        return redirect('login')


def google_callback(request):
    """
    Handle Google OAuth callback - latest best practices
    Use the latest exchange_code_for_session method
    """
    try:
        print(f"[DEBUG] === OAuth Callback Debug ===")
        print(f"[DEBUG] Full URL: {request.build_absolute_uri()}")
        print(f"[DEBUG] Method: {request.method}")
        print(f"[DEBUG] GET params: {dict(request.GET)}")
        print(f"[DEBUG] ========================================")
        
        # 1. Get parameters
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        print(f"[DEBUG] Extracted - code: {code[:20] if code else None}...")
        print(f"[DEBUG] Extracted - state: {state}")
        print(f"[DEBUG] Extracted - error: {error}")
        print(f"[DEBUG] Extracted - error_description: {error_description}")
        
        # 2. Error handling
        if error:
            print(f"[DEBUG] OAuth error: {error} - {error_description}")
            messages.error(request, f"OAuth error: {error_description or error}")
            return redirect('login')
        
        if not code:
            print("[DEBUG] No authorization code received")
            messages.error(request, "Authentication failed: No authorization code received.")
            return redirect('login')
        
        # 3. Validate state (if any)
        if state:
            cached_state = cache.get(f"oauth_state_{state}")
            if not cached_state:
                print("[DEBUG] Invalid or expired state parameter")
                messages.error(request, "Authentication failed: Invalid state parameter.")
                return redirect('login')
            cache.delete(f"oauth_state_{state}")
            print("[DEBUG] State parameter validated successfully")
        
        # 4. Use the latest exchange_code_for_session method
        print(f"[DEBUG] Exchanging code for session: {code[:10]}...")
        
        # Initialize Supabase client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # This is the latest recommended method - only pass the authorization code
            session_response = supabase.auth.exchange_code_for_session(code)
            
            if session_response and session_response.session:
                user = session_response.user
                session = session_response.session
                
                print(f"[DEBUG] User authenticated successfully: {user.email if user else 'No user'}")
                
                # 5. Store user session information to Django session (best practice)
                request.session['supabase_access_token'] = session.access_token
                request.session['supabase_refresh_token'] = session.refresh_token
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully")
                
                # 6. Use Django authentication system (optional, if you need it)
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
                    return redirect('login')
                
                print(f"[DEBUG] Redirecting to main page")
                return redirect(reverse('matcher:main_page'))
            else:
                print("[DEBUG] No session returned from code exchange")
                messages.error(request, "Authentication failed: No session returned.")
                return redirect('login')
                
        except Exception as exchange_error:
            print(f"[DEBUG] Error exchanging code for session: {str(exchange_error)}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            messages.error(request, f"Authentication failed: {str(exchange_error)}")
            return redirect('login')
            
    except Exception as e:
        print(f"[DEBUG] Error in google_callback: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        messages.error(request, "An error occurred during authentication.")
        return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = User.objects.create_user(username=username, password=password)
            user.save()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('matcher:main_page')
            else:
                messages.error(request, 'Registration succeeded but login failed.')
                return redirect('login')
        else:
            # Form is invalid, display errors
            return render(request, 'matcher/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'matcher/register.html', {'form': form})


def logout_view(request):
    """Logout view"""
    return logout_user(request)


def api_check_auth(request):
    """API: Check authentication status"""
    user = get_current_user_info(request)
    return JsonResponse({
        'authenticated': user is not None,
        'user': user
    })


@csrf_exempt
@require_POST
def process_oauth_tokens(request):
    """
    Handle OAuth tokens sent from client JavaScript
    """
    try:
        print(f"[DEBUG] Processing OAuth tokens from client")
        
        # Get tokens
        access_token = request.POST.get('access_token')
        refresh_token = request.POST.get('refresh_token')
        expires_at = request.POST.get('expires_at')
        provider_token = request.POST.get('provider_token')
        
        print(f"[DEBUG] Received tokens - access_token: {access_token[:20] if access_token else None}...")
        print(f"[DEBUG] Received tokens - refresh_token: {refresh_token[:20] if refresh_token else None}...")
        print(f"[DEBUG] Received tokens - expires_at: {expires_at}")
        
        if not access_token:
            return JsonResponse({'error': 'No access token provided'}, status=400)
        
        # Use access_token to get user information
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        try:
            # Use access_token to get user information
            user_response = supabase.auth.get_user(access_token)
            
            if user_response and user_response.user:
                user = user_response.user
                
                print(f"[DEBUG] User authenticated via client tokens: {user.email if user else 'No user'}")
                
                # Store user session information to Django session
                request.session['supabase_access_token'] = access_token
                request.session['supabase_refresh_token'] = refresh_token or ''
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_name'] = user.user_metadata.get('full_name', '')
                request.session['user_avatar'] = user.user_metadata.get('picture', '')
                
                print(f"[DEBUG] Session data stored successfully via client tokens")
                
                # Use Django authentication system
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
# Supabase user session management helper functions
# ===================================

def get_current_user_info(request):
    """Get current user information"""
    try:
        access_token = request.session.get('supabase_access_token')
        if not access_token:
            return None
        
        # Get user information from session (recommended, faster)
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
    """Logout user"""
    try:
        # Log out from Supabase
        access_token = request.session.get('supabase_access_token')
        if access_token:
            try:
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                supabase.auth.sign_out()
            except Exception as e:
                print(f"[DEBUG] Warning: Error signing out from Supabase: {str(e)}")
        
        # Clear Django session
        request.session.flush()
        
        return redirect('login')
    except Exception as e:
        print(f"[DEBUG] Error during logout: {str(e)}")
        request.session.flush()
        return redirect('login')

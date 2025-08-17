import os
from django.conf import settings
from django.contrib import auth
from supabase import create_client, Client

class SupabaseAuthMiddleware:
    """
    这个中间件负责处理基于 Supabase JWT 的用户认证。
    它遵循 user_auth.md 中定义的匿名用户 + 可选注册流程。
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.supabase: Client = self._get_supabase_client()

    def _get_supabase_client(self) -> Client:
        """使用 ANON_KEY 初始化 Supabase 客户端。"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY') 
        if not url or not key:
            raise Exception('Supabase URL/KEY (anon) 未配置')
        return create_client(url, key)

    def __call__(self, request):
        # 1. If user is already authenticated, skip
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Even if authenticated, try to attach a Supabase client
            token = request.COOKIES.get('supabase-auth-token')
            if token:
                request.supabase = self._create_authed_client(token)
            else:
                request.supabase = self.supabase # Attach anonymous client
            return self.get_response(request)

        # 2. Try to get token from HttpOnly cookie
        token = request.COOKIES.get('supabase-auth-token')
        user = None
        authed_client = None

        if token:
            try:
                # Validate token and get user
                user_response = self.supabase.auth.get_user(token)
                if user_response and user_response.user:
                    # Use custom backend for authentication
                    user = auth.authenticate(request, supabase_user=user_response.user)
                    authed_client = self._create_authed_client(token)
            except Exception as e:
                # Token invalid or expired, treat as anonymous user
                if settings.DEBUG:
                    print(f"[AuthMiddleware] Token validation failed: {e}")
                token = None # Clear invalid token

        # 3. If no valid token, create anonymous user
        if not user:
            try:
                # Create anonymous user session
                user_response = self.supabase.auth.sign_in_anonymously()
                if user_response and user_response.session and user_response.user:
                    token = user_response.session.access_token
                    user = auth.authenticate(request, supabase_user=user_response.user)
                    authed_client = self._create_authed_client(token)
            except Exception as e:
                # If anonymous user creation fails, cannot continue
                print(f"[AuthMiddleware] Critical: Anonymous user creation failed: {e}")
                # Attach an anonymous client and continue
                request.supabase = self.supabase
                return self.get_response(request)

        # 4. Attach authenticated user and client to request object
        if user:
            request.user = user
        request.supabase = authed_client if authed_client else self.supabase

        response = self.get_response(request)

        # 5. If there is a new token, set it to HttpOnly cookie
        if token:
            response.set_cookie(
                'supabase-auth-token',
                value=token,
                httponly=True,
                samesite='Lax',
                secure=not settings.DEBUG, # Use secure=True in production
                path='/'
            )
            
        return response

    def _create_authed_client(self, token: str) -> Client:
        """Create a Supabase client authenticated with user JWT."""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY') # Still use anon key
        if not url or not key:
            raise Exception('Supabase URL/KEY (anon) not configured')
        
        client = create_client(url, key)
        client.auth.set_session(access_token=token, refresh_token="") # refresh token is optional
        return client

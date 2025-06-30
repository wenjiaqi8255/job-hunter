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
        key = os.environ.get('SUPABASE_KEY') # 使用 anon key
        if not url or not key:
            raise Exception('Supabase URL/KEY (anon) 未配置')
        return create_client(url, key)

    def __call__(self, request):
        # 1. 如果用户已经通过其他方式认证，则直接跳过
        if hasattr(request, 'user') and request.user.is_authenticated:
            # 即使已认证，也尝试附加一个 Supabase 客户端
            token = request.COOKIES.get('supabase-auth-token')
            if token:
                request.supabase = self._create_authed_client(token)
            else:
                request.supabase = self.supabase # 附加匿名客户端
            return self.get_response(request)

        # 2. 尝试从 HttpOnly cookie 中获取 token
        token = request.COOKIES.get('supabase-auth-token')
        user = None
        authed_client = None

        if token:
            try:
                # 验证 token 并获取用户
                user_response = self.supabase.auth.get_user(token)
                if user_response and user_response.user:
                    # 使用自定义后端进行认证
                    user = auth.authenticate(request, supabase_user=user_response.user)
                    authed_client = self._create_authed_client(token)
            except Exception as e:
                # Token 无效或过期，当作匿名用户处理
                if settings.DEBUG:
                    print(f"[AuthMiddleware] Token validation failed: {e}")
                token = None # 清除无效 token

        # 3. 如果没有有效的 token，则创建匿名用户
        if not user:
            try:
                # 创建匿名用户会话
                user_response = self.supabase.auth.sign_in_anonymously()
                if user_response and user_response.session and user_response.user:
                    token = user_response.session.access_token
                    user = auth.authenticate(request, supabase_user=user_response.user)
                    authed_client = self._create_authed_client(token)
            except Exception as e:
                # 如果创建匿名用户失败，则无法继续
                print(f"[AuthMiddleware] Critical: Anonymous user creation failed: {e}")
                # 附加一个匿名客户端并继续
                request.supabase = self.supabase
                return self.get_response(request)

        # 4. 将认证成功的用户和客户端附加到 request 对象
        if user:
            request.user = user
        request.supabase = authed_client if authed_client else self.supabase

        response = self.get_response(request)

        # 5. 如果有新的 token，设置到 HttpOnly cookie 中
        if token:
            response.set_cookie(
                'supabase-auth-token',
                value=token,
                httponly=True,
                samesite='Lax',
                secure=not settings.DEBUG, # 在生产环境中使用 secure=True
                path='/'
            )
            
        return response

    def _create_authed_client(self, token: str) -> Client:
        """创建一个使用用户 JWT 进行认证的 Supabase 客户端。"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY') # 仍然使用 anon key
        if not url or not key:
            raise Exception('Supabase URL/KEY (anon) 未配置')
        
        client = create_client(url, key)
        client.auth.set_session(access_token=token, refresh_token="") # refresh token is optional
        return client

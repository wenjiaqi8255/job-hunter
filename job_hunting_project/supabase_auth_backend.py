import os
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase import create_client

class SupabaseAuthBackend(BaseBackend):
    """
    通过 Supabase JWT 认证用户的 Django 后端。
    此实现遵循官方推荐，直接使用 supabase.auth.get_user() 进行验证。
    """
    def authenticate(self, request, token=None):
        if token is None:
            return None
            
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            # 生产环境中应使用日志记录
            return None
        
        supabase = create_client(supabase_url, supabase_key)
        
        try:
            # 直接使用官方推荐方法，它处理了所有验证逻辑
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                # 使用 Supabase user ID 作为 Django username，确保唯一性
                user, created = User.objects.get_or_create(
                    username=user_response.user.id,
                    defaults={'email': user_response.user.email}
                )
                if created:
                    # 为新创建的用户设置一个不可用的密码
                    user.set_unusable_password()
                    user.save()
                return user
        except Exception as e:
            # 令牌无效、过期或 Supabase 服务不可用
            if settings.DEBUG:
                print(f"Supabase auth failed: {e}")
            return None
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

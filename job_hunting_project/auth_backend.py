
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

class SupabaseUserBackend(BaseBackend):
    """
    这个认证后端与 SupabaseAuthMiddleware 配合使用。
    它不直接验证 token，而是接收来自中间件的 Supabase 用户对象，
    并负责在 Django 的 User 模型中创建或获取对应的用户。
    """
    def authenticate(self, request, supabase_user=None):
        if not supabase_user:
            return None

        try:
            # 使用 Supabase user ID 作为 Django 的 username，确保唯一性
            user, created = User.objects.get_or_create(
                username=supabase_user.id,
                defaults={
                    'email': supabase_user.email if supabase_user.email else '',
                    # 对于匿名用户，email 可能为空
                }
            )

            if created:
                # 为新用户设置一个不可用的密码
                user.set_unusable_password()
                user.save()
            
            return user
        except Exception as e:
            # 记录潜在的数据库错误
            print(f"[SupabaseUserBackend] Error during user get_or_create: {e}")
            return None

    def get_user(self, user_id):
        """
        Django 认证框架要求实现此方法，以便在 session 中检索用户。
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

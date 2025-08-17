
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
            # Use Supabase user ID as Django username, ensuring uniqueness
            user, created = User.objects.get_or_create(
                username=supabase_user.id,
                defaults={
                    'email': supabase_user.email if supabase_user.email else '',
                    # For anonymous users, email may be empty
                }
            )

            if created:
                # Set an unusable password for new users
                user.set_unusable_password()
                user.save()
            
            return user
        except Exception as e:
            # Log potential database errors
            print(f"[SupabaseUserBackend] Error during user get_or_create: {e}")
            return None

    def get_user(self, user_id):
        """
        Django authentication framework requires this method to retrieve users from session.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

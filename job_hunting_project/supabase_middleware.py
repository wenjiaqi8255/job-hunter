from django.contrib import auth

class SupabaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 如果用户已通过其他方式认证（如 Django session），则跳过
        if hasattr(request, 'user') and request.user.is_authenticated:
            return self.get_response(request)
        
        # 从 Authorization header 中提取 Bearer token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # 调用 Django 的认证框架，它会尝试所有已配置的 AUTHENTICATION_BACKENDS
            user = auth.authenticate(request, token=token)
            if user:
                # 将认证成功的用户附加到 request 对象上
                # 这使得 request.user 在后续的视图中可用
                request.user = user
        
        return self.get_response(request)

"""
简单的Supabase客户端认证辅助函数
遵循"简单粗暴，能工作就行"原则
实现方案A+：使用ClientOptions设置正确的Authorization头
"""

from supabase import create_client, Client, ClientOptions
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def create_authed_supabase_client(user_jwt: str) -> Client:
    """
    创建已认证的Supabase客户端
    使用ClientOptions设置正确的Authorization头，实现双Header模式
    
    Args:
        user_jwt: 用户的JWT token
        
    Returns:
        Client: 已认证的Supabase客户端，所有请求都会自动带上正确的Authorization头
    """
    # 创建ClientOptions，设置Authorization头
    client_options = ClientOptions()
    client_options.headers = {"Authorization": f"Bearer {user_jwt}"}
    
    # 创建客户端，supabase-py会智能合并headers：
    # - 保留默认的apikey头
    # - 用我们提供的Authorization头覆盖默认的错误Authorization头
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, options=client_options)
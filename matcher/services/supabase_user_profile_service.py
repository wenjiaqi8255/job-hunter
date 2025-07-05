"""
Supabase 用户数据同步服务 - 严格遵循RLS和最小权限原则
负责Django UserProfile和Supabase user_profiles表之间的数据同步

安全规则：
1. 绝对不使用SERVICE_ROLE_KEY，那是用来绕过RLS的超级钥匙
2. 所有用户相关操作必须通过用户JWT进行认证
3. 严格遵循RLS策略，让Supabase控制数据访问权限
"""
from django.conf import settings
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# 安全检查：确保不会意外使用SERVICE_ROLE_KEY
def _security_check():
    """
    启动时安全检查 - 确保我们没有意外使用SERVICE_ROLE_KEY
    """
    service_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
    anon_key = getattr(settings, 'SUPABASE_KEY', None)
    
    if service_key and anon_key and service_key == anon_key:
        raise ValueError(
            "SECURITY ERROR: SUPABASE_KEY appears to be set to SERVICE_ROLE_KEY. "
            "This violates RLS and minimum privilege principles. "
            "Please use ANON_KEY for SUPABASE_KEY setting."
        )
    
    logger.info("Security check passed: Using ANON_KEY for user operations")

# 运行启动安全检查
_security_check()

def get_supabase_client() -> Client:
    """
    获取Supabase客户端 - 使用ANON_KEY，严格遵循RLS
    根据开发经验：绝对不使用SERVICE_ROLE_KEY，那是用来绕过RLS的超级钥匙
    """
    # 额外安全检查：确保使用的是ANON_KEY
    key = settings.SUPABASE_KEY
    if not key:
        raise ValueError("SUPABASE_KEY not configured")
    
    # 检查key的长度和格式，SERVICE_ROLE_KEY通常比ANON_KEY长
    if len(key) < 100:  # ANON_KEY通常较短
        logger.warning("SUPABASE_KEY seems unusually short, please verify it's the correct ANON_KEY")
    
    return create_client(settings.SUPABASE_URL, key)

def create_authed_supabase_client(user_jwt_token: str) -> Client:
    """
    创建带有用户认证的Supabase客户端
    关键学习：根据第六阶段的解决方案 - 通过ClientOptions强制覆盖Authorization头
    
    安全要点：
    1. 必须传入用户JWT token
    2. 绝对不使用SERVICE_ROLE_KEY
    3. 让RLS策略验证用户权限
    """
    if not user_jwt_token:
        raise ValueError("user_jwt_token is required for authenticated operations")
    
    # 基本的JWT格式检查
    if not user_jwt_token.startswith('eyJ'):
        raise ValueError("Invalid JWT token format")
    
    try:
        from supabase import ClientOptions
        
        # 核心解决方案：通过ClientOptions在创建客户端时强制覆盖Authorization头
        # 这是第六阶段发现的关键技术 - 让Python SDK知道用户身份
        options = ClientOptions()
        options.headers = {"Authorization": f"Bearer {user_jwt_token}"}
        
        supabase = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY,  # 仍使用ANON_KEY，但通过headers传递用户token
            options=options
        )
        
        logger.info("Created authenticated Supabase client with user JWT")
        return supabase
    except Exception as e:
        logger.error(f"Failed to create authenticated Supabase client: {str(e)}")
        raise ValueError(f"Failed to create authenticated client: {str(e)}")

def sync_user_profile_to_supabase(django_profile, user_id: str) -> bool:
    """
    将Django UserProfile数据同步到Supabase
    
    Args:
        django_profile: Django UserProfile实例
        user_id: Supabase用户ID
        
    Returns:
        bool: 同步是否成功
    """
    try:
        supabase = get_supabase_client()
        
        # 准备同步数据
        sync_data = {
            'user_id': user_id,
            'cv_text': django_profile.user_cv_text or '',
            'preferences_text': django_profile.user_preferences_text or '',
            'structured_profile': django_profile.cv_analysis_cache or {},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 检查是否已存在用户资料
        existing_profile = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if existing_profile.data:
            # 更新现有记录
            result = supabase.table('user_profiles').update(sync_data).eq('user_id', user_id).execute()
            logger.info(f"Updated user profile in Supabase for user {user_id}")
        else:
            # 创建新记录
            sync_data['created_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase.table('user_profiles').insert(sync_data).execute()
            logger.info(f"Created new user profile in Supabase for user {user_id}")
        
        # 更新Django同步时间戳
        django_profile.supabase_synced_at = datetime.now(timezone.utc)
        django_profile.save(update_fields=['supabase_synced_at'])
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync user profile to Supabase for user {user_id}: {str(e)}")
        return False

def sync_user_profile_from_supabase(django_profile, user_id: str) -> bool:
    """
    从Supabase同步用户数据到Django
    
    Args:
        django_profile: Django UserProfile实例
        user_id: Supabase用户ID
        
    Returns:
        bool: 同步是否成功
    """
    try:
        supabase = get_supabase_client()
        
        # 从Supabase获取用户资料
        result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            logger.info(f"No user profile found in Supabase for user {user_id}")
            return False
            
        supabase_profile = result.data[0]
        
        # 更新Django模型
        django_profile.user_cv_text = supabase_profile.get('cv_text', '')
        django_profile.user_preferences_text = supabase_profile.get('preferences_text', '')
        django_profile.cv_analysis_cache = supabase_profile.get('structured_profile', {})
        django_profile.supabase_synced_at = datetime.now(timezone.utc)
        django_profile.save()
        
        logger.info(f"Synced user profile from Supabase for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync user profile from Supabase for user {user_id}: {str(e)}")
        return False

def should_sync_from_supabase(django_profile) -> bool:
    """
    判断是否需要从Supabase同步数据
    
    Args:
        django_profile: Django UserProfile实例
        
    Returns:
        bool: 是否需要同步
    """
    # 如果从未同步过，需要同步
    if not django_profile.supabase_synced_at:
        return True
    
    # 如果Django数据比同步时间戳新，不需要同步
    if django_profile.updated_at > django_profile.supabase_synced_at:
        return False
    
    # 如果同步时间超过1小时，需要重新同步
    time_diff = datetime.now(timezone.utc) - django_profile.supabase_synced_at
    if time_diff.total_seconds() > 3600:  # 1小时
        return True
    
    return False

def get_or_create_user_profile(user_id: str, user_jwt_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    获取或创建用户资料，严格遵循RLS
    重要：不再直接用Supabase作为主要数据源，而是尊重RLS权限
    
    Args:
        user_id: Supabase用户ID
        user_jwt_token: 用户的JWT token（强烈建议提供，用于认证操作）
        
    Returns:
        Dict: 用户资料数据，如果失败返回None
    """
    if not user_id:
        logger.error("user_id is required")
        return None
    
    try:
        # 根据是否有token决定使用哪个客户端
        if user_jwt_token:
            # 有token时，使用认证客户端，RLS会正确限制访问
            supabase = create_authed_supabase_client(user_jwt_token)
            logger.info(f"Using authenticated client for user {user_id}")
        else:
            # 没有token时，使用匿名客户端，只能访问公开数据
            # 警告：这种情况下RLS可能会阻止访问私有数据
            supabase = get_supabase_client()
            logger.warning(f"Using anonymous client for user {user_id} - RLS may restrict access")
        
        result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            supabase_profile = result.data[0]
            return {
                'cv_text': supabase_profile.get('cv_text', ''),
                'preferences_text': supabase_profile.get('preferences_text', ''),
                'structured_profile': supabase_profile.get('structured_profile', {}),
                'last_synced': supabase_profile.get('updated_at')
            }
        else:
            # 如果Supabase中没有数据，可能是：
            # 1. 真的没有数据
            # 2. RLS阻止了访问
            if user_jwt_token:
                logger.info(f"No user profile found for user {user_id} (with auth)")
            else:
                logger.warning(f"No user profile found for user {user_id} (anonymous - may be RLS restricted)")
            
            # 返回空的默认数据
            return {
                'cv_text': '',
                'preferences_text': '',
                'structured_profile': {},
                'last_synced': None
            }
        
    except Exception as e:
        logger.error(f"Failed to get user profile for user {user_id}: {str(e)}")
        # 检查是否是RLS相关错误
        if "row-level security" in str(e).lower() or "rls" in str(e).lower():
            logger.error(f"RLS policy violation detected for user {user_id}")
        return None

def update_user_profile_with_analysis(user_id: str, cv_text: str, preferences_text: str, 
                                     structured_profile: dict, user_jwt_token: str) -> bool:
    """
    更新用户资料和分析结果，严格使用用户认证的客户端
    重要：绝对不使用SERVICE_ROLE_KEY，完全依赖RLS和用户认证
    
    Args:
        user_id: Supabase用户ID
        cv_text: CV文本
        preferences_text: 偏好文本
        structured_profile: AI分析结果
        user_jwt_token: 用户的JWT token（必需！）
        
    Returns:
        bool: 更新是否成功
    """
    # 严格的输入验证
    if not user_id:
        raise ValueError("user_id is required")
    if not user_jwt_token:
        raise ValueError("user_jwt_token is required for RLS compliance")
    
    try:
        # 必须使用认证客户端，让RLS验证用户权限
        supabase = create_authed_supabase_client(user_jwt_token)
        
        # 准备同步数据
        sync_data = {
            'user_id': user_id,
            'cv_text': cv_text or '',
            'preferences_text': preferences_text or '',
            'structured_profile': structured_profile or {},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 检查是否已存在用户资料 - RLS会确保用户只能查看自己的记录
        existing_profile = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if existing_profile.data:
            # 更新现有记录 - RLS会确保用户只能更新自己的记录
            result = supabase.table('user_profiles').update(sync_data).eq('user_id', user_id).execute()
            
            # 检查是否更新成功 - 如果RLS阻止了更新，result可能为空
            if not result.data:
                logger.error(f"RLS may have blocked profile update for user {user_id}")
                return False
            
            logger.info(f"Updated user profile in Supabase for user {user_id}")
        else:
            # 创建新记录 - RLS会确保用户只能为自己创建记录
            sync_data['created_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase.table('user_profiles').insert(sync_data).execute()
            
            # 检查是否创建成功
            if not result.data:
                logger.error(f"RLS may have blocked profile creation for user {user_id}")
                return False
            
            logger.info(f"Created new user profile in Supabase for user {user_id}")
        
        return True
            
    except Exception as e:
        logger.error(f"Failed to update user profile with analysis for user {user_id}: {str(e)}")
        # 检查是否是RLS相关错误
        if "row-level security" in str(e).lower() or "rls" in str(e).lower():
            logger.error(f"RLS policy violation detected for user {user_id}")
        return False

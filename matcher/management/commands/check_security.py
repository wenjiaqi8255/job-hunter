"""
安全配置检查工具 - 确保系统配置符合RLS和最小权限原则
"""
from django.conf import settings
from django.core.management.base import BaseCommand
import os
import logging

logger = logging.getLogger(__name__)

class SecurityConfigChecker:
    """
    安全配置检查器 - 基于开发过程中学到的经验
    """
    
    def __init__(self):
        self.warnings = []
        self.errors = []
    
    def check_supabase_keys(self):
        """
        检查Supabase密钥配置 - 确保不会意外使用SERVICE_ROLE_KEY
        """
        anon_key = getattr(settings, 'SUPABASE_KEY', None)
        service_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
        
        if not anon_key:
            self.errors.append("SUPABASE_KEY not configured")
            return
        
        if not service_key:
            self.warnings.append("SUPABASE_SERVICE_ROLE_KEY not configured (this is OK if not needed)")
        
        # 检查是否意外使用了SERVICE_ROLE_KEY
        if service_key and anon_key == service_key:
            self.errors.append(
                "CRITICAL: SUPABASE_KEY is set to SERVICE_ROLE_KEY! "
                "This violates RLS and minimum privilege principles."
            )
        
        # 检查key的格式
        if anon_key and not anon_key.startswith('eyJ'):
            self.warnings.append(
                f"SUPABASE_KEY doesn't look like a typical Supabase key: {anon_key[:20]}..."
            )
        
        if service_key and not service_key.startswith('eyJ'):
            self.warnings.append(
                f"SUPABASE_SERVICE_ROLE_KEY doesn't look like a typical Supabase key: {service_key[:20]}..."
            )
    
    def check_environment_vars(self):
        """
        检查环境变量配置
        """
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Environment variable {var} not set")
    
    def check_debug_settings(self):
        """
        检查调试设置
        """
        if getattr(settings, 'DEBUG', False):
            self.warnings.append("DEBUG is enabled - should be disabled in production")
    
    def check_allowed_hosts(self):
        """
        检查允许的主机设置
        """
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if '*' in allowed_hosts:
            self.warnings.append("ALLOWED_HOSTS contains '*' - should be restricted in production")
    
    def run_all_checks(self):
        """
        运行所有安全检查
        """
        self.check_supabase_keys()
        self.check_environment_vars()
        self.check_debug_settings()
        self.check_allowed_hosts()
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'is_secure': len(self.errors) == 0
        }

def check_security_config():
    """
    检查安全配置的便捷函数
    """
    checker = SecurityConfigChecker()
    result = checker.run_all_checks()
    
    print("\n" + "="*60)
    print("SECURITY CONFIGURATION CHECK")
    print("="*60)
    
    if result['errors']:
        print("\n❌ ERRORS (must fix):")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    if not result['errors'] and not result['warnings']:
        print("\n✅ All security checks passed!")
    
    print("\n" + "="*60)
    print(f"OVERALL STATUS: {'✅ SECURE' if result['is_secure'] else '❌ NEEDS ATTENTION'}")
    print("="*60)
    
    return result

# Django管理命令
class Command(BaseCommand):
    help = 'Check security configuration for RLS and minimum privilege compliance'

    def handle(self, *args, **options):
        result = check_security_config()
        
        if result['errors']:
            self.stdout.write(
                self.style.ERROR(f"Found {len(result['errors'])} security errors")
            )
            return 1
        
        if result['warnings']:
            self.stdout.write(
                self.style.WARNING(f"Found {len(result['warnings'])} security warnings")
            )
        
        self.stdout.write(
            self.style.SUCCESS("Security configuration check completed")
        )
        return 0

if __name__ == '__main__':
    check_security_config()

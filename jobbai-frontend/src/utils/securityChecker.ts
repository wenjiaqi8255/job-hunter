/**
 * 前端安全检查工具 - 确保前端正确处理认证和RLS
 */

interface SecurityCheckResult {
    errors: string[];
    warnings: string[];
    isSecure: boolean;
}

interface ApiSecurityIssue {
    url: string;
    issue: string;
    severity: 'ERROR' | 'WARNING';
}

// 安全配置检查器
class FrontendSecurityChecker {
    private errors: string[] = [];
    private warnings: string[] = [];

    // 检查Supabase配置
    checkSupabaseConfig(): void {
        const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
        const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

        if (!supabaseUrl) {
            this.errors.push('VITE_SUPABASE_URL not configured');
        }

        if (!supabaseKey) {
            this.errors.push('VITE_SUPABASE_ANON_KEY not configured');
        }

        // 检查是否意外使用了SERVICE_ROLE_KEY
        if (supabaseKey && supabaseKey.length > 200) {
            this.warnings.push('Supabase key is unusually long - ensure it\'s not SERVICE_ROLE_KEY');
        }

        // 检查key格式
        if (supabaseKey && !supabaseKey.startsWith('eyJ')) {
            this.warnings.push('Supabase key doesn\'t look like a typical JWT token');
        }
    }

    // 检查API配置
    checkApiConfig(): void {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

        if (!apiBaseUrl) {
            this.errors.push('VITE_API_BASE_URL not configured');
        }

        // 检查是否使用HTTPS（生产环境）
        if (apiBaseUrl && !apiBaseUrl.startsWith('https://') && !apiBaseUrl.startsWith('http://localhost')) {
            this.warnings.push('API base URL should use HTTPS in production');
        }
    }

    // 检查本地存储中的敏感信息
    checkLocalStorage(): void {
        const sensitiveKeys = ['supabase.auth.token', 'access_token', 'refresh_token'];
        
        for (const key of sensitiveKeys) {
            if (localStorage.getItem(key)) {
                this.warnings.push(`Sensitive data found in localStorage: ${key}`);
            }
        }
    }

    // 检查会话存储中的敏感信息
    checkSessionStorage(): void {
        const sensitiveKeys = ['supabase.auth.token', 'access_token', 'refresh_token'];
        
        for (const key of sensitiveKeys) {
            if (sessionStorage.getItem(key)) {
                this.warnings.push(`Sensitive data found in sessionStorage: ${key}`);
            }
        }
    }

    // 检查全局变量泄露
    checkGlobalVariables(): void {
        const dangerousGlobals = ['SUPABASE_SERVICE_ROLE_KEY', 'DATABASE_URL', 'PRIVATE_KEY'];
        
        for (const variable of dangerousGlobals) {
            if ((window as any)[variable]) {
                this.errors.push(`Dangerous global variable exposed: ${variable}`);
            }
        }
    }

    // 运行所有检查
    runAllChecks(): SecurityCheckResult {
        this.checkSupabaseConfig();
        this.checkApiConfig();
        this.checkLocalStorage();
        this.checkSessionStorage();
        this.checkGlobalVariables();

        return {
            errors: this.errors,
            warnings: this.warnings,
            isSecure: this.errors.length === 0
        };
    }

    // 生成报告
    generateReport(): SecurityCheckResult {
        const result = this.runAllChecks();
        
        console.log('\n' + '='.repeat(60));
        console.log('FRONTEND SECURITY CHECK REPORT');
        console.log('='.repeat(60));
        
        if (result.errors.length > 0) {
            console.log('\n❌ ERRORS (must fix):');
            result.errors.forEach((error: string) => {
                console.log(`  - ${error}`);
            });
        }
        
        if (result.warnings.length > 0) {
            console.log('\n⚠️  WARNINGS:');
            result.warnings.forEach((warning: string) => {
                console.log(`  - ${warning}`);
            });
        }
        
        if (result.errors.length === 0 && result.warnings.length === 0) {
            console.log('\n✅ All frontend security checks passed!');
        }
        
        console.log('\n' + '='.repeat(60));
        console.log(`OVERALL STATUS: ${result.isSecure ? '✅ SECURE' : '❌ NEEDS ATTENTION'}`);
        console.log('='.repeat(60));
        
        return result;
    }
}

// API调用拦截器检查
class ApiSecurityChecker {
    private interceptedCalls: ApiSecurityIssue[] = [];

    // 检查API调用是否正确附加了认证头
    checkAuthHeaders(url: string, headers: Record<string, string>): void {
        const isProtectedEndpoint = [
            '/api/user-profile',
            '/api/cv-analysis',
            '/api/match-jobs',
            '/api/protected'
        ].some(endpoint => url.includes(endpoint));

        if (isProtectedEndpoint) {
            const authHeader = headers['Authorization'];
            
            if (!authHeader) {
                this.interceptedCalls.push({
                    url,
                    issue: 'Missing Authorization header',
                    severity: 'ERROR'
                });
            } else if (!authHeader.startsWith('Bearer ')) {
                this.interceptedCalls.push({
                    url,
                    issue: 'Invalid Authorization header format',
                    severity: 'ERROR'
                });
            } else {
                const token = authHeader.split(' ')[1];
                if (!token || token.length < 50) {
                    this.interceptedCalls.push({
                        url,
                        issue: 'Invalid or empty token',
                        severity: 'ERROR'
                    });
                }
            }
        }
    }

    // 生成API安全报告
    generateApiReport(): ApiSecurityIssue[] {
        console.log('\n' + '='.repeat(60));
        console.log('API SECURITY ANALYSIS');
        console.log('='.repeat(60));
        
        if (this.interceptedCalls.length === 0) {
            console.log('\n✅ No API security issues detected in recent calls');
        } else {
            console.log('\n🔍 API Security Issues:');
            this.interceptedCalls.forEach(call => {
                const icon = call.severity === 'ERROR' ? '❌' : '⚠️';
                console.log(`${icon} ${call.url}`);
                console.log(`   Issue: ${call.issue}`);
            });
        }
        
        console.log('='.repeat(60));
        
        return this.interceptedCalls;
    }
}

// 导出工具
export { FrontendSecurityChecker, ApiSecurityChecker };

// 开发环境自动检查
if (import.meta.env.DEV) {
    const checker = new FrontendSecurityChecker();
    
    // 延迟执行，确保应用初始化完成
    setTimeout(() => {
        console.log('Running frontend security checks...');
        checker.generateReport();
    }, 1000);
}

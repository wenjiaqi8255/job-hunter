/**
 * Supabase认证管理模块
 * 统一管理前端认证状态和API调用
 */

// 全局Supabase客户端
let supabaseClient = null;

// 认证状态
let currentUser = null;
let authToken = null;

// 调试模式
const DEBUG_AUTH = true;

// 调试日志函数
function authLog(message) {
    if (DEBUG_AUTH) {
        console.log(`[AUTH] ${message}`);
    }
}

// 初始化Supabase客户端
function initSupabaseAuth() {
    // 这些值将在页面中通过Django模板传递
    const supabaseUrl = window.SUPABASE_URL;
    const supabaseKey = window.SUPABASE_KEY;
    
    if (!supabaseUrl || !supabaseKey) {
        authLog('错误: Supabase配置未找到');
        return false;
    }
    
    try {
        supabaseClient = window.supabase.createClient(supabaseUrl, supabaseKey);
        authLog('Supabase客户端初始化成功');
        return true;
    } catch (error) {
        authLog(`Supabase客户端初始化失败: ${error.message}`);
        return false;
    }
}

// 检查认证状态
async function checkAuthStatus() {
    if (!supabaseClient) {
        authLog('Supabase客户端未初始化');
        return false;
    }
    
    try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        
        if (session) {
            currentUser = session.user;
            authToken = session.access_token;
            authLog(`用户已登录: ${currentUser.email}`);
            updateAuthUI(true);
            return true;
        } else {
            currentUser = null;
            authToken = null;
            authLog('用户未登录');
            updateAuthUI(false);
            return false;
        }
    } catch (error) {
        authLog(`检查认证状态失败: ${error.message}`);
        updateAuthUI(false);
        return false;
    }
}

// 使用Google登录
async function signInWithGoogle() {
    if (!supabaseClient) {
        authLog('Supabase客户端未初始化');
        return false;
    }
    
    try {
        authLog('开始Google登录流程');
        
        const { data, error } = await supabaseClient.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: window.location.origin + window.location.pathname
            }
        });
        
        if (error) {
            authLog(`Google登录错误: ${error.message}`);
            return false;
        } else {
            authLog('Google登录流程已启动');
            return true;
        }
    } catch (error) {
        authLog(`Google登录异常: ${error.message}`);
        return false;
    }
}

// 登出
async function signOut() {
    if (!supabaseClient) {
        authLog('Supabase客户端未初始化');
        return false;
    }
    
    try {
        authLog('开始登出流程');
        
        const { error } = await supabaseClient.auth.signOut();
        
        if (error) {
            authLog(`登出错误: ${error.message}`);
            return false;
        } else {
            currentUser = null;
            authToken = null;
            authLog('登出成功');
            updateAuthUI(false);
            return true;
        }
    } catch (error) {
        authLog(`登出异常: ${error.message}`);
        return false;
    }
}

// 更新认证UI
function updateAuthUI(isAuthenticated) {
    authLog(`更新UI状态: 已认证=${isAuthenticated}`);
    
    // 更新导航栏
    const navLogin = document.getElementById('nav-login');
    const navMyApplications = document.getElementById('nav-my-applications');
    const navProfile = document.getElementById('nav-profile');
    const navLogout = document.getElementById('nav-logout');
    
    if (isAuthenticated) {
        // 显示已认证用户的导航项
        if (navLogin) {
            navLogin.style.display = 'none';
            authLog('隐藏登录按钮');
        }
        if (navMyApplications) {
            navMyApplications.style.display = 'block';
            authLog('显示我的申请');
        }
        if (navProfile) {
            navProfile.style.display = 'block';
            authLog('显示个人资料');
        }
        if (navLogout) {
            navLogout.style.display = 'block';
            authLog('显示登出按钮');
        }
    } else {
        // 显示未认证用户的导航项
        if (navLogin) {
            navLogin.style.display = 'block';
            authLog('显示登录按钮');
        }
        if (navMyApplications) {
            navMyApplications.style.display = 'none';
            authLog('隐藏我的申请');
        }
        if (navProfile) {
            navProfile.style.display = 'none';
            authLog('隐藏个人资料');
        }
        if (navLogout) {
            navLogout.style.display = 'none';
            authLog('隐藏登出按钮');
        }
    }
}

// 为所有API请求添加认证头
function addAuthHeaders(headers = {}) {
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
        authLog('添加认证头到请求');
    } else {
        authLog('没有认证token，跳过添加认证头');
    }
    return headers;
}

// 保存原始fetch函数的引用
let originalFetch = null;

// 增强的fetch函数，自动添加认证头
async function authFetch(url, options = {}) {
    const headers = addAuthHeaders(options.headers || {});
    
    // 添加CSRF token
    if (!headers['X-CSRFToken']) {
        headers['X-CSRFToken'] = getCookie('csrftoken');
    }
    
    const enhancedOptions = {
        ...options,
        headers: headers
    };
    
    try {
        // 使用原始fetch避免递归
        if (!originalFetch) {
            throw new Error('Original fetch not available');
        }
        const response = await originalFetch.call(window, url, enhancedOptions);
        
        // 如果返回401，可能需要重新登录
        if (response.status === 401) {
            authLog('API返回401，可能需要重新登录');
            // 更新UI状态为未登录
            updateAuthUI(false);
            // 可以选择自动重新登录或显示登录提示
            showLoginPrompt();
        }
        
        return response;
    } catch (error) {
        authLog(`API请求失败: ${error.message}`);
        throw error;
    }
}

// 显示登录提示
function showLoginPrompt() {
    // 可以显示一个提示框或重定向到登录
    console.log('需要重新登录');
    // 这里可以添加更友好的提示
}

// 拦截所有fetch请求，自动添加认证头
function interceptFetch() {
    // 如果已经拦截过，就不要重复拦截
    if (window.fetch !== originalFetch) {
        authLog('Fetch已经被拦截，跳过重复拦截');
        return;
    }
    
    window.fetch = async function(url, options = {}) {
        // 如果URL是相对路径或同域，自动添加认证头
        if (typeof url === 'string' && (url.startsWith('/') || url.startsWith(window.location.origin))) {
            authLog(`拦截API请求: ${url}`);
            
            // 直接在这里添加认证头，避免调用authFetch造成递归
            const headers = addAuthHeaders(options.headers || {});
            
            // 添加CSRF token
            if (!headers['X-CSRFToken']) {
                headers['X-CSRFToken'] = getCookie('csrftoken');
            }
            
            const enhancedOptions = {
                ...options,
                headers: headers
            };
            
            try {
                const response = await originalFetch.call(this, url, enhancedOptions);
                
                // 如果返回401，可能需要重新登录
                if (response.status === 401) {
                    authLog('API返回401，可能需要重新登录');
                    // 更新UI状态为未登录
                    updateAuthUI(false);
                    // 可以选择自动重新登录或显示登录提示
                    showLoginPrompt();
                }
                
                return response;
            } catch (error) {
                authLog(`API请求失败: ${error.message}`);
                throw error;
            }
        }
        
        // 对于外部API，使用原始fetch
        return originalFetch.call(this, url, options);
    };
}

// 拦截jQuery Ajax请求
function interceptJQuery() {
    if (window.jQuery) {
        const originalAjax = window.jQuery.ajax;
        
        window.jQuery.ajax = function(options) {
            // 自动添加认证头
            if (!options.headers) {
                options.headers = {};
            }
            
            options.headers = addAuthHeaders(options.headers);
            
            // 添加CSRF token
            if (!options.headers['X-CSRFToken']) {
                options.headers['X-CSRFToken'] = getCookie('csrftoken');
            }
            
            authLog(`拦截jQuery Ajax请求: ${options.url}`);
            
            return originalAjax.call(this, options);
        };
    }
}

// 获取CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    authLog('开始初始化认证模块');
    
    // 在任何拦截发生之前，先保存原始fetch
    originalFetch = window.fetch;
    
    if (initSupabaseAuth()) {
        authLog('Supabase客户端初始化成功，开始检查认证状态');
        
        // 检查认证状态
        checkAuthStatus().then(isAuthenticated => {
            authLog(`初始认证状态检查完成: ${isAuthenticated}`);
        }).catch(error => {
            authLog(`初始认证状态检查失败: ${error.message}`);
        });
        
        // 拦截所有API请求
        interceptFetch();
        interceptJQuery();
        
        // 监听认证状态变化
        supabaseClient.auth.onAuthStateChange((event, session) => {
            authLog(`认证状态变化事件: ${event}`);
            
            if (event === 'SIGNED_IN' && session) {
                currentUser = session.user;
                authToken = session.access_token;
                authLog(`用户登录成功: ${currentUser.email}`);
                updateAuthUI(true);
                
                // 如果当前在登录页面，跳转到首页
                if (window.location.pathname.includes('/login/')) {
                    window.location.href = '/';
                }
            } else if (event === 'SIGNED_OUT') {
                currentUser = null;
                authToken = null;
                authLog('用户已登出');
                updateAuthUI(false);
            }
        });
    } else {
        authLog('Supabase客户端初始化失败，设置UI为未认证状态');
        updateAuthUI(false);
    }
});

// 导出全局函数
window.authManager = {
    signInWithGoogle,
    signOut,
    checkAuthStatus,
    getCurrentUser: () => currentUser,
    getAuthToken: () => authToken,
    authFetch,
    interceptFetch,
    interceptJQuery,
    // 新增的API调用函数
    getUserStatus,
    saveJob,
    getSavedJobs,
    loadUserData
};

// API调用函数 - 简单粗暴的实现

// 获取用户状态
async function getUserStatus() {
    try {
        const response = await authFetch('/api/user-status/');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                authLog('用户状态获取成功');
                return data.user;
            }
        }
        authLog('用户状态获取失败');
        return null;
    } catch (error) {
        authLog(`获取用户状态异常: ${error.message}`);
        return null;
    }
}

// 保存工作
async function saveJob(jobId, status = 'viewed', notes = '') {
    try {
        const response = await authFetch('/api/jobs/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_id: jobId,
                status: status,
                notes: notes
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                authLog(`工作保存成功: ${jobId} - ${status}`);
                return true;
            }
        }
        authLog(`工作保存失败: ${jobId}`);
        return false;
    } catch (error) {
        authLog(`保存工作异常: ${error.message}`);
        return false;
    }
}

// 获取保存的工作列表
async function getSavedJobs() {
    try {
        const response = await authFetch('/api/jobs/saved/');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                authLog(`获取保存的工作成功: ${data.count}个`);
                return data.jobs;
            }
        }
        authLog('获取保存的工作失败');
        return [];
    } catch (error) {
        authLog(`获取保存的工作异常: ${error.message}`);
        return [];
    }
}

// 加载用户数据到页面
async function loadUserData() {
    authLog('开始加载用户数据');
    
    if (!currentUser || !authToken) {
        authLog('用户未认证，跳过加载用户数据');
        return;
    }
    
    try {
        // 获取用户状态
        const userStatus = await getUserStatus();
        if (userStatus) {
            authLog('用户状态加载成功');
            // 更新页面上的用户信息显示
            updateUserInfoDisplay(userStatus);
        }
        
        // 如果在相关页面，加载特定数据
        if (window.location.pathname.includes('/my-applications/')) {
            await loadSavedJobsData();
        }
        
    } catch (error) {
        authLog(`加载用户数据失败: ${error.message}`);
    }
}

// 更新用户信息显示
function updateUserInfoDisplay(userStatus) {
    // 简单的用户信息显示更新
    const userEmailElements = document.querySelectorAll('[data-user-email]');
    userEmailElements.forEach(el => {
        el.textContent = userStatus.email || '';
    });
    
    const userNameElements = document.querySelectorAll('[data-user-name]');
    userNameElements.forEach(el => {
        el.textContent = userStatus.full_name || userStatus.email || '';
    });
}

// 加载保存的工作数据
async function loadSavedJobsData() {
    authLog('开始加载保存的工作数据');
    
    const savedJobs = await getSavedJobs();
    
    // 找到显示保存工作的容器
    const container = document.querySelector('[data-saved-jobs-container]');
    if (container && savedJobs.length > 0) {
        // 简单的工作列表显示
        let html = '<div class="saved-jobs-list">';
        savedJobs.forEach(job => {
            html += `
                <div class="saved-job-item">
                    <h4>${job.job_title}</h4>
                    <p><strong>Company:</strong> ${job.company_name}</p>
                    <p><strong>Status:</strong> ${job.status}</p>
                    <p><strong>Location:</strong> ${job.location || 'Not specified'}</p>
                    ${job.notes ? `<p><strong>Notes:</strong> ${job.notes}</p>` : ''}
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    }
}

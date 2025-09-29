// useSidebar.ts - 侧边栏状态管理Hook
import { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from './useToast';
import { AuthContext } from '../contexts/AuthContext';
import { useApi } from './useApi';
import type { SidebarState, SidebarActions, User, SessionHistory, LanguageOption } from '../types/sidebar';

const STORAGE_KEY = 'sidebarCollapsed';

export const useSidebar = (): SidebarState & SidebarActions => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showSuccess, showError } = useToast();
  const { logout: authLogout } = useApi();
  const { token, user } = useContext(AuthContext);

  // 状态管理
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === 'true';
  });

  const [activeNav, setActiveNav] = useState(() => {
    const path = location.pathname;
    if (path.includes('/applications')) return 'my_applications';
    if (path.includes('/profile')) return 'profile';
    if (path.includes('/matches') || path.includes('/jobs')) return 'matches';
    return 'matches';
  });

  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [sessionHistory, setSessionHistory] = useState<SessionHistory[]>([]);
  const [languages, setLanguages] = useState<LanguageOption[]>([
    { code: 'en', name: 'English', is_selected: true },
    { code: 'zh', name: '中文', is_selected: false },
  ]);

  // 从URL参数中获取session_id
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session_id');
    if (sessionId) {
      setCurrentSessionId(sessionId);
    }
  }, [location.search]);

  // 监听路由变化更新activeNav
  useEffect(() => {
    const path = location.pathname;
    if (path.includes('/applications')) {
      setActiveNav('my_applications');
    } else if (path.includes('/profile')) {
      setActiveNav('profile');
    } else if (path.includes('/matches') || path.includes('/jobs')) {
      setActiveNav('matches');
    }
  }, [location.pathname]);

  // 侧边栏折叠/展开
  const toggleSidebar = useCallback(() => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem(STORAGE_KEY, String(newState));
  }, [isCollapsed]);

  // 设置当前会话
  const setCurrentSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
    // 更新会话历史中的当前状态
    setSessionHistory(prev =>
      prev.map(session => ({
        ...session,
        is_current: session.id.toString() === sessionId
      }))
    );
  }, []);

  // 添加会话到历史记录（从匹配结果中提取）
  const addSessionToHistory = useCallback((sessionData: any) => {
    const sessionHistoryItem: SessionHistory = {
      id: sessionData.id,
      matched_at: sessionData.matched_at || new Date().toISOString(),
      user_preferences_text: sessionData.user_preferences_text || sessionData.preferences_text || 'New Session',
      is_current: true,
      // 简化显示，只保留必要信息
      job_count: sessionData.matches?.length || 0,
    };

    setSessionHistory(prev => {
      // 移除重复的会话，添加新的会话到顶部
      const filtered = prev.filter(session => session.id !== sessionData.id);
      return [sessionHistoryItem, ...filtered].slice(0, 10); // 最多保留10个历史记录
    });

    setCurrentSessionId(sessionData.id.toString());
  }, []);

  // 语言切换
  const changeLanguage = useCallback(async (languageCode: string) => {
    try {
      const response = await fetch('/api/v1/language/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
        },
        body: JSON.stringify({ language: languageCode }),
      });

      if (response.ok) {
        // 更新本地状态
        setLanguages(prev =>
          prev.map(lang => ({
            ...lang,
            is_selected: lang.code === languageCode
          }))
        );

        // 页面刷新以应用新语言
        window.location.reload();
        showSuccess('Language changed successfully');
      } else {
        showError('Failed to change language');
      }
    } catch (error) {
      console.error('Error changing language:', error);
      showError('Error changing language');
    }
  }, [showSuccess, showError]);

  // 用户登出
  const logout = useCallback(async () => {
    try {
      await authLogout();
      showSuccess('Logged out successfully');
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      showError('Logout failed');
    }
  }, [authLogout, showSuccess, showError, navigate]);

  // 初始化时从localStorage加载会话历史
  useEffect(() => {
    const savedHistory = localStorage.getItem('sessionHistory');
    if (savedHistory) {
      try {
        setSessionHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Error parsing session history from localStorage:', error);
        setSessionHistory([]);
      }
    }
  }, []);

  // 当会话历史变化时保存到localStorage
  useEffect(() => {
    if (sessionHistory.length > 0) {
      localStorage.setItem('sessionHistory', JSON.stringify(sessionHistory));
    }
  }, [sessionHistory]);

  return {
    // State
    isCollapsed,
    activeNav,
    currentSessionId,
    user,
    sessionHistory,
    languages,

    // Actions
    toggleSidebar,
    setActiveNav,
    setCurrentSession,
    changeLanguage,
    addSessionToHistory,
    logout,
  };
};
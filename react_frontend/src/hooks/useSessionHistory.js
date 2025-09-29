// useSessionHistory.js
// 管理用户匹配会话历史的自定义Hook
import { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';

// TypeScript类型定义
export const useSessionHistory = (options = {}) => {
  const { token, user } = useContext(AuthContext) || {};
  const {
    initialPage = 1,
    limit = 10,
    autoFetch = true
  } = options;

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: initialPage,
    limit,
    total: 0,
    has_next: false,
    has_prev: false
  });

  // 获取会话历史
  const fetchSessions = async (page = initialPage) => {
    if (!token || !user?.id) {
      setError('用户未登录');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await DefaultService.getUserMatchSessionsApiV1MatchingSessionsGet(
        user.id,
        (page - 1) * limit,
        limit
      );

      setSessions(response.sessions || []);
      setPagination(prev => ({
        ...prev,
        page,
        total: response.total || 0,
        has_next: response.has_next || false,
        has_prev: page > 1
      }));
    } catch (err) {
      console.error('获取会话历史失败:', err);
      setError('获取匹配历史失败');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  // 刷新当前页面数据
  const refresh = () => {
    fetchSessions(pagination.page);
  };

  // 跳转到指定页面
  const goToPage = (page) => {
    if (page >= 1 && page <= Math.ceil(pagination.total / pagination.limit)) {
      fetchSessions(page);
    }
  };

  // 下一页
  const nextPage = () => {
    if (pagination.has_next) {
      goToPage(pagination.page + 1);
    }
  };

  // 上一页
  const prevPage = () => {
    if (pagination.has_prev) {
      goToPage(pagination.page - 1);
    }
  };

  // 自动获取数据
  useEffect(() => {
    if (autoFetch && token && user?.id) {
      fetchSessions();
    }
  }, [token, user?.id, autoFetch]);

  return {
    // 数据
    sessions,
    loading,
    error,
    pagination,

    // 操作
    fetchSessions,
    refresh,
    goToPage,
    nextPage,
    prevPage,

    // 计算属性
    isEmpty: sessions.length === 0 && !loading,
    totalPages: Math.ceil(pagination.total / pagination.limit),
    currentPage: pagination.page
  };
};
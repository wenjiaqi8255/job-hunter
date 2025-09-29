// useApi.ts - API调用Hook
// 遵循SOLID原则：单一职责、依赖倒置
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useToast } from './useToast';
import httpClient from '../services/httpClient';
import { CONFIG } from '../config';

export const useApi = () => {
  const { user, logout } = useContext(AuthContext);
  const { showError } = useToast();

  // 通用的API请求函数
  const apiRequest = async (endpoint: string, options = {}) => {
    try {
      const response = await httpClient.request({
        url: endpoint,
        ...options,
      });
      return response;
    } catch (error) {
      // 处理特定错误
      if (error.code === 'UNAUTHORIZED') {
        // Token过期，自动登出
        logout();
        showError(CONFIG.ERROR.UNAUTHORIZED);
      } else {
        showError(error.message || CONFIG.ERROR.UNKNOWN);
      }
      throw error;
    }
  };

  // 启动新的匹配会话
  const startNewMatch = async () => {
    return apiRequest('/matching/start/', {
      method: 'POST',
    });
  };

  // 更新工作申请状态
  const updateJobApplicationStatus = async (jobId: string, status: string) => {
    return apiRequest(`/applications/jobs/${jobId}/status/`, {
      method: 'POST',
      data: { status },
    });
  };

  // 切换语言
  const changeLanguage = async (languageCode: string) => {
    return apiRequest('/language/', {
      method: 'POST',
      data: { language: languageCode },
    });
  };

  return {
    user,
    logout,
    startNewMatch,
    updateJobApplicationStatus,
    changeLanguage,
    apiRequest,
  };
};
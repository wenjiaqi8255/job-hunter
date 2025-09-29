// useApi.ts - API调用Hook
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useToast } from './useToast';
import axios from 'axios';

const API_BASE_URL = '/api/v1';

export const useApi = () => {
  const { token, user, logout } = useContext(AuthContext);
  const { showError } = useToast();

  // 通用的API请求函数
  const apiRequest = async (endpoint: string, options = {}) => {
    const config = {
      headers: {},
      ...options
    };

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await axios(`${API_BASE_URL}${endpoint}`, config);
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        // Token过期，自动登出
        logout();
        showError('Session expired. Please login again.');
      } else {
        showError(error.response?.data?.message || 'API request failed');
      }
      throw error;
    }
  };

  // 启动新的匹配会话
  const startNewMatch = async () => {
    return apiRequest('/matching/start/', {
      method: 'POST'
    });
  };

  // 更新工作申请状态
  const updateJobApplicationStatus = async (jobId: string, status: string) => {
    return apiRequest(`/applications/jobs/${jobId}/status/`, {
      method: 'POST',
      data: { status }
    });
  };

  
  // 切换语言
  const changeLanguage = async (languageCode: string) => {
    return apiRequest('/language/', {
      method: 'POST',
      data: { language: languageCode }
    });
  };

  return {
    user,
    token,
    logout,
    startNewMatch,
    updateJobApplicationStatus,
    changeLanguage,
    apiRequest
  };
};
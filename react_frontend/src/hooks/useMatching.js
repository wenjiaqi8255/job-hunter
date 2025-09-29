import { useState, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { MatchingService } from '../services/api_gen/services/MatchingService';

/**
 * 工作匹配核心逻辑Hook
 * 对应Django的start_new_match_session视图
 *
 * 功能：
 * 1. 防抖处理（30秒内不允许重复请求）
 * 2. AI工作匹配
 * 3. 匹配会话管理
 * 4. 错误处理和加载状态
 */
export const useMatching = () => {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();

  const [isMatching, setIsMatching] = useState(false);
  const [error, setError] = useState(null);
  const [matchSessionId, setMatchSessionId] = useState(null);
  const [debounceKey, setDebounceKey] = useState(null);

  /**
   * 开始新的匹配会话
   * 对应Django的start_new_match_session视图
   */
  const startMatching = useCallback(async () => {
    if (!user || !token) {
      setError('请先登录');
      return;
    }

    // 防抖检查 - 30秒内不允许重复请求
    const now = Date.now();
    if (debounceKey && now - debounceKey < 30000) {
      setError('匹配请求正在进行中，请稍后再试');
      return;
    }

    if (!user || !user.id) {
      setError('用户信息不完整，请重新登录');
      return;
    }

    setIsMatching(true);
    setError(null);
    setDebounceKey(now);

    try {
      console.log('DEBUG: Starting new match session...');

      // 调用FastAPI的匹配端点
      const matchSessionData = {
        user_id: user.id,
        skills_text: '', // 将从用户profile获取
        user_preferences_text: '', // 将从用户profile获取
      };

      // 创建匹配会话
      const response = await MatchingService.createMatchSessionApiV1MatchingSessionsPost(
        matchSessionData
      );

      console.log('DEBUG: Match session created:', response);

      setMatchSessionId(response.id);

      // 导航到匹配结果页面
      navigate(`/?session_id=${response.id}`);

    } catch (err) {
      console.error('Matching failed:', err);
      setError(err.response?.data?.detail || '匹配失败，请重试');
      setDebounceKey(null); // 重置防抖，允许重试
    } finally {
      setIsMatching(false);
    }
  }, [user, token, navigate, debounceKey]);

  /**
   * 检查匹配状态
   * 对应Django的_match_session_status检查
   */
  const checkMatchStatus = useCallback(async (sessionId) => {
    if (!sessionId || !token) return null;

    try {
      const response = await MatchingService.getMatchSessionDetailApiV1MatchingSessionsSessionIdGet(
        sessionId
      );
      return response;
    } catch (err) {
      console.error('Failed to check match status:', err);
      return null;
    }
  }, [token]);

  /**
   * 重置匹配状态
   */
  const resetMatching = useCallback(() => {
    setIsMatching(false);
    setError(null);
    setMatchSessionId(null);
    setDebounceKey(null);
  }, []);

  return {
    isMatching,
    error,
    matchSessionId,
    startMatching,
    checkMatchStatus,
    resetMatching,
  };
};
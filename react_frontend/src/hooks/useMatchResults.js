import { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { MatchingService } from '../services/api_gen/services/MatchingService';
import { ApplicationsService } from '../services/api_gen/services/ApplicationsService';

/**
 * 匹配结果数据管理Hook
 * 对应Django的_handle_session_view_get和_process_matched_jobs_for_session
 *
 * 功能：
 * 1. 根据session_id获取匹配结果
 * 2. 处理匹配数据（分数、原因、提示、洞察）
 * 3. 支持保存状态管理
 * 4. 错误处理和加载状态
 */
export const useMatchResults = () => {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const [matchResults, setMatchResults] = useState([]);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 获取匹配结果
   * 对应Django的_process_matched_jobs_for_session
   */
  const fetchMatchResults = useCallback(async (sessionIdToFetch) => {
    if (!sessionIdToFetch || !token || !user) {
      setError('缺少必要参数');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('DEBUG: Fetching match results for session:', sessionIdToFetch);

      // 获取匹配会话信息和匹配结果
      const sessionResponse = await MatchingService.getMatchSessionDetailApiV1MatchingSessionsSessionIdGet(
        sessionIdToFetch,
        user?.id
      );

      console.log('DEBUG: Session response:', sessionResponse);

      setSessionInfo(sessionResponse.session);

      // 从响应中提取匹配结果
      const resultsResponse = sessionResponse.matched_jobs || [];

      console.log('DEBUG: Match results:', resultsResponse);

      // 处理匹配结果，添加保存状态
      const processedResults = await Promise.all(
        resultsResponse.map(async (result) => {
          // 如果API没有返回saved_status，则查询数据库
          let savedStatus = result.saved_status;
          if (!savedStatus) {
            try {
              const savedJobResponse = await ApplicationsService.getSavedJobApiV1ApplicationsJobsJobIdSavedGet(
                result.job_object.id
              );
              savedStatus = savedJobResponse?.status || 'not_applied';
            } catch (err) {
              // 如果没有保存记录，状态为null
              savedStatus = null;
            }
          }

          return {
            ...result,
            job_listing: result.job_object, // 标准化字段名
            saved_status: savedStatus,
            // 确保解析后的数据存在
            parsed_insights: result.parsed_insights_list || [],
            parsed_tips: result.parsed_tips_list || (result.tips ? result.tips.split('\n').filter(tip => tip.trim()) : []),
            parsed_anomalies: result.job_anomalies || [],
          };
        })
      );

      setMatchResults(processedResults);

    } catch (err) {
      console.error('Failed to fetch match results:', err);
      setError(err.response?.data?.detail || '获取匹配结果失败');

      // 如果会话不存在，导航回首页
      if (err.response?.status === 404) {
        navigate('/');
      }
    } finally {
      setLoading(false);
    }
  }, [token, user, navigate]);

  /**
   * 当sessionId变化时自动获取匹配结果
   */
  useEffect(() => {
    if (sessionId) {
      fetchMatchResults(sessionId);
    }
  }, [sessionId, fetchMatchResults]);

  /**
   * 保存/取消保存工作
   * 对应Django的SavedJob创建/更新逻辑
   */
  const toggleSaveJob = useCallback(async (jobId, currentStatus) => {
    if (!token || !user) {
      setError('请先登录');
      return;
    }

    try {
      const newStatus = currentStatus === 'saved' ? 'not_applied' : 'saved';

      if (currentStatus) {
        // 更新现有记录
        await ApplicationsService.updateSavedJobApiV1ApplicationsJobsJobIdSavedPut(
          jobId,
          { status: newStatus }
        );
      } else {
        // 创建新记录
        await ApplicationsService.createSavedJobApiV1ApplicationsJobsJobIdSavedPost(
          jobId,
          { status: newStatus }
        );
      }

      // 更新本地状态
      setMatchResults(prevResults =>
        prevResults.map(result =>
          result.job_listing.id === jobId || result.job_object?.id === jobId
            ? { ...result, saved_status: newStatus }
            : result
        )
      );

    } catch (err) {
      console.error('Failed to toggle save job:', err);
      setError(err.response?.data?.detail || '操作失败');
    }
  }, [token, user]);

  /**
   * 刷新匹配结果
   */
  const refetch = useCallback(() => {
    if (sessionId) {
      fetchMatchResults(sessionId);
    }
  }, [sessionId, fetchMatchResults]);

  return {
    matchResults,
    sessionInfo,
    loading,
    error,
    sessionId,
    toggleSaveJob,
    refetch,
  };
};
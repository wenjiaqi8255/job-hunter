// useApplications.js
// 管理用户申请状态的自定义Hook，对应Django的application_views.py
import { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';

export const useApplications = (options = {}) => {
  const { token, user } = useContext(AuthContext) || {};
  const {
    statusFilter = null,
    autoFetch = true
  } = options;

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusCounts, setStatusCounts] = useState({});

  // Django SavedJob.STATUS_CHOICES
  const statusChoices = [
    { value: 'not_applied', label: '未申请' },
    { value: 'applied', label: '已申请' },
    { value: 'interviewing', label: '面试中' },
    { value: 'offered', label: '已录用' },
    { value: 'rejected', label: '已拒绝' }
  ];

  // 获取申请列表
  const fetchApplications = async () => {
    if (!token || !user?.id) {
      setError('用户未登录');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 获取保存的工作列表
      const savedJobs = await DefaultService.getUserSavedJobsApiV1SavedJobsGet(user?.id);

      // 根据状态过滤
      const filteredJobs = statusFilter
        ? savedJobs.filter(job => job.status === statusFilter)
        : savedJobs;

      setApplications(filteredJobs);

      // 计算状态统计
      const counts = {};
      statusChoices.forEach(choice => {
        counts[choice.value] = savedJobs.filter(job => job.status === choice.value).length;
      });
      setStatusCounts(counts);
    } catch (err) {
      console.error('获取申请列表失败:', err);
      setError('获取申请列表失败');
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  // 更新申请状态
  const updateApplicationStatus = async (jobId, newStatus) => {
    if (!token || !user?.id) {
      throw new Error('用户未登录');
    }

    try {
      await DefaultService.updateJobApplicationStatusApiV1ApplicationsJobIdStatusPost(
        jobId,
        { status: newStatus }
      );

      // 更新本地状态
      setApplications(prev =>
        prev.map(app =>
          app.job_listing?.id === jobId
            ? { ...app, status: newStatus }
            : app
        )
      );

      // 更新统计
      setStatusCounts(prev => ({
        ...prev,
        [newStatus]: (prev[newStatus] || 0) + 1
      }));

      return true;
    } catch (err) {
      console.error('更新申请状态失败:', err);
      throw err;
    }
  };

  // 生成求职信
  const generateCoverLetter = async (jobId) => {
    if (!token || !user?.id) {
      throw new Error('用户未登录');
    }

    try {
      const response = await DefaultService.generateCoverLetterApiV1ApplicationsJobIdCoverLetterPost(jobId);
      return response;
    } catch (err) {
      console.error('生成求职信失败:', err);
      throw err;
    }
  };

  // 生成定制简历
  const generateCustomResume = async (jobId) => {
    if (!token || !user?.id) {
      throw new Error('用户未登录');
    }

    try {
      const response = await DefaultService.generateCustomResumeApiV1ApplicationsJobIdResumePost(jobId);
      return response;
    } catch (err) {
      console.error('生成定制简历失败:', err);
      throw err;
    }
  };

  // 自动获取数据
  useEffect(() => {
    if (autoFetch && token && user?.id) {
      fetchApplications();
    }
  }, [token, user?.id, statusFilter, autoFetch]);

  return {
    // 数据
    applications,
    loading,
    error,
    statusCounts,
    statusChoices,
    currentFilter: statusFilter,

    // 操作
    fetchApplications,
    updateApplicationStatus,
    generateCoverLetter,
    generateCustomResume,

    // 计算属性
    isEmpty: applications.length === 0 && !loading
  };
};
import { useState, useCallback, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { ApplicationsService } from '../services/api_gen/services/ApplicationsService';

/**
 * 申请状态管理Hook
 * 对应Django的update_job_application_status视图和SavedJob模型
 *
 * 功能：
 * 1. 申请状态管理（not_applied, viewed, applied, interviewing, offered, rejected）
 * 2. 申请历史查询
 * 3. 状态统计
 * 4. 批量操作支持
 */
export const useApplicationStatus = () => {
  const { user, token } = useContext(AuthContext);

  const [applications, setApplications] = useState([]);
  const [statusCounts, setStatusCounts] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 申请状态选项，对应Django的SavedJob.STATUS_CHOICES
  const STATUS_CHOICES = [
    { value: 'not_applied', label: '未申请', color: 'gray' },
    { value: 'viewed', label: '已查看', color: 'blue' },
    { value: 'applied', label: '已申请', color: 'yellow' },
    { value: 'interviewing', label: '面试中', color: 'purple' },
    { value: 'offered', label: '已录用', color: 'green' },
    { value: 'rejected', label: '已拒绝', color: 'red' },
  ];

  /**
   * 获取申请列表
   * 对应Django的my_applications_page
   */
  const fetchApplications = useCallback(async (statusFilter = null) => {
    if (!token || !user) {
      setError('请先登录');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('DEBUG: Fetching applications...');

      const params = {};
      if (statusFilter) {
        params.status = statusFilter;
      }

      const response = await ApplicationsService.getUserApplicationsApiV1ApplicationsApplicationsGet(
        params
      );

      console.log('DEBUG: Applications:', response);

      setApplications(response);

      // 计算状态统计
      const counts = {};
      STATUS_CHOICES.forEach(choice => {
        counts[choice.value] = response.filter(app => app.status === choice.value).length;
      });
      setStatusCounts(counts);

    } catch (err) {
      console.error('Failed to fetch applications:', err);
      setError(err.response?.data?.detail || '获取申请列表失败');
    } finally {
      setLoading(false);
    }
  }, [token, user]);

  /**
   * 更新申请状态
   * 对应Django的update_job_application_status
   */
  const updateApplicationStatus = useCallback(async (jobId, newStatus, notes = null) => {
    if (!token || !user) {
      setError('请先登录');
      return false;
    }

    try {
      console.log('DEBUG: Updating application status:', { jobId, newStatus });

      const updateData = { status: newStatus };
      if (notes !== undefined) {
        updateData.notes = notes;
      }

      await ApplicationsService.updateSavedJobApiV1ApplicationsJobsJobIdSavedPut(
        jobId,
        updateData
      );

      // 更新本地状态
      setApplications(prevApplications =>
        prevApplications.map(app =>
          app.job_listing.id === jobId
            ? { ...app, status: newStatus, notes: notes || app.notes }
            : app
        )
      );

      // 更新统计
      setStatusCounts(prevCounts => ({
        ...prevCounts,
        [newStatus]: (prevCounts[newStatus] || 0) + 1,
      }));

      return true;

    } catch (err) {
      console.error('Failed to update application status:', err);
      setError(err.response?.data?.detail || '更新状态失败');
      return false;
    }
  }, [token, user]);

  /**
   * 自动记录工作查看
   * 对应Django的job_detail_page中的自动保存逻辑
   */
  const recordJobView = useCallback(async (jobId) => {
    if (!token || !user) return;

    try {
      // 检查是否已存在记录
      const existingApplication = applications.find(app => app.job_listing.id === jobId);

      if (existingApplication && existingApplication.status === 'not_applied') {
        // 如果存在但状态是not_applied，更新为viewed
        await updateApplicationStatus(jobId, 'viewed');
      } else if (!existingApplication) {
        // 如果不存在，创建新记录，状态为viewed
        await ApplicationsService.createSavedJobApiV1ApplicationsJobsJobIdSavedPost(
          jobId,
          { status: 'viewed' }
        );

        // 刷新列表
        fetchApplications();
      }
    } catch (err) {
      console.error('Failed to record job view:', err);
      // 不显示错误，因为这个操作对用户是透明的
    }
  }, [token, user, applications, updateApplicationStatus, fetchApplications]);

  /**
   * 获取状态标签信息
   */
  const getStatusInfo = useCallback((status) => {
    return STATUS_CHOICES.find(choice => choice.value === status) || STATUS_CHOICES[0];
  }, []);

  /**
   * 批量更新状态
   */
  const bulkUpdateStatus = useCallback(async (jobIds, newStatus) => {
    if (!token || !user || !jobIds.length) {
      setError('请先登录并选择要更新的申请');
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      const promises = jobIds.map(jobId =>
        updateApplicationStatus(jobId, newStatus)
      );

      await Promise.all(promises);

      // 刷新列表
      await fetchApplications();

      return true;

    } catch (err) {
      console.error('Failed to bulk update status:', err);
      setError('批量更新失败');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token, user, updateApplicationStatus, fetchApplications]);

  /**
   * 删除申请记录
   */
  const deleteApplication = useCallback(async (jobId) => {
    if (!token || !user) {
      setError('请先登录');
      return false;
    }

    try {
      await ApplicationsService.deleteSavedJobApiV1ApplicationsJobsJobIdSavedDelete(
        jobId
      );

      // 更新本地状态
      setApplications(prevApplications =>
        prevApplications.filter(app => app.job_listing.id !== jobId)
      );

      // 刷新统计
      fetchApplications();

      return true;

    } catch (err) {
      console.error('Failed to delete application:', err);
      setError(err.response?.data?.detail || '删除失败');
      return false;
    }
  }, [token, user, fetchApplications]);

  return {
    applications,
    statusCounts,
    loading,
    error,
    STATUS_CHOICES,
    fetchApplications,
    updateApplicationStatus,
    recordJobView,
    getStatusInfo,
    bulkUpdateStatus,
    deleteApplication,
  };
};
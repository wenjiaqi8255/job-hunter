// SaveJobButton.jsx
// 对应Django工作卡片的保存/取消保存功能
// 对接API: /api/v1/applications/saved-jobs

import React, { useState, useEffect, useContext, useCallback } from 'react';
import axios from 'axios';
import { AuthContext } from '../../contexts/AuthContext';

const API_BASE_URL = '/api/v1';

const SaveJobButton = ({ jobId, initialSaved = false }) => {
  const { user, token } = useContext(AuthContext);
  const [saved, setSaved] = useState(initialSaved);
  const [loading, setLoading] = useState(false);
  const [hasCheckedStatus, setHasCheckedStatus] = useState(initialSaved); // 如果有初始状态，认为已经检查过

  // 检查工作是否已保存 - 只在需要时检查实际保存状态
  useEffect(() => {
    if (!user || !jobId) {
      console.log(`DEBUG: Skipping saved check - user: ${!!user}, jobId: ${!!jobId}`);
      return;
    }

    // 如果已经有可靠的初始状态且已经检查过，跳过检查
    if (hasCheckedStatus) {
      console.log(`DEBUG: Already checked status for job ${jobId}, skipping`);
      return;
    }

    // 如果有明确的初始状态（来自JobListPage），信任它
    if (initialSaved !== undefined) {
      console.log(`DEBUG: Using initialSaved ${initialSaved} for job ${jobId}`);
      setHasCheckedStatus(true);
      return;
    }

    console.log(`DEBUG: SaveJobButton checking saved status for job ${jobId}, user: ${user?.id}`);
    const checkIfSaved = async () => {
      console.log(`DEBUG: Checking saved status for job ${jobId}, user ${user.id}`);
      try {
        const response = await axios.get(
          `${API_BASE_URL}/applications/saved-jobs`,
          {
            params: { user_id: user.id },
            headers: { 'Authorization': `Bearer ${token}` }
          }
        );

        const isSaved = response.data.some(job => job.job_listing_id === jobId);
        console.log(`DEBUG: Job ${jobId} saved status: ${isSaved}`);
        setSaved(isSaved);
        setHasCheckedStatus(true); // 标记已经检查过状态
      } catch (error) {
        console.error('检查保存状态失败:', error);
      }
    };

    checkIfSaved();
  }, [user, jobId, token, initialSaved, hasCheckedStatus]);

  // 使用useCallback优化事件处理函数
  const handleSave = useCallback(async () => {
    if (!user) {
      alert('请先登录');
      return;
    }

    // 如果已经保存，直接返回
    if (saved) {
      console.log(`DEBUG: Job ${jobId} already saved, skipping save request`);
      return;
    }

    console.log(`DEBUG: Attempting to save job ${jobId} for user ${user.id}`);
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/applications/saved-jobs`,
        {
          job_listing_id: jobId,
          user_id: user.id,
          status: 'interested'
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      console.log(`DEBUG: Save successful for job ${jobId}, response:`, response.data);
      setSaved(true);
    } catch (error) {
      console.log(`DEBUG: Save error for job ${jobId}:`, error.response?.data);
      // 如果是"已保存"错误，实际上成功了
      if (error.response?.status === 400 && error.response.data.detail === "Job already saved") {
        console.log(`DEBUG: Job ${jobId} was already saved, updating state`);
        setSaved(true);
      } else {
        console.error('保存工作失败:', error);
        alert('保存失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  }, [user, token, jobId, saved]);

  const handleUnsave = useCallback(async () => {
    console.log(`DEBUG: handleUnsave called for job ${jobId}, saved state: ${saved}`);
    if (!saved) {
      console.log(`DEBUG: Job ${jobId} is not saved, skipping unsave`);
      return;
    }

    setLoading(true);
    try {
      console.log(`DEBUG: Getting saved jobs for user ${user.id} to find job ${jobId}`);
      // 获取保存的工作ID
      const response = await axios.get(
        `${API_BASE_URL}/applications/saved-jobs`,
        {
          params: { user_id: user.id },
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      const savedJob = response.data.find(job => job.job_listing_id === jobId);
      console.log(`DEBUG: Found saved job:`, savedJob);

      if (savedJob) {
        console.log(`DEBUG: Deleting saved job ${savedJob.id}`);
        await axios.delete(
          `${API_BASE_URL}/applications/saved-jobs/${savedJob.id}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        console.log(`DEBUG: Successfully deleted saved job ${savedJob.id}`);
        setSaved(false);
      } else {
        console.log(`DEBUG: No saved job found for job ${jobId}, updating state anyway`);
        setSaved(false); // 如果没找到但也认为未保存
      }
    } catch (error) {
      console.error('取消保存失败:', error);
      alert('操作失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [user, token, jobId, saved]);

  // 直接条件渲染，避免useMemo缓存问题
  return saved ? (
    <button
      className="btn btn-warning btn-sm"
      onClick={handleUnsave}
      disabled={loading}
    >
      {loading ? '取消中...' : '取消保存'}
    </button>
  ) : (
    <button
      className="btn btn-outline-primary btn-sm"
      onClick={handleSave}
      disabled={loading}
    >
      {loading ? '保存中...' : '保存职位'}
    </button>
  );
};

// 使用React.memo防止不必要的重新渲染
export default React.memo(SaveJobButton);

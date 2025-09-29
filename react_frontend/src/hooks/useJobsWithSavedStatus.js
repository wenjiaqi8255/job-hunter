import { useState, useEffect, useContext, useRef, useCallback } from 'react';
import axios from 'axios';
import { AuthContext } from '../contexts/AuthContext';

const API_BASE_URL = '/api/v1';

export const useJobsWithSavedStatus = (limit = null) => {
  const { token, user } = useContext(AuthContext);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Use a ref to track loading state for each limit value separately
  const loadingStates = useRef({});

  // Define loadJobs function outside useEffect so it can be used in refetch
  const loadJobs = useCallback(async () => {
    const limitKey = limit || 'all';

    try {
      console.log(`DEBUG: useJobsWithSavedStatus loading jobs (limit: ${limit})...`);
      const response = await axios.get(`${API_BASE_URL}/jobs/`);
      let jobsData = limit ? response.data.slice(0, limit) : response.data;

      // 如果用户已登录，获取保存状态
      if (user && token) {
        console.log('DEBUG: User logged in, fetching saved jobs...');
        try {
          const savedResponse = await axios.get(
            `${API_BASE_URL}/applications/saved-jobs`,
            {
              params: { user_id: user.id },
              headers: { 'Authorization': `Bearer ${token}` }
            }
          );

          const savedJobIds = savedResponse.data.map(job => job.job_listing_id);
          console.log(`DEBUG: Found ${savedJobIds.length} saved jobs`);

          // 为每个工作添加保存状态
          jobsData = jobsData.map(job => ({
            ...job,
            is_saved: savedJobIds.includes(job.id)
          }));
        } catch (err) {
          console.error('获取保存状态失败:', err);
        }
      }

      console.log(`DEBUG: Setting ${jobsData.length} jobs with saved status`);
      setJobs(jobsData);
      setLoading(false);
      loadingStates.current[limitKey] = true;
    } catch (err) {
      console.error('获取工作列表失败:', err);
      setError('加载失败');
      setLoading(false);
    }
  }, [token, user, limit]);

  useEffect(() => {
    // Create a unique key for this limit value
    const limitKey = limit || 'all';

    // 避免重复加载
    if (loadingStates.current[limitKey]) {
      console.log(`DEBUG: Already loaded jobs for limit ${limit}, skipping API call`);
      return;
    }

    loadJobs();
  }, [loadJobs, limit]); // Now loadJobs is a dependency

  return { jobs, loading, error, refetch: () => {
    // Reset loading state for this limit and reload
    const limitKey = limit || 'all';
    loadingStates.current[limitKey] = false;
    loadJobs();
  }};
};
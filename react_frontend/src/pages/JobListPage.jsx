// JobListPage.jsx
// 工作列表页面：展示所有职位，支持搜索和过滤

import React from 'react';
import JobCard from '../components/jobs/JobCard';
import { useJobsWithSavedStatus } from '../hooks/useJobsWithSavedStatus';

export default function JobListPage() {
  const { jobs, loading, error } = useJobsWithSavedStatus();

  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">工作列表</h1>
      {/* 对应Django all_jobs_annotated循环渲染JobCard */}
      {jobs.length === 0 ? (
        <div className="text-gray-500">暂无职位</div>
      ) : (
        jobs.map(job => <JobCard key={job.id} job={job} />)
      )}
    </div>
  );
}

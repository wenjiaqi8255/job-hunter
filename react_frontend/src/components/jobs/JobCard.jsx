// JobCard.jsx
// 对应Django main_page.html中的工作卡片静态部分
// 包含标题、公司、标签、描述、操作按钮

import React from 'react';
import SaveJobButton from '../applications/SaveJobButton';

export default function JobCard({ job }) {
  return (
    <div className="jobbAI-job-card border rounded-lg p-4 shadow hover:shadow-lg transition mb-4 bg-white">
      <h2 className="text-lg font-bold text-gray-800 mb-1">
        <a href={`/jobs/${job.id}`} className="text-blue-700 hover:underline">{job.job_title}</a>
      </h2>
      <p className="text-sm text-gray-600 mb-2">{job.company_name} · {job.location || 'N/A'}</p>
      <div className="flex flex-wrap gap-2 text-xs text-gray-500 mb-2">
        {job.level && <span><i className="fas fa-briefcase mr-1"></i>{job.level}</span>}
        {job.industry && <span><i className="fas fa-industry mr-1"></i>{job.industry}</span>}
        {job.flexibility && <span><i className="fas fa-clock mr-1"></i>{job.flexibility}</span>}
        {job.salary_range && <span><i className="fas fa-dollar-sign mr-1"></i>{job.salary_range}</span>}
      </div>
      <p className="mt-2 text-gray-700 line-clamp-2 text-sm">{job.description}</p>
      <div className="flex justify-end gap-2 mt-3">
        <a href={`/jobs/${job.id}`} className="btn btn-outline-secondary btn-sm">
          <i className="fas fa-info-circle mr-1"></i> 详情
        </a>
        {job.application_url ? (
          <a href={job.application_url} target="_blank" rel="noopener noreferrer" className="btn btn-success btn-sm">
            <i className="fas fa-external-link-alt mr-1"></i> 申请
          </a>
        ) : (
          <button type="button" className="btn btn-success btn-sm" disabled title="No application link available">
            <i className="fas fa-external-link-alt mr-1"></i> 申请
          </button>
        )}
        {/* 保存/取消保存按钮 */}
        <SaveJobButton jobId={job.id} initialSaved={job.is_saved || false} />
      </div>
    </div>
  );
}

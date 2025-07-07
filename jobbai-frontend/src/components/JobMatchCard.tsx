/**
 * 匹配工作卡片组件
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求实现
 * 使用新的JSONB结构化数据展示
 */

import { useState } from 'react';
import type { MatchedJob } from '../types';
import JobInsights from './JobInsights';

interface JobMatchCardProps {
  matchedJob: MatchedJob;
  onViewDetails?: (jobId: string) => void;
  onUpdateStatus?: (jobId: string, newStatus: string) => void;
}

const statusClasses: { [key: string]: string } = {
  applied: 'bg-status-applied-bg text-status-applied-text',
  interviewing: 'bg-status-interviewing-bg text-status-interviewing-text',
  offer: 'bg-status-offer-bg text-status-offer-text',
  rejected: 'bg-status-rejected-bg text-status-rejected-text',
  viewed: 'bg-status-viewed-bg text-status-viewed-text',
  not_applied: 'bg-status-not_applied-bg text-status-not_applied-text',
};

export function JobMatchCard({ matchedJob, onViewDetails, onUpdateStatus }: JobMatchCardProps) {
  const [isInsightsOpen, setIsInsightsOpen] = useState(false);

  const handleViewDetails = () => {
    onViewDetails?.(matchedJob.id);
  };

  const handleApplyNow = () => {
    if (matchedJob.applicationUrl) {
      window.open(matchedJob.applicationUrl, '_blank', 'noopener,noreferrer');
      onUpdateStatus?.(matchedJob.id, 'applied');
    }
  };

  const score = matchedJob.score || 0;
  const hasInsights = matchedJob.analysis && (matchedJob.analysis.pros?.length > 0 || matchedJob.analysis.cons?.length > 0);

  return (
    <div className="bg-cardBackground rounded-xl shadow-[0px_4px_12px_rgba(0,0,0,0.05)] hover:shadow-[0px_8px_20px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-200 ease-in-out p-4">
      {/* Card Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-base font-bold text-textPrimary mb-1">{matchedJob.title}</h3>
          <p className="text-sm text-textSecondary">{matchedJob.company}</p>
        </div>
        <div className="text-center ml-4 flex-shrink-0">
          <div className="w-16 h-16 bg-primary rounded-full flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-textPrimary">{score}</span>
          </div>
          <p className="text-xs text-textSecondary mt-1">Match Score</p>
        </div>
      </div>

      {/* Job Tags */}
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-textSecondary mb-4">
        {matchedJob.level && <span>📍 {matchedJob.level}</span>}
        {matchedJob.location && <span>📍 {matchedJob.location}</span>}
        {matchedJob.industry && <span>🏭 {matchedJob.industry}</span>}
        {matchedJob.flexibility && <span>⏰ {matchedJob.flexibility}</span>}
        {matchedJob.salaryRange && <span>💰 {matchedJob.salaryRange}</span>}
      </div>

      {/* Collapsible Insights */}
      {hasInsights && (
        <div className="border-t border-border pt-3">
          <button
            onClick={() => setIsInsightsOpen(!isInsightsOpen)}
            className="flex justify-between items-center w-full text-sm font-bold text-textPrimary"
          >
            <span>💡 Key Insights</span>
            <span>{isInsightsOpen ? '▲' : '▼'}</span>
          </button>
          {isInsightsOpen && <JobInsights analysis={matchedJob.analysis} />}
        </div>
      )}

      {/* Action Buttons & Status */}
      <div className="flex justify-between items-center mt-4">
        <div>
          <span className={`px-2.5 py-1.5 rounded-lg text-xs font-medium ${statusClasses[matchedJob.status] || statusClasses.not_applied}`}>
            {matchedJob.status}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleViewDetails}
            className="bg-primaryLight text-textPrimary rounded-full px-4 py-2 text-sm font-bold"
          >
            View Details
          </button>
          <button
            onClick={handleApplyNow}
            className="bg-primary text-textPrimary rounded-full px-4 py-2 text-sm font-bold hover:bg-primaryHover"
            disabled={!matchedJob.applicationUrl}
          >
            Apply Now
          </button>
        </div>
      </div>
    </div>
  );
}

export default JobMatchCard

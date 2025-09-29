// MatchCard.jsx
// 对应Django main_page.html中的匹配结果卡片静态部分
// 展示分数、状态、Insights、Tips等

import React from 'react';

const MatchCard = ({ match }) => (
  <div className="jobbAI-job-card border rounded-lg p-4 shadow mb-4 bg-white">
    <div className="flex justify-between items-start mb-2">
      <div>
        <h5 className="text-lg font-bold text-blue-700 mb-0">
          <a href={`/jobs/${match.job_object.id}`} className="hover:underline">{match.job_object.job_title}</a>
        </h5>
        <small className="text-gray-500">{match.job_object.company_name}</small>
      </div>
      <div className="text-center">
        <span className="text-2xl font-bold text-blue-600">{match.score}%</span>
        <div className="text-xs text-gray-400">Match Score</div>
      </div>
    </div>
    {/* 状态Badge静态展示 */}
    <div className="mb-2">
      {match.saved_status === 'applied' && <span className="badge bg-green-100 text-green-700 mr-2">已申请</span>}
      {match.saved_status === 'viewed' && <span className="badge bg-blue-100 text-blue-700 mr-2">已查看</span>}
      {match.is_saved && <span className="badge bg-yellow-100 text-yellow-700">已保存</span>}
    </div>
    {/* 标签区 */}
    <div className="flex flex-wrap gap-2 text-xs text-gray-500 mb-2">
      {match.job_object.level && <span><i className="fas fa-briefcase mr-1"></i>{match.job_object.level}</span>}
      {match.job_object.location && <span><i className="fas fa-map-marker-alt mr-1"></i>{match.job_object.location}</span>}
      {match.job_object.industry && <span><i className="fas fa-industry mr-1"></i>{match.job_object.industry}</span>}
      {match.job_object.flexibility && <span><i className="fas fa-clock mr-1"></i>{match.job_object.flexibility}</span>}
      {match.job_object.salary_range && <span><i className="fas fa-dollar-sign mr-1"></i>{match.job_object.salary_range}</span>}
    </div>
    {/* 匹配理由 */}
    <p className="text-sm text-gray-700 mb-2">{match.reason}</p>
    {/* Insights静态展示 */}
    {match.parsed_insights_list && (
      <div className="bg-gray-50 rounded p-2 mb-2">
        <strong className="text-green-700 text-sm"><i className="fas fa-lightbulb mr-1"></i>Key Insights</strong>
        <div className="flex gap-4 mt-1">
          <ul className="list-disc pl-4 text-xs text-green-700 flex-1">
            {match.parsed_insights_list.map(([pro, _], idx) => pro && <li key={idx}>{pro}</li>)}
          </ul>
          <ul className="list-disc pl-4 text-xs text-red-700 flex-1">
            {match.parsed_insights_list.map(([_, con], idx) => con && <li key={idx}>{con}</li>)}
          </ul>
        </div>
      </div>
    )}
    {/* Tips静态展示 */}
    {match.parsed_tips_list && (
      <div className="bg-blue-50 rounded p-2 mb-2">
        <strong className="text-blue-700 text-sm"><i className="fas fa-bullseye mr-1"></i>Application Tips</strong>
        <ul className="list-disc pl-4 text-xs mt-1">
          {match.parsed_tips_list.map((tip, idx) => <li key={idx}>{tip}</li>)}
        </ul>
      </div>
    )}
    {/* 操作按钮区 */}
    <div className="flex justify-end gap-2 mt-3">
      <a href={`/jobs/${match.job_object.id}`} className="btn btn-outline-secondary btn-sm">
        <i className="fas fa-info-circle mr-1"></i> 详情
      </a>
      {match.job_object.application_url ? (
        <a href={match.job_object.application_url} target="_blank" rel="noopener noreferrer" className="btn btn-success btn-sm">
          <i className="fas fa-external-link-alt mr-1"></i> 申请
        </a>
      ) : (
        <button type="button" className="btn btn-success btn-sm" disabled title="No application link available">
          <i className="fas fa-external-link-alt mr-1"></i> 申请
        </button>
      )}
    </div>
  </div>
);

export default MatchCard;

// JobDetailPage.jsx
// 工作详情页面：显示单个工作的详细信息

import React, { useEffect, useState, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../contexts/AuthContext';
import SaveJobButton from '../components/applications/SaveJobButton';
import ApplyModal from '../components/common/ApplyModal';

const API_BASE_URL = '/api/v1';

const JobDetailPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useContext(AuthContext);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showApplyModal, setShowApplyModal] = useState(false);

  useEffect(() => {
    const fetchJobDetail = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/jobs/${jobId}`);
        setJob(response.data);
      } catch (err) {
        console.error('获取工作详情失败:', err);
        setError('工作不存在或加载失败');
      } finally {
        setLoading(false);
      }
    };

    if (jobId) {
      fetchJobDetail();
    }
  }, [jobId]);

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">加载中...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-red-500">{error || '工作不存在'}</div>
        <button
          onClick={() => navigate('/jobs')}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← 返回工作列表
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      {/* 返回按钮 */}
      <button
        onClick={() => navigate('/jobs')}
        className="mb-6 text-blue-600 hover:text-blue-800 flex items-center"
      >
        ← 返回工作列表
      </button>

      {/* 工作详情 */}
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {job.job_title}
            </h1>
            <h2 className="text-xl text-gray-700 mb-4">
              {job.company_name}
            </h2>

            {/* 工作基本信息 */}
            <div className="flex flex-wrap gap-4 text-gray-600 mb-6">
              <span className="flex items-center">
                📍 {job.location}
              </span>
              {job.industry && (
                <span className="flex items-center">
                  🏢 {job.industry}
                </span>
              )}
              {job.salary_range && (
                <span className="flex items-center">
                  💰 {job.salary_range}
                </span>
              )}
              {job.flexibility && (
                <span className="flex items-center">
                  ⚡ {job.flexibility}
                </span>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex flex-col gap-3 ml-8">
            {user && (
              <SaveJobButton jobId={jobId} initialSaved={false} />
            )}
            {token ? (
              <button
                onClick={() => setShowApplyModal(true)}
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors"
              >
                立即申请
              </button>
            ) : (
              <a
                href="/login"
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors text-center block"
              >
                登录后申请
              </a>
            )}
            {job.application_url && (
              <a
                href={job.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700 transition-colors text-center block"
              >
                原始链接
              </a>
            )}
          </div>
        </div>

        {/* 工作描述 */}
        <div className="border-t pt-6">
          <h3 className="text-xl font-semibold mb-4">职位描述</h3>
          <div className="text-gray-700 whitespace-pre-wrap">
            {job.description || '暂无详细描述'}
          </div>
        </div>

        {/* 匹配原因（如果有的话） */}
        {job.reason_for_match && (
          <div className="border-t pt-6 mt-6">
            <h3 className="text-xl font-semibold mb-4">匹配原因</h3>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-blue-800">{job.reason_for_match}</p>
            </div>
          </div>
        )}

        {/* 创建时间 */}
        <div className="border-t pt-6 mt-6">
          <p className="text-sm text-gray-500">
            发布时间: {job.created_at ? new Date(job.created_at).toLocaleDateString() : '未知'}
          </p>
        </div>
      </div>

      {/* 申请模态框 */}
      {showApplyModal && (
        <ApplyModal
          job={job}
          onClose={() => setShowApplyModal(false)}
          onSuccess={() => {
            setShowApplyModal(false);
            alert('申请成功！');
          }}
        />
      )}
    </div>
  );
};

export default JobDetailPage;
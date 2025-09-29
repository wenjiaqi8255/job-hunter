// ApplicationHistoryPage.jsx
// 展示用户申请历史，对接API: /api/v1/applications/history

import React, { useEffect, useState, useContext } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';
// import { AuthContext } from '../../contexts/MockAuthContext';   

const ApplicationHistoryPage = () => {
  const { token, user } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) fetchHistory();
  }, [token]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      // 假设 user.id 可用，实际可根据后端接口调整
      const res = await DefaultService.getUserSavedJobsApiV1SavedJobsGet(user?.id);
      setHistory(res);
    } catch {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  if (!token) return <div className="p-8 text-center">请先登录</div>;
  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">申请历史</h1>
      {history.length === 0 ? (
        <div className="text-gray-500">暂无申请记录</div>
      ) : (
        <ul className="divide-y">
          {history.map(app => (
            <li key={app.id} className="py-4">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-bold text-blue-700">{app.job_title}</div>
                  <div className="text-sm text-gray-500">{app.company_name} · {app.status}</div>
                  <div className="text-xs text-gray-400">{app.applied_at}</div>
                </div>
                <a href={`/jobs/${app.job_id}`} className="btn btn-outline-secondary btn-sm">详情</a>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ApplicationHistoryPage;

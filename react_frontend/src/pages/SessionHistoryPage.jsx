// SessionHistoryPage.jsx
// 展示用户所有匹配会话历史，对应Django的all_matches.html
import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';
import { useToast } from '../hooks/useToast';

// TypeScript类型定义
const SessionHistoryPage = () => {
  const { token, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    has_next: false,
    has_prev: false
  });

  // 获取会话历史
  const fetchSessions = async (page = 1) => {
    if (!token || !user?.id) return;

    setLoading(true);
    setError('');
    try {
      const response = await DefaultService.getUserMatchSessionsApiV1MatchingSessionsGet(
        user.id,
        (page - 1) * pagination.limit,
        pagination.limit
      );

      setSessions(response.sessions || []);
      setPagination(prev => ({
        ...prev,
        page,
        total: response.total || 0,
        has_next: response.has_next || false,
        has_prev: page > 1
      }));
    } catch (err) {
      const errorMsg = '获取匹配历史失败';
      setError(errorMsg);
      showError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && user?.id) {
      fetchSessions();
    }
  }, [token, user?.id]);

  // 查看会话详情
  const handleViewSession = (sessionId) => {
    navigate(`/?session_id=${sessionId}`);
  };

  // 分页处理
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= Math.ceil(pagination.total / pagination.limit)) {
      fetchSessions(newPage);
    }
  };

  if (!token) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold mb-4">匹配历史</h1>
          <p className="text-gray-600 mb-4">请先登录查看您的匹配历史</p>
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            立即登录
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">匹配历史</h1>
        {sessions.length > 0 && (
          <p className="text-gray-600">浏览您过去所有的职位匹配会话记录</p>
        )}
      </div>

      {/* 错误信息 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center text-red-800">
            <i className="fas fa-exclamation-circle mr-2"></i>
            {error}
          </div>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      )}

      {/* 会话列表 */}
      {!loading && sessions.length > 0 && (
        <div className="space-y-4">
          {sessions.map((session) => (
            <div key={session.id} className="card session-card">
              <div className="card-body">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <h5 className="card-title mb-2">
                      <span className="text-decoration-none text-dark">
                        会话时间: {new Date(session.matched_at).toLocaleString('zh-CN', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </h5>
                    <p className="card-text mb-2">
                      <strong>偏好设置:</strong>
                      <span className="text-muted ms-2">
                        {session.user_preferences_text
                          ? `${session.user_preferences_text.substring(0, 150)}${session.user_preferences_text.length > 150 ? '...' : ''}`
                          : '未设置'
                        }
                      </span>
                    </p>
                    <p className="card-text">
                      <strong>匹配结果:</strong>
                      <span className="badge bg-primary ms-2">
                        {session.matched_jobs_count || 0} 个职位
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => handleViewSession(session.id)}
                    className="btn btn-sm btn-outline-primary ms-4"
                  >
                    查看详情 <i className="fas fa-arrow-right ms-1"></i>
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* 分页控件 */}
          {pagination.total > pagination.limit && (
            <nav aria-label="Page navigation" className="mt-6">
              <ul className="pagination justify-content-center">
                <li className={`page-item ${!pagination.has_prev ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => handlePageChange(1)}
                    disabled={!pagination.has_prev}
                  >
                    首页
                  </button>
                </li>
                <li className={`page-item ${!pagination.has_prev ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={!pagination.has_prev}
                  >
                    上一页
                  </button>
                </li>

                <li className="page-item active">
                  <span className="page-link">
                    第 {pagination.page} 页，共 {Math.ceil(pagination.total / pagination.limit)} 页
                  </span>
                </li>

                <li className={`page-item ${!pagination.has_next ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={!pagination.has_next}
                  >
                    下一页
                  </button>
                </li>
                <li className={`page-item ${!pagination.has_next ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => handlePageChange(Math.ceil(pagination.total / pagination.limit))}
                    disabled={!pagination.has_next}
                  >
                    末页
                  </button>
                </li>
              </ul>
            </nav>
          )}
        </div>
      )}

      {/* 无会话记录 */}
      {!loading && sessions.length === 0 && (
        <div className="text-center p-8 border rounded">
          <div className="text-gray-400 mb-4">
            <i className="fas fa-search fa-3x"></i>
          </div>
          <h2 className="h2 mb-3">暂无匹配会话</h2>
          <p className="lead text-gray-600 mb-4">
            您还没有开始任何职位匹配会话
          </p>
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary mt-3"
          >
            <i className="fas fa-plus me-2"></i>
            开始第一次匹配
          </button>
        </div>
      )}
    </div>
  );
};

export default SessionHistoryPage;
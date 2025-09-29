// MatchResultsPage.jsx
// 匹配结果页面：显示匹配列表和用户信息侧边栏
// 重构版本：使用useMatchResults Hook，支持会话ID参数，完整的匹配结果显示

import React, { useContext } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMatchResults } from '../hooks/useMatchResults';
import MatchList from '../components/matching/MatchList';
import CVBox from '../components/profile/CVBox';
import PreferencesBox from '../components/profile/PreferencesBox';
import { AuthContext } from '../contexts/AuthContext';

const MatchResultsPage = () => {
  const { token, user } = useContext(AuthContext);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session_id');

  const {
    matchResults,
    sessionInfo,
    loading,
    error,
    toggleSaveJob,
    refetch,
  } = useMatchResults();

  if (!token) {
    return (
      <div className="container mx-auto py-8 text-center">
        <h1 className="text-2xl font-bold mb-4">匹配结果</h1>
        <p className="text-gray-500 mb-4">请先登录查看匹配结果</p>
        <button
          onClick={() => navigate('/login')}
          className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
        >
          登录
        </button>
      </div>
    );
  }

  // 没有sessionId时显示欢迎页面
  if (!sessionId) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-4">欢迎回来，{user?.username}！</h1>
          <p className="text-gray-600 mb-6">
            选择一个匹配会话查看结果，或开始新的匹配
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            <i className="fas fa-search mr-2"></i>
            开始新的匹配
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* 页面标题和会话信息 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">匹配结果</h1>
            {sessionInfo && (
              <p className="text-gray-600">
                匹配时间: {new Date(sessionInfo.matched_at).toLocaleString()} |
                匹配工作数: {matchResults.length}
              </p>
            )}
          </div>
          <button
            onClick={() => navigate('/')}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            返回首页
          </button>
        </div>
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
          <p className="text-gray-600">正在加载匹配结果...</p>
        </div>
      )}

      {/* 无匹配结果 */}
      {!loading && matchResults.length === 0 && sessionId && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <i className="fas fa-search text-4xl"></i>
          </div>
          <h3 className="text-xl font-semibold mb-2">暂无匹配结果</h3>
          <p className="text-gray-600 mb-4">
            当前会话没有找到合适的工作匹配
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            重新匹配
          </button>
        </div>
      )}

      {/* 主要内容区域 */}
      {!loading && matchResults.length > 0 && (
        <div className="flex flex-col lg:flex-row gap-8">
          {/* 主内容区：匹配结果列表 */}
          <div className="flex-1">
            <MatchList
              matchResults={matchResults}
              onToggleSave={toggleSaveJob}
              onRefresh={refetch}
            />
          </div>

          {/* 右侧栏：CV和偏好展示 */}
          <div className="w-full lg:w-80 flex flex-col gap-4">
            <CVBox profile={sessionInfo?.skills_text || ''} />
            <PreferencesBox preferences={sessionInfo?.user_preferences_text || ''} />

            {/* 会话信息 */}
            {sessionInfo && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold mb-3">会话信息</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600">匹配时间:</span>
                    <span className="ml-2">
                      {new Date(sessionInfo.matched_at).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">匹配工作数:</span>
                    <span className="ml-2">{matchResults.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">会话ID:</span>
                    <span className="ml-2 font-mono text-xs">{sessionId}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchResultsPage;

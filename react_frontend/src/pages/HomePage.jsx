// HomePage.jsx
// 首页：包含欢迎区、AI匹配启动、推荐工作列表、用户状态感知
// 重构版本：整合MatchingWizard，支持匹配会话显示，完整的状态管理

import React, { useContext, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import MatchingWizard from '../components/matching/MatchingWizard';
import JobCard from '../components/jobs/JobCard';
import { useJobsWithSavedStatus } from '../hooks/useJobsWithSavedStatus';
import { useMatchResults } from '../hooks/useMatchResults';
import { useToast } from '../hooks/useToast.jsx';
import { AuthContext } from '../contexts/AuthContext';

const HomePage = () => {
  const { token, user } = useContext(AuthContext);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session_id');

  const { jobs: featuredJobs, loading: jobsLoading } = useJobsWithSavedStatus(6);
  const { matchResults, sessionInfo, loading: matchLoading, error: matchError } = useMatchResults();
  const { showError } = useToast();

  // 处理匹配错误
  useEffect(() => {
    if (matchError) {
      showError(matchError);
    }
  }, [matchError, showError]);

  // 如果有sessionId，显示匹配结果而不是欢迎页面
  if (sessionId) {
    return (
      <div className="container mx-auto py-8">
        {/* 匹配结果头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                欢迎回来，{user?.username}！
              </h1>
              {sessionInfo && (
                <p className="text-gray-600">
                  匹配时间: {new Date(sessionInfo.matched_at).toLocaleString()} |
                  找到 {matchResults.length} 个匹配工作
                </p>
              )}
            </div>
            <button
              onClick={() => {
                navigate('/');
                window.location.reload(); // 清除URL参数
              }}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              <i className="fas fa-home mr-2"></i>
              返回首页
            </button>
          </div>
        </div>

        {/* 错误信息 */}
        {matchError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center text-red-800">
              <i className="fas fa-exclamation-circle mr-2"></i>
              {matchError}
            </div>
          </div>
        )}

        {/* 加载状态 */}
        {matchLoading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">正在加载匹配结果...</p>
          </div>
        )}

        {/* 匹配结果 */}
        {!matchLoading && matchResults.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6">为你推荐的职位</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {matchResults.slice(0, 6).map((result) => (
                <JobCard
                  key={result.job_listing.id}
                  job={result.job_listing}
                  matchScore={result.score}
                  matchReason={result.reason}
                  isSaved={result.saved_status === 'saved'}
                />
              ))}
            </div>
            {matchResults.length > 6 && (
              <div className="text-center mt-6">
                <button
                  onClick={() => navigate('/matches')}
                  className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
                >
                  查看全部 {matchResults.length} 个匹配结果
                </button>
              </div>
            )}
          </div>
        )}

        {/* 无匹配结果 */}
        {!matchLoading && matchResults.length === 0 && sessionInfo && (
          <div className="text-center py-8 mb-8">
            <div className="text-gray-400 mb-4">
              <i className="fas fa-search text-4xl"></i>
            </div>
            <h3 className="text-xl font-semibold mb-2">暂无匹配结果</h3>
            <p className="text-gray-600 mb-4">
              当前会话没有找到合适的工作匹配
            </p>
            <MatchingWizard />
          </div>
        )}
      </div>
    );
  }

  // 默认首页（没有sessionId）
  return (
    <div className="container mx-auto py-8">
      {/* 欢迎区域 */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">
          {token ? `欢迎回来，${user?.username}！` : 'Transform Your Job Hunt with AI'}
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          {token
            ? '让我们为你找到最合适的工作机会'
            : 'AI驱动的智能职位匹配，为你推荐最适合的工作机会'
          }
        </p>

        {/* 匹配向导 */}
        <div className="max-w-2xl mx-auto">
          <MatchingWizard />
        </div>
      </div>

      {/* 推荐工作区域 */}
      <div className="mt-16">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">
            {token ? '推荐职位' : '热门职位'}
          </h2>
          {token && (
            <button
              onClick={() => navigate('/jobs')}
              className="text-blue-600 hover:text-blue-800 flex items-center"
            >
              查看全部 <i className="fas fa-arrow-right ml-1"></i>
            </button>
          )}
        </div>

        {jobsLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredJobs.map(job => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}

        {/* 未登录提示 */}
        {!token && (
          <div className="text-center mt-8 p-6 bg-blue-50 rounded-lg">
            <p className="text-blue-800 mb-4">
              登录后可享受个性化职位匹配和申请管理功能
            </p>
            <button
              onClick={() => navigate('/login')}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
            >
              立即登录
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;

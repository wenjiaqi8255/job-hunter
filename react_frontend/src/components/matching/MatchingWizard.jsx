// MatchingWizard.jsx
// 工作匹配向导组件，对应Django main_page.html中的匹配启动区域
// 重构版本：使用useMatching Hook，增加防抖、错误处理、用户体验优化

import React from 'react';
import { useMatching } from '../../hooks/useMatching';
import { AuthContext } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const MatchingWizard = () => {
  const { user, token } = React.useContext(AuthContext);
  const navigate = useNavigate();
  const { isMatching, error, startMatching } = useMatching();

  const handleStartMatching = async () => {
    await startMatching();
  };

  // 未登录状态或用户信息未加载
  if (!token || !user) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">Transform Your Job Hunt with AI</h2>
        <p className="text-gray-600 mb-6">
          To get personalized job matches, save applications, and use all features, please log in.
        </p>
        <button
          onClick={() => navigate('/login')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <i className="fas fa-sign-in-alt mr-2"></i>
          Login or Sign Up
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-8 text-center">
      <h2 className="text-2xl font-bold mb-3">
        Let's find the best matches for {user.username}!
      </h2>
      <p className="text-gray-600 mb-6">
        Your profile seems ready. Start a new session to discover jobs tailored for you.
      </p>

      {/* 错误信息显示 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center text-red-800">
            <i className="fas fa-exclamation-circle mr-2"></i>
            {error}
          </div>
        </div>
      )}

      {/* 匹配按钮 */}
      <button
        onClick={handleStartMatching}
        disabled={isMatching}
        className={`px-8 py-3 rounded-lg font-medium transition-colors ${
          isMatching
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isMatching ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
            Matching in progress...
          </div>
        ) : (
          <>
            <i className="fas fa-search mr-2"></i>
            Start Matching!
          </>
        )}
      </button>

      {/* 匹配进行中的状态提示 */}
      {isMatching && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center text-blue-800">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-800 mr-2"></div>
            <span className="text-sm">
              AI is analyzing your profile and matching with available jobs. This may take 30-60 seconds.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchingWizard;

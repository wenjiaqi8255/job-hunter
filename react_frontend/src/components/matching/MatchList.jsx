// MatchList.jsx
// 匹配结果列表组件，从API获取真实匹配数据

import React, { useEffect, useState, useContext } from 'react';
import MatchCard from './MatchCard';
import { AuthContext } from '../../contexts/AuthContext';
import { DefaultService } from '../../services/api_gen/services/DefaultService';

const MatchList = ({ sessionId }) => {
  const { token, user } = useContext(AuthContext);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMatches = async () => {
      if (!token || !user) return;

      try {
        let matchData;

        if (sessionId) {
          // 如果有sessionId，获取特定匹配会话
          matchData = await DefaultService.getMatchSessionDetailApiV1SessionsSessionIdGet(sessionId);
        } else {
          // 否则获取用户的最新匹配会话
          const sessions = await DefaultService.getUserMatchSessionsApiV1UsersUserIdSessionsGet(user.id);
          if (sessions && sessions.length > 0) {
            matchData = await DefaultService.getMatchSessionDetailApiV1SessionsSessionIdGet(sessions[0].id);
          }
        }

        if (matchData && matchData.matches) {
          // 转换数据格式以适配MatchCard组件
          const formattedMatches = matchData.matches.map(match => ({
            job_object: match.job_listing,
            score: match.score || 0,
            saved_status: match.saved_status || 'viewed',
            is_saved: match.is_saved || false,
            reason: match.reason || '',
            parsed_insights_list: match.insights ? match.insights.split('\n').filter(Boolean) : [],
            parsed_tips_list: match.tips ? match.tips.split('\n').filter(Boolean) : [],
          }));
          setMatches(formattedMatches);
        }
      } catch (err) {
        console.error('获取匹配数据失败:', err);
        setError('获取匹配数据失败');
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [token, user, sessionId]);

  if (!token) {
    return (
      <div className="max-w-2xl mx-auto p-4 text-center">
        <p className="text-gray-500">请先登录查看匹配结果</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto p-4 text-center">
        <p>加载中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-4 text-center">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="max-w-2xl mx-auto p-4 text-center">
        <p className="text-gray-500">暂无匹配结果，请先进行职位匹配</p>
        <a href="/matching/start" className="text-blue-600 hover:text-blue-800 mt-2 inline-block">
          开始匹配 →
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">{matches.length} 个匹配职位</h1>
        {sessionId && (
          <span className="text-gray-400">匹配结果</span>
        )}
      </div>
      {matches.map((match, idx) => (
        <MatchCard key={idx} match={match} />
      ))}
    </div>
  );
};

export default MatchList;

// MatchResultsDynamicPage.jsx
// 动态获取匹配结果，对接API: /api/v1/matching/results/{session_id}

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import MatchCard from '../components/matching/MatchCard';
import CVBox from '../components/profile/CVBox';
import PreferencesBox from '../components/profile/PreferencesBox';

const MatchResultsDynamicPage = () => {
  const { session_id } = useParams();
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line
  }, [session_id]);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const res = await DefaultService.getMatchSessionDetailApiV1SessionsSessionIdGet(session_id);
      setMatches(res.matches || []);
    } catch {
      setError('加载匹配结果失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="container mx-auto py-8 flex flex-col lg:flex-row gap-8">
      <div className="flex-1">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">{matches.length} Best Matches</h1>
          <span className="text-gray-400">Session: {session_id}</span>
        </div>
        {matches.length === 0 ? (
          <div className="text-gray-500">暂无匹配结果</div>
        ) : (
          matches.map((match, idx) => <MatchCard key={idx} match={match} />)
        )}
      </div>
      <div className="w-full lg:w-80 flex flex-col gap-4">
        <CVBox />
        <PreferencesBox />
      </div>
    </div>
  );
};

export default MatchResultsDynamicPage;

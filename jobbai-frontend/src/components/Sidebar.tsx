import { useEffect, useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { matchApi } from '../services/api'
import type { MatchSession } from '../types'

function Sidebar() {
  const { isAuthenticated } = useAuthStore()
  const [matchHistory, setMatchHistory] = useState<MatchSession[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 获取匹配历史
  const fetchMatchHistory = async () => {
    if (!isAuthenticated) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await matchApi.getMatchHistory(10)
      if (response.success && response.data) {
        setMatchHistory(response.data.sessions)
      } else {
        setError(response.error || 'Failed to fetch match history')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  // 当认证状态变化时获取匹配历史
  useEffect(() => {
    if (isAuthenticated) {
      fetchMatchHistory()
    } else {
      setMatchHistory([])
    }
  }, [isAuthenticated])

  // 触发新匹配
  const handleNewMatch = async () => {
    if (!isAuthenticated) return
    
    try {
      const response = await matchApi.triggerMatch()
      if (response.success) {
        // 重新获取匹配历史
        await fetchMatchHistory()
      }
    } catch (err) {
      console.error('Failed to trigger new match:', err)
    }
  }

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 获取今日匹配
  const today = new Date().toDateString()
  const todayMatches = matchHistory.filter(session => 
    new Date(session.matched_at).toDateString() === today
  )

  // 获取历史匹配
  const historyMatches = matchHistory.filter(session => 
    new Date(session.matched_at).toDateString() !== today
  )

  return (
    <nav className="w-80 bg-white border-r border-gray-200 h-screen sticky top-0">
      <div className="p-4">
        {/* 开始新匹配按钮 */}
        <div className="mb-6">
          <button 
            onClick={handleNewMatch}
            disabled={!isAuthenticated}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-300"
          >
            <i className="fas fa-plus-circle mr-2"></i>
            Start New Match
          </button>
        </div>

        {/* 认证用户内容 */}
        {isAuthenticated && (
          <>
            {/* 今日匹配 */}
            <div className="mb-6">
              <h6 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                Today's Matches
              </h6>
              <div className="space-y-2">
                {loading && (
                  <div className="p-2 text-sm text-gray-600 bg-gray-50 rounded">
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    Loading...
                  </div>
                )}
                {error && (
                  <div className="p-2 text-sm text-red-600 bg-red-50 rounded">
                    <i className="fas fa-exclamation-triangle mr-2"></i>
                    {error}
                  </div>
                )}
                {!loading && !error && todayMatches.length === 0 && (
                  <div className="p-2 text-sm text-gray-600 bg-gray-50 rounded">
                    <i className="fas fa-calendar-day mr-2"></i>
                    <span>No matches today.</span>
                  </div>
                )}
                {todayMatches.map(session => (
                  <div key={session.id} className="p-2 text-sm bg-blue-50 rounded hover:bg-blue-100 cursor-pointer">
                    <i className="fas fa-calendar-day mr-2 text-blue-600"></i>
                    <span>{formatDate(session.matched_at)} - {session.job_count} jobs</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 历史匹配 */}
            <div className="mb-6">
              <h6 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                History Matches
              </h6>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {!loading && !error && historyMatches.length === 0 && (
                  <div className="p-2 text-sm text-gray-600 bg-gray-50 rounded">
                    <i className="fas fa-history mr-2"></i>
                    <span>No match history yet.</span>
                  </div>
                )}
                {historyMatches.map(session => (
                  <div key={session.id} className="p-2 text-sm bg-gray-50 rounded hover:bg-gray-100 cursor-pointer">
                    <i className="fas fa-history mr-2 text-gray-600"></i>
                    <span>{formatDate(session.matched_at)} - {session.job_count} jobs</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* 访客提示 */}
        {!isAuthenticated && (
          <div className="mt-6 p-3 bg-blue-50 rounded-lg">
            <div className="text-sm text-blue-700">
              <i className="fas fa-sign-in-alt mr-2"></i>
              <span>Log in to view your match history and save jobs.</span>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

export default Sidebar

import { useState } from 'react'
import { useJobsStore } from '../stores/jobsStore'

interface AIMatchButtonProps {
  onMatchComplete?: () => void
}

function AIMatchButton({ onMatchComplete }: AIMatchButtonProps) {
  const { triggerAIMatch, loading } = useJobsStore()
  const [isMatching, setIsMatching] = useState(false)
  
  const handleAIMatch = async () => {
    setIsMatching(true)
    try {
      await triggerAIMatch()
      onMatchComplete?.()
    } catch (error) {
      console.error('AI match failed:', error)
    } finally {
      setIsMatching(false)
    }
  }

  return (
    <button
      onClick={handleAIMatch}
      disabled={loading || isMatching}
      className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
        loading || isMatching
          ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
          : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700'
      }`}
    >
      {loading || isMatching ? (
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          AI匹配中...
        </div>
      ) : (
        <div className="flex items-center justify-center">
          <i className="fas fa-robot mr-2"></i>
          开始AI智能匹配
        </div>
      )}
    </button>
  )
}

export default AIMatchButton

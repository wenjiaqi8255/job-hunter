import { useEffect, useState } from 'react'
import { matchApi } from '../services/api'

function DebugSessionPage() {
  const [apiResponse, setApiResponse] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const testAPI = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('Testing matchApi.getMatchHistory(1)...')
      const response = await matchApi.getMatchHistory(1)
      console.log('Raw API response:', response)
      setApiResponse(response)
    } catch (err) {
      console.error('API test error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    testAPI()
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Debug Session API</h1>
      
      <button 
        onClick={testAPI}
        className="bg-blue-600 text-white px-4 py-2 rounded mb-4"
        disabled={loading}
      >
        {loading ? 'Testing...' : 'Test API'}
      </button>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      {apiResponse && (
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">API Response:</h2>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(apiResponse, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default DebugSessionPage

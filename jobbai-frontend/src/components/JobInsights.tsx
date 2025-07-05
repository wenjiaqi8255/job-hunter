import type { JobInsight } from '../types'

interface JobInsightsProps {
  insights: JobInsight[]
}

function JobInsights({ insights }: JobInsightsProps) {
  if (!insights || insights.length === 0) {
    return null
  }

  return (
    <div className="mb-8">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        <i className="fas fa-list-ul text-blue-600 mr-2"></i>
        关键洞察
      </h3>
      
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-sm font-medium text-green-700 w-1/2">
                  <i className="fas fa-check-circle mr-2"></i>
                  优势
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-red-700 w-1/2">
                  <i className="fas fa-times-circle mr-2"></i>
                  需要注意
                </th>
              </tr>
            </thead>
            <tbody>
              {insights.map((insight, index) => (
                <tr key={index} className="border-t border-gray-200">
                  <td className="px-4 py-3 align-top">
                    {insight.pros && insight.pros.length > 0 ? (
                      <ul className="space-y-1">
                        {insight.pros.map((pro, proIndex) => (
                          <li key={proIndex} className="text-sm text-green-700 flex items-start">
                            <i className="fas fa-check-circle text-green-500 mr-2 mt-0.5 flex-shrink-0"></i>
                            <span>{pro}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-sm text-gray-500">无</span>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top">
                    {insight.cons && insight.cons.length > 0 ? (
                      <ul className="space-y-1">
                        {insight.cons.map((con, conIndex) => (
                          <li key={conIndex} className="text-sm text-red-700 flex items-start">
                            <i className="fas fa-times-circle text-red-500 mr-2 mt-0.5 flex-shrink-0"></i>
                            <span>{con}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-sm text-gray-500">无</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default JobInsights

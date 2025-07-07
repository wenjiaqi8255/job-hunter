import type { AnalysisData } from '../types'

interface JobInsightsProps {
  analysis: AnalysisData | undefined | null
}

function JobInsights({ analysis }: JobInsightsProps) {
  if (!analysis || (!analysis.pros?.length && !analysis.cons?.length)) {
    return null
  }

  return (
    <div className="mt-3 text-xs">
      <div className="grid grid-cols-2 gap-4">
        {/* Pros */}
        <div>
          <h4 className="font-bold text-success mb-1">Pros</h4>
          <ul className="list-disc list-inside text-textSecondary space-y-1">
            {analysis.pros?.map((pro, i) => <li key={i}>{pro}</li>)}
          </ul>
        </div>

        {/* Cons */}
        <div>
          <h4 className="font-bold text-danger mb-1">Cons</h4>
          <ul className="list-disc list-inside text-textSecondary space-y-1">
            {analysis.cons?.map((con, i) => <li key={i}>{con}</li>)}
          </ul>
        </div>
      </div>
    </div>
  )
}

export default JobInsights

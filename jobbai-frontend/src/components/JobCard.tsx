import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'
import type { Job } from '../types'
import JobInsights from './JobInsights'

interface JobCardProps {
  job: Job
  showMatchScore?: boolean
}

function JobCard({ job, showMatchScore = true }: JobCardProps) {
  const [isInsightsOpen, setIsInsightsOpen] = useState(false)
  const { selectedSessionId } = useSessionStore()
  const navigate = useNavigate()
  
  const handleViewDetails = () => {
    const path = selectedSessionId 
      ? `/sessions/${selectedSessionId}/jobs/${job.id}` 
      : `/jobs/${job.id}`
    navigate(path)
  }
  
  const handleApplyNow = () => {
    if (job.applicationUrl) {
      window.open(job.applicationUrl, '_blank', 'noopener,noreferrer')
    }
  }

  const score = job.score || 0
  const hasInsights = job.analysis && (job.analysis.pros?.length > 0 || job.analysis.cons?.length > 0)

  return (
    <div className="bg-cardBackground rounded-xl shadow-[0px_4px_12px_rgba(0,0,0,0.05)] hover:shadow-[0px_8px_20px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-200 ease-in-out p-4">
      {/* Card Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-base font-bold text-textPrimary mb-1">{job.title}</h3>
          <p className="text-sm text-textSecondary">{job.company}</p>
        </div>
        {showMatchScore && score > 0 && (
          <div className="text-center ml-4 flex-shrink-0">
            <div className="w-16 h-16 bg-primary rounded-full flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-textPrimary">{score}</span>
            </div>
            <p className="text-xs text-textSecondary mt-1">Match Score</p>
          </div>
        )}
      </div>

      {/* Job Tags */}
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-textSecondary mb-4">
        {job.level && <span>📍 {job.level}</span>}
        {job.location && <span>📍 {job.location}</span>}
        {job.industry && <span>🏭 {job.industry}</span>}
        {job.flexibility && <span>⏰ {job.flexibility}</span>}
        {job.salaryRange && <span>💰 {job.salaryRange}</span>}
      </div>

      {/* Collapsible Insights */}
      {hasInsights && (
        <div className="border-t border-border pt-3">
          <button
            onClick={() => setIsInsightsOpen(!isInsightsOpen)}
            className="flex justify-between items-center w-full text-sm font-bold text-textPrimary"
          >
            <span>💡 Key Insights</span>
            <span>{isInsightsOpen ? '▲' : '▼'}</span>
          </button>
          {isInsightsOpen && (
             <JobInsights analysis={job.analysis} />
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end items-center gap-2 mt-4">
        <button
          onClick={handleViewDetails}
          className="bg-primaryLight text-textPrimary rounded-full px-4 py-2 text-sm font-bold"
        >
          View Details
        </button>
        <button
          onClick={handleApplyNow}
          className="bg-primary text-textPrimary rounded-full px-4 py-2 text-sm font-bold hover:bg-primaryHover"
        >
          Apply Now
        </button>
      </div>
    </div>
  )
}

export default JobCard

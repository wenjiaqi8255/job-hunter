import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useJobsStore } from '../stores/jobsStore'
import { useAuthStore } from '../stores/authStore'
import LoadingSpinner from '../components/LoadingSpinner'
import AuthenticatedJobActions from '../components/AuthenticatedJobActions'
import GuestJobPrompt from '../components/GuestJobPrompt'
import Breadcrumb from '../components/Breadcrumb'
import type { Job } from '../types'
import { jobsApi } from '../services/api'
import PageLayout from '../components/PageLayout'
import JobInsights from '../components/JobInsights'

function JobDetailPage() {
  const { id } = useParams<{ id: string; }>()
  const navigate = useNavigate()
  const { getJobById, jobs } = useJobsStore()
  const { isAuthenticated } = useAuthStore()
  
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [savedJobStatus, setSavedJobStatus] = useState<string>('not_applied')
  const [savedJobNotes, setSavedJobNotes] = useState<string>('')

  const loadSavedJobStatus = async (jobId: string) => {
    if (!isAuthenticated) return
    try {
      const response = await jobsApi.getJobSavedStatus(jobId)
      if (response.success && response.data) {
        const savedData = response.data as import('../types').JobSavedStatusApiResponse
        setSavedJobStatus(savedData.status || 'not_applied')
        setSavedJobNotes(savedData.notes || '')
      }
    } catch (error) {
      console.error('Failed to load saved job status:', error)
    }
  }

  useEffect(() => {
    if (!id) {
      navigate('/')
      return
    }

    const fetchJobData = async () => {
      setLoading(true)
      setError(null)
      try {
        let jobData = getJobById(id)
        if (!jobData) {
          const response = await jobsApi.getJobDetail(id)
          if (response.success && response.data?.job) {
            jobData = response.data.job
          } else {
            throw new Error(response.error || 'Job not found')
          }
        }
        setJob(jobData)
        if (isAuthenticated) {
          await loadSavedJobStatus(id)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred.')
      } finally {
        setLoading(false)
      }
    }

    fetchJobData()
  }, [id, getJobById, navigate, jobs, isAuthenticated])
  
  const handleSaveJob = async (status: string, notes: string) => {
    if (!job || !isAuthenticated) {
      throw new Error('User not logged in or job data not available.')
    }
    const response = await jobsApi.saveJob(job.id, status, notes)
    if (response.success) {
      setSavedJobStatus(status)
      setSavedJobNotes(notes)
    } else {
      throw new Error(response.error || 'Failed to save job status.')
    }
  }

  if (loading) {
    return (
      <PageLayout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner />
        </div>
      </PageLayout>
    )
  }

  if (error || !job) {
    return (
      <PageLayout>
        <div className="text-center py-12">
          <h2 className="text-xl font-bold text-danger">Error</h2>
          <p className="text-textSecondary">{error || 'Job could not be loaded.'}</p>
        </div>
      </PageLayout>
    )
  }

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: 'Jobs', href: '/' },
    { label: job.title, active: true },
  ]

  return (
    <PageLayout className="max-w-4xl mx-auto p-4 md:p-6">
      <Breadcrumb items={breadcrumbItems} />
      
      <div className="bg-white rounded-xl shadow-sm border border-border mt-4">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-bold text-textPrimary">{job.title}</h1>
          <p className="text-textSecondary mt-1">{job.company}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-textSecondary mt-2">
            {job.level && <span>📍 {job.level}</span>}
            {job.location && <span>📍 {job.location}</span>}
            {job.industry && <span>🏭 {job.industry}</span>}
            {job.flexibility && <span>⏰ {job.flexibility}</span>}
            {job.salaryRange && <span>💰 {job.salaryRange}</span>}
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="prose max-w-none text-textSecondary" dangerouslySetInnerHTML={{ __html: job.description || '' }} />

          {job.analysis && <JobInsights analysis={job.analysis} />}
        </div>

        {/* Actions */}
        <div className="p-6 bg-gray-50 border-t border-border rounded-b-xl">
          {isAuthenticated ? (
            <AuthenticatedJobActions 
              jobId={job.id}
              onSave={handleSaveJob}
              initialStatus={savedJobStatus}
              initialNotes={savedJobNotes}
            />
          ) : <GuestJobPrompt />}
        </div>
      </div>
    </PageLayout>
  )
}

export default JobDetailPage

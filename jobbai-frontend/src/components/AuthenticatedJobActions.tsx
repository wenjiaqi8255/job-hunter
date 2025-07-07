import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

interface AuthenticatedJobActionsProps {
  onSave: (status: string, notes: string) => Promise<void>
  initialStatus?: string
  initialNotes?: string
  jobId?: string
}

// 状态选择选项
const STATUS_OPTIONS = [
  { value: 'not_applied', label: 'Not Applied' },
  { value: 'bookmarked', label: 'Bookmarked' },
  { value: 'applied', label: 'Applied' },
  { value: 'interviewing', label: 'Interviewing' },
  { value: 'offer_received', label: 'Offer Received' },
  { value: 'rejected', label: 'Rejected' },
]

function AuthenticatedJobActions({ 
  onSave, 
  initialStatus = 'not_applied',
  initialNotes = '',
  jobId
}: AuthenticatedJobActionsProps) {
  const navigate = useNavigate()
  const [status, setStatus] = useState(initialStatus)
  const [notes, setNotes] = useState(initialNotes)
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    setStatus(initialStatus)
    setNotes(initialNotes)
  }, [initialStatus, initialNotes])

  const handleSave = async () => {
    if (saving) return
    
    setSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)
    
    try {
      await onSave(status, notes)
      setSuccessMessage('Status saved successfully!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (error) {
      setErrorMessage('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-lg p-4">
      <h3 className="text-lg font-bold text-textPrimary mb-4">Application Actions</h3>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-textSecondary mb-1">
            Application Status
          </label>
          <select
            id="status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-textSecondary mb-1">
            Notes
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Add your notes here..."
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary text-textPrimary py-2 px-4 rounded-lg text-sm font-bold hover:bg-primaryHover disabled:bg-gray-300"
        >
          {saving ? 'Saving...' : 'Save Status & Notes'}
        </button>
      </div>
      
      {jobId && (
        <div className="mt-4 space-y-2">
          <button
            onClick={() => navigate(`/jobs/${jobId}/cover-letter`)}
            className="w-full bg-primaryLight text-textPrimary py-2 px-4 rounded-lg text-sm font-bold"
          >
            Generate Cover Letter
          </button>
          <button
            onClick={() => navigate(`/jobs/${jobId}/custom-cv`)}
            className="w-full bg-primaryLight text-textPrimary py-2 px-4 rounded-lg text-sm font-bold"
          >
            Customize CV
          </button>
        </div>
      )}

      {successMessage && (
        <div className="mt-3 p-3 bg-success/10 text-success text-sm rounded-lg">
          {successMessage}
        </div>
      )}
      
      {errorMessage && (
        <div className="mt-3 p-3 bg-danger/10 text-danger text-sm rounded-lg">
          {errorMessage}
        </div>
      )}
    </div>
  )
}

export default AuthenticatedJobActions

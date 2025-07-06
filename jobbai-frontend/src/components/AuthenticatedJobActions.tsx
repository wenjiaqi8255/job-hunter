import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface AuthenticatedJobActionsProps {
  onSave: (status: string, notes: string) => Promise<void>
  initialStatus?: string
  initialNotes?: string
  jobId?: string
}

// 状态选择选项
const STATUS_OPTIONS = [
  { value: 'not_applied', label: '未申请' },
  { value: 'bookmarked', label: '已收藏' },
  { value: 'applied', label: '已申请' },
  { value: 'interviewing', label: '面试中' },
  { value: 'offer_received', label: '已获得Offer' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'withdrawn', label: '已撤回' },
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

  const handleSave = async () => {
    if (saving) return
    
    try {
      setSaving(true)
      setErrorMessage(null)
      setSuccessMessage(null)
      
      await onSave(status, notes)
      setSuccessMessage('状态已保存')
      
      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000)
      
    } catch (error) {
      console.error('保存工作状态失败:', error)
      setErrorMessage('保存失败，请稍后重试')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 sticky top-6">
      <div className="p-6">
        <div className="flex items-center mb-4">
          <i className="fas fa-clipboard-check text-blue-600 mr-3"></i>
          <h3 className="text-lg font-medium text-gray-900">申请状态与笔记</h3>
        </div>
        
        {/* 状态选择器 */}
        <div className="mb-4">
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
            申请状态
          </label>
          <select
            id="status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 笔记输入框 */}
        <div className="mb-4">
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
            笔记
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="添加关于这个职位的笔记..."
          />
        </div>

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {saving ? (
            <>
              <i className="fas fa-spinner fa-spin mr-2"></i>
              保存中...
            </>
          ) : (
            <>
              <i className="fas fa-save mr-2"></i>
              保存状态与笔记
            </>
          )}
        </button>
        
        {/* 生成求职信按钮 */}
        {jobId && (
          <button
            onClick={() => navigate(`/jobs/${jobId}/cover-letter`)}
            className="w-full mt-3 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <i className="fas fa-file-alt mr-2"></i>
            生成求职信
          </button>
        )}

        {/* 生成定制简历按钮 */}
        {jobId && (
          <button
            onClick={() => navigate(`/jobs/${jobId}/custom-cv`)}
            className="w-full mt-3 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
          >
            <i className="fas fa-file-user mr-2"></i>
            定制简历
          </button>
        )}

        {/* 成功/错误消息 */}
        {successMessage && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center">
              <i className="fas fa-check-circle text-green-600 mr-2"></i>
              <span className="text-sm text-green-800">{successMessage}</span>
            </div>
          </div>
        )}
        
        {errorMessage && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <i className="fas fa-exclamation-circle text-red-600 mr-2"></i>
              <span className="text-sm text-red-800">{errorMessage}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AuthenticatedJobActions

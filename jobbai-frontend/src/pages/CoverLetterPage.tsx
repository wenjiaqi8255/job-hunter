import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { jobsApi, coverLetterApi } from '../services/api'
import type { Job, CoverLetter } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import Breadcrumb from '../components/Breadcrumb'

const CoverLetterPage: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  
  const [job, setJob] = useState<Job | null>(null)
  const [coverLetter, setCoverLetter] = useState<CoverLetter | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 如果未登录，重定向到登录页
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
  }, [isAuthenticated, navigate])

  // 加载工作信息
  useEffect(() => {
    if (!jobId) return
    
    const loadJob = async () => {
      try {
        const response = await jobsApi.getJobDetail(jobId)
        if (response.success && response.data) {
          setJob(response.data.job)
        } else {
          setError('无法加载工作信息')
        }
      } catch (err) {
        setError('加载工作信息失败')
        console.error('Error loading job:', err)
      }
    }

    loadJob()
  }, [jobId])

  // 加载现有求职信
  useEffect(() => {
    if (!jobId || !isAuthenticated) return
    
    const loadCoverLetter = async () => {
      try {
        const response = await coverLetterApi.getCoverLetter(jobId)
        if (response.success && response.data) {
          setCoverLetter({
            id: '', // API响应中不包含id
            user_id: user?.id || '',
            original_job_id: jobId,
            company_name: response.data.cover_letter?.company_name || '',
            job_title: response.data.cover_letter?.job_title || '',
            content: response.data.cover_letter?.content || '',
            created_at: response.data.cover_letter?.created_at || '',
            updated_at: response.data.cover_letter?.updated_at || ''
          })
        }
      } catch (err) {
        // 没有找到求职信是正常的，不需要显示错误
        console.log('No existing cover letter found')
      } finally {
        setIsLoading(false)
      }
    }

    loadCoverLetter()
  }, [jobId, isAuthenticated, user?.id])

  // 生成求职信
  const handleGenerateCoverLetter = async () => {
    if (!jobId) return
    
    setIsGenerating(true)
    setError(null)
    
    try {
      console.log('[DEBUG] Starting cover letter generation for job:', jobId)
      const response = await coverLetterApi.generateCoverLetter(jobId)
      console.log('[DEBUG] Cover letter generation response:', response)
      
      if (response.success && response.data) {
        console.log('[DEBUG] Cover letter generated successfully')
        setCoverLetter({
          id: '', // API响应中不包含id
          user_id: user?.id || '',
          original_job_id: jobId,
          company_name: response.data.cover_letter?.company_name || '',
          job_title: response.data.cover_letter?.job_title || '',
          content: response.data.cover_letter?.content || '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
      } else {
        console.error('[DEBUG] Cover letter generation failed:', response.error)
        setError(response.error || '生成求职信失败')
      }
    } catch (err) {
      console.error('[DEBUG] Cover letter generation error:', err)
      setError('生成求职信时发生错误')
      console.error('Error generating cover letter:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // 复制求职信内容
  const handleCopyCoverLetter = () => {
    if (!coverLetter?.content) return
    
    navigator.clipboard.writeText(coverLetter.content)
      .then(() => {
        alert('求职信已复制到剪贴板！')
      })
      .catch(() => {
        alert('复制失败，请手动选择文本复制')
      })
  }

  // 保存求职信
  const handleSaveCoverLetter = async () => {
    if (!jobId || !coverLetter?.content) return
    
    setIsSaving(true)
    setError(null)
    
    try {
      console.log('[DEBUG] Starting cover letter save for job:', jobId)
      console.log('[DEBUG] Cover letter content length:', coverLetter.content.length)
      
      const response = await coverLetterApi.updateCoverLetter(jobId, coverLetter.content)
      console.log('[DEBUG] Cover letter save response:', response)
      
      if (response.success) {
        console.log('[DEBUG] Cover letter saved successfully')
        // 更新本地状态
        setCoverLetter(prev => prev ? { 
          ...prev, 
          updated_at: new Date().toISOString() 
        } : null)
        
        // 显示成功提示
        alert('求职信已成功保存！')
      } else {
        console.error('[DEBUG] Cover letter save failed:', response.error)
        setError(response.error || '保存求职信失败')
      }
    } catch (err) {
      console.error('[DEBUG] Cover letter save error:', err)
      setError('保存求职信时发生错误')
      console.error('Error saving cover letter:', err)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">工作信息不存在</h2>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-800"
          >
            返回主页
          </button>
        </div>
      </div>
    )
  }

  const breadcrumbItems = [
    { label: '主页', href: '/' },
    { label: '工作详情', href: `/jobs/${jobId}` },
    { label: '求职信生成', href: `/jobs/${jobId}/cover-letter` }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Breadcrumb items={breadcrumbItems} />
        
        <div className="mt-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            求职信生成
          </h1>
          <p className="text-gray-600 mb-6">
            为 <span className="font-medium">{job.company}</span> 的 
            <span className="font-medium">{job.title}</span> 职位生成个性化求职信
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              {coverLetter ? '生成的求职信' : '生成求职信'}
            </h2>
          </div>
          
          <div className="p-6">
            {coverLetter ? (
              <div>
                <textarea
                  value={coverLetter.content}
                  onChange={(e) => setCoverLetter(prev => prev ? { ...prev, content: e.target.value } : null)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="求职信内容..."
                />
                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-gray-500">
                    {coverLetter.updated_at && (
                      <span>最后更新: {new Date(coverLetter.updated_at).toLocaleString()}</span>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={handleSaveCoverLetter}
                      disabled={isSaving}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                    >
                      {isSaving ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          保存中...
                        </>
                      ) : (
                        <>
                          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                          </svg>
                          保存
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleCopyCoverLetter}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      复制文本
                    </button>
                    <button
                      onClick={handleGenerateCoverLetter}
                      disabled={isGenerating}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          重新生成中...
                        </>
                      ) : (
                        <>
                          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          重新生成
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 48 48">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">还没有求职信</h3>
                <p className="mt-2 text-sm text-gray-500">
                  基于您的简历和这个职位，我们将为您生成个性化的求职信。
                </p>
                <div className="mt-6">
                  <button
                    onClick={handleGenerateCoverLetter}
                    disabled={isGenerating}
                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        AI生成中...
                      </>
                    ) : (
                      <>
                        <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        生成求职信
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CoverLetterPage

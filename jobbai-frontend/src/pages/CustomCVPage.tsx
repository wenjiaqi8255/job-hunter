import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { jobsApi, customCvApi } from '../services/api'
import type { Job } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import Breadcrumb from '../components/Breadcrumb'

// 定制简历类型
interface CustomCV {
  id: string
  user_id: string
  job_id: string
  content: string
  customization_notes?: string
  job_title: string
  company_name: string
  created_at: string
}

const CustomCVPage: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  
  const [job, setJob] = useState<Job | null>(null)
  const [customCV, setCustomCV] = useState<CustomCV | null>(null)
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

  // 加载现有定制简历
  useEffect(() => {
    if (!jobId || !isAuthenticated) return
    
    const loadCustomCV = async () => {
      try {
        const response = await customCvApi.getCustomCv(jobId)
        if (response.success && response.data) {
          setCustomCV({
            id: '', // API响应中不包含id
            user_id: user?.id || '',
            job_id: jobId,
            content: response.data.custom_cv?.content || '',
            customization_notes: response.data.custom_cv?.customization_notes || '',
            job_title: response.data.custom_cv?.job_title || '',
            company_name: response.data.custom_cv?.company_name || '',
            created_at: response.data.custom_cv?.created_at || ''
          })
        }
      } catch (err) {
        // 没有找到定制简历是正常的，不需要显示错误
        console.log('No existing custom CV found')
      } finally {
        setIsLoading(false)
      }
    }

    loadCustomCV()
  }, [jobId, isAuthenticated, user?.id])

  // 生成定制简历
  const handleGenerateCustomCV = async () => {
    if (!jobId) return
    
    setIsGenerating(true)
    setError(null)
    
    try {
      console.log('[DEBUG] Starting custom CV generation for job:', jobId)
      const response = await customCvApi.generateCustomCv(jobId)
      console.log('[DEBUG] Custom CV generation response:', response)
      
      if (response.success && response.data) {
        console.log('[DEBUG] Custom CV generated successfully')
        setCustomCV({
          id: '', // API响应中不包含id
          user_id: user?.id || '',
          job_id: jobId,
          content: response.data.custom_cv?.content || '',
          customization_notes: response.data.custom_cv?.customization_notes || '',
          job_title: response.data.custom_cv?.job_title || '',
          company_name: response.data.custom_cv?.company_name || '',
          created_at: new Date().toISOString()
        })
      } else {
        console.error('[DEBUG] Custom CV generation failed:', response.error)
        setError(response.error || '生成定制简历失败')
      }
    } catch (err) {
      console.error('[DEBUG] Custom CV generation error:', err)
      setError('生成定制简历时发生错误')
      console.error('Error generating custom CV:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // 复制定制简历内容
  const handleCopyCustomCV = () => {
    if (!customCV?.content) return
    
    navigator.clipboard.writeText(customCV.content)
      .then(() => {
        alert('定制简历已复制到剪贴板！')
      })
      .catch(() => {
        alert('复制失败，请手动选择文本复制')
      })
  }

  // 保存定制简历
  const handleSaveCustomCV = async () => {
    if (!jobId || !customCV?.content) return
    
    setIsSaving(true)
    setError(null)
    
    try {
      console.log('[DEBUG] Starting custom CV save for job:', jobId)
      console.log('[DEBUG] Custom CV content length:', customCV.content.length)
      
      const response = await customCvApi.updateCustomCv(jobId, customCV.content, customCV.customization_notes)
      console.log('[DEBUG] Custom CV save response:', response)
      
      if (response.success) {
        console.log('[DEBUG] Custom CV saved successfully')
        // 更新本地状态
        setCustomCV(prev => prev ? { 
          ...prev, 
          created_at: new Date().toISOString() 
        } : null)
        
        // 显示成功提示
        alert('定制简历已成功保存！')
      } else {
        console.error('[DEBUG] Custom CV save failed:', response.error)
        setError(response.error || '保存定制简历失败')
      }
    } catch (err) {
      console.error('[DEBUG] Custom CV save error:', err)
      setError('保存定制简历时发生错误')
      console.error('Error saving custom CV:', err)
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
    { label: '定制简历', href: `/jobs/${jobId}/custom-cv` }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Breadcrumb items={breadcrumbItems} />
        
        <div className="mt-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            定制简历生成
          </h1>
          <p className="text-gray-600 mb-6">
            为 <span className="font-medium">{job.company}</span> 的 
            <span className="font-medium">{job.title}</span> 职位生成个性化定制简历
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
              {customCV ? '生成的定制简历' : '生成定制简历'}
            </h2>
          </div>
          
          <div className="p-6">
            {customCV ? (
              <div>
                <textarea
                  value={customCV.content}
                  onChange={(e) => setCustomCV(prev => prev ? { ...prev, content: e.target.value } : null)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="定制简历内容..."
                />
                
                {/* 定制备注 */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    定制备注（可选）
                  </label>
                  <textarea
                    value={customCV.customization_notes || ''}
                    onChange={(e) => setCustomCV(prev => prev ? { ...prev, customization_notes: e.target.value } : null)}
                    className="w-full h-24 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="记录定制的要点、特殊调整等..."
                  />
                </div>
                
                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-gray-500">
                    {customCV.created_at && (
                      <span>最后更新: {new Date(customCV.created_at).toLocaleString()}</span>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={handleSaveCustomCV}
                      disabled={isSaving}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                    >
                      {isSaving ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          保存中...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          保存
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={handleCopyCustomCV}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      复制
                    </button>
                    
                    <button
                      onClick={handleGenerateCustomCV}
                      disabled={isGenerating}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          重新生成中...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  还没有定制简历
                </h3>
                <p className="text-gray-600 mb-6">
                  点击下方按钮，AI将根据您的简历和工作要求生成个性化的定制简历
                </p>
                <button
                  onClick={handleGenerateCustomCV}
                  disabled={isGenerating}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      生成中...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      生成定制简历
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CustomCVPage

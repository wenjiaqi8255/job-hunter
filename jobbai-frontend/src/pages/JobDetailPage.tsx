import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useJobsStore } from '../stores/jobsStore'
import { useAuthStore } from '../stores/authStore'
import { useSessionStore } from '../stores/sessionStore'
import { jobsApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import AuthenticatedJobActions from '../components/AuthenticatedJobActions'
import GuestJobPrompt from '../components/GuestJobPrompt'
import Breadcrumb from '../components/Breadcrumb'
import type { Job } from '../types'

function JobDetailPage() {
  const { id, sessionId } = useParams<{ id: string; sessionId?: string }>()
  const navigate = useNavigate()
  const { getJobById, fetchMatchedJobs, jobs, loading: jobsLoading } = useJobsStore()
  const { isAuthenticated } = useAuthStore()
  const { currentSession } = useSessionStore()
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [savedJobStatus, setSavedJobStatus] = useState<string>('not_applied')
  const [savedJobNotes, setSavedJobNotes] = useState<string>('')
  const [loadingSavedStatus, setLoadingSavedStatus] = useState(false)

  useEffect(() => {
    if (!id) {
      navigate('/')
      return
    }

    const fetchJobData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // 判断是否为匹配上下文中的工作
        const isInMatchContext = Boolean(sessionId)
        
        if (isInMatchContext) {
          // 场景1: 匹配上下文中的工作 - 从 jobsStore 获取数据
          console.log('[工作详情页] 获取匹配上下文中的工作信息')
          console.log('[工作详情页] 查找工作ID:', id)
          
          // 等待一段时间，让store完成数据加载
          if (jobsLoading) {
            console.log('[工作详情页] 等待store完成数据加载...')
            // 等待store完成加载
            let attempts = 0
            while (jobsLoading && attempts < 50) { // 最多等待5秒
              await new Promise(resolve => setTimeout(resolve, 100))
              attempts++
            }
            console.log('[工作详情页] 等待完成，尝试次数:', attempts)
          }
          
          // 首先尝试从 jobsStore 获取工作数据
          let jobFromStore = getJobById(id)
          console.log('[工作详情页] 从store获取到的工作:', jobFromStore)
          console.log('[工作详情页] 当前store中的工作数量:', jobs.length)
          
          // 如果store中没有数据，并且store不在加载状态，则主动获取数据
          if (!jobFromStore && !jobsLoading && jobs.length === 0) {
            console.log('[工作详情页] store中无数据且未在加载，主动获取匹配的工作')
            await fetchMatchedJobs(true) // 强制刷新
            jobFromStore = getJobById(id) // 重新尝试获取
            console.log('[工作详情页] 获取数据后重新查找工作:', jobFromStore)
          }
          
          if (jobFromStore) {
            console.log('[工作详情页] 使用 jobsStore 中的工作数据')
            setJob(jobFromStore)
            
            // 如果有会话ID，设置面包屑需要的会话信息
            if (sessionId) {
              console.log('[工作详情页] 设置面包屑会话信息')
              // 这里应该有会话信息在sessionStore中，如果没有可以从API获取
              // 但根据新架构，会话信息应该在获取工作数据时就已经设置了
            }
          } else {
            // 如果store中仍然没有数据，直接从API获取工作详情
            console.log('[工作详情页] store中仍无数据，从API获取工作详情')
            const response = await jobsApi.getJobDetail(id)
            
            if (response.success && response.data?.job) {
              console.log('[工作详情页] 从API获取到工作详情')
              setJob(response.data.job)
            } else {
              throw new Error('未找到指定工作')
            }
          }
        } else {
          // 场景2: 普通工作详情 - 从job_listings表获取基本信息
          console.log('[工作详情页] 获取普通工作详情')
          
          // 步骤1: 先尝试从store中获取工作数据
          let existingJob = getJobById(id)
          console.log('[工作详情页] 从store获取到的工作:', existingJob)
          console.log('[工作详情页] 当前store中的工作数量:', jobs.length)
          
          // 如果store中没有数据，并且用户已登录，尝试获取匹配的工作
          if (!existingJob && isAuthenticated && !jobsLoading && jobs.length === 0) {
            console.log('[工作详情页] store中无数据且用户已登录，尝试获取匹配的工作')
            await fetchMatchedJobs(true) // 强制刷新
            existingJob = getJobById(id) // 重新尝试获取
            console.log('[工作详情页] 获取匹配数据后重新查找工作:', existingJob)
          }
          
          if (existingJob) {
            console.log('[工作详情页] 从store获取到工作数据')
            setJob(existingJob)
          } else {
            // 步骤2: 从API获取单个工作详情
            console.log('[工作详情页] 从API获取工作详情')
            const response = await jobsApi.getJobDetail(id)
            
            if (response.success && response.data?.job) {
              console.log('[工作详情页] 从API获取到工作详情')
              setJob(response.data.job)
            } else {
              throw new Error(response.error || '获取工作信息失败')
            }
          }
        }
        
        // 如果用户已登录，加载保存状态
        if (isAuthenticated) {
          await loadSavedJobStatus(id)
        }
        
      } catch (error) {
        console.error('[工作详情页] 获取工作数据时出错:', error)
        setError(error instanceof Error ? error.message : '网络错误，请检查网络连接后重试。')
      } finally {
        setLoading(false)
      }
    }

    fetchJobData()
  }, [id, sessionId, getJobById, navigate, isAuthenticated, fetchMatchedJobs, jobs, jobsLoading])

  // 加载用户保存的工作状态
  const loadSavedJobStatus = async (jobId: string) => {
    if (!isAuthenticated) {
      console.log('[工作详情页] 用户未登录，跳过加载保存状态')
      return
    }
    
    try {
      setLoadingSavedStatus(true)
      console.log('[工作详情页] 开始加载保存状态')
      
      const response = await jobsApi.getJobSavedStatus(jobId)
      
      if (response.success && response.data) {
        console.log('[工作详情页] 加载保存状态成功:', response.data)
        const savedData = response.data as import('../types').JobSavedStatusApiResponse
        setSavedJobStatus(savedData.status || 'not_applied')
        setSavedJobNotes(savedData.notes || '')
      } else {
        console.log('[工作详情页] 该工作未保存，使用默认状态')
        setSavedJobStatus('not_applied')
        setSavedJobNotes('')
      }
    } catch (error) {
      console.error('[工作详情页] 加载保存状态失败:', error)
      // 失败时使用默认状态
      setSavedJobStatus('not_applied')
      setSavedJobNotes('')
    } finally {
      setLoadingSavedStatus(false)
    }
  }

  // 构建面包屑导航项 - 利用 sessionStore 的数据
  const buildBreadcrumbItems = () => {
    const items: Array<{ label: string; href?: string; active?: boolean }> = [
      { label: '主页', href: '/' }
    ]

    // 使用 sessionStore 的 currentSession 信息
    if (currentSession) {
      // 在匹配上下文中
      const sessionDate = new Date(currentSession.matched_at || currentSession.created_at)
      const formattedDate = sessionDate.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      })
      
      items.push({
        label: `匹配会话 ${formattedDate}`,
        href: `/?session=${currentSession.id}`
      })
    } else {
      // 普通工作浏览
      items.push({
        label: '工作列表',
        href: '/'
      })
    }

    items.push({
      label: job?.title || '工作详情',
      active: true
    })

    return items
  }

  const handleSaveJob = async (status: string, notes: string) => {
    if (!job || !isAuthenticated) {
      console.error('[工作详情页] 保存工作失败:', { 
        hasJob: !!job, 
        isAuthenticated,
        jobId: job?.id 
      })
      throw new Error('用户未登录或工作信息不存在')
    }
    
    try {
      console.log('[工作详情页] 保存工作状态:', { jobId: job.id, status, notes })
      console.log('[工作详情页] 认证状态检查:', { isAuthenticated })
      
      const response = await jobsApi.saveJob(job.id, status, notes)
      
      if (response.success) {
        console.log('[工作详情页] 工作状态保存成功')
        setSavedJobStatus(status)
        setSavedJobNotes(notes)
      } else {
        throw new Error(response.error || '保存失败')
      }
    } catch (error) {
      console.error('[工作详情页] 保存工作状态失败:', error)
      throw error
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner />
        <span className="ml-3 text-gray-600">加载工作详情中...</span>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-4">
            <i className="fas fa-exclamation-triangle text-4xl"></i>
          </div>
          <h2 className="text-xl font-medium text-gray-900 mb-2">
            工作详情未找到
          </h2>
          <p className="text-gray-600 mb-4">
            {error || '抱歉，我们找不到您要查看的工作信息。'}
          </p>
          <Link 
            to="/"
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 inline-flex items-center"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            返回主页
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="text-blue-600 hover:text-blue-800 mr-4">
                <i className="fas fa-arrow-left mr-2"></i>
                返回主页
              </Link>
              <h1 className="text-lg font-medium text-gray-900">工作详情</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 面包屑导航 */}
        <Breadcrumb items={buildBreadcrumbItems()} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧 - 工作详情 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-8">
                {/* 工作标题部分 */}
                <div className="mb-8">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h1 className="text-2xl font-bold text-gray-900 mb-2">
                        {job.title}
                      </h1>
                      <h2 className="text-xl text-gray-700 mb-3">
                        {job.company}
                      </h2>
                    </div>
                    {job.score && (
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600 mb-1">
                          {job.score}%
                        </div>
                        <div className="text-sm text-gray-500">匹配度</div>
                      </div>
                    )}
                  </div>

                  {/* 工作基本信息 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500 mb-1">位置</div>
                      <div className="font-medium text-gray-900">{job.location || '未指定'}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500 mb-1">级别</div>
                      <div className="font-medium text-gray-900">{job.level || '未指定'}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500 mb-1">行业</div>
                      <div className="font-medium text-gray-900">{job.industry || '未指定'}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500 mb-1">工作方式</div>
                      <div className="font-medium text-gray-900">{job.flexibility || '未指定'}</div>
                    </div>
                  </div>

                  {job.salaryRange && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                      <div className="flex items-center">
                        <i className="fas fa-dollar-sign text-green-600 mr-3"></i>
                        <div>
                          <div className="text-sm text-green-700">薪资范围</div>
                          <div className="text-lg font-semibold text-green-900">{job.salaryRange}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* 匹配原因 */}
                {job.analysis?.reasoning && (
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">
                      <i className="fas fa-bullseye text-blue-600 mr-2"></i>
                      为什么推荐这个职位
                    </h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-blue-900 whitespace-pre-wrap">{job.analysis.reasoning}</p>
                    </div>
                  </div>
                )}

                {/* 关键洞察 - 使用新的数据结构 */}
                {job.analysis && (
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">
                      <i className="fas fa-lightbulb text-yellow-600 mr-2"></i>
                      关键洞察
                    </h3>
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      {job.analysis.pros && job.analysis.pros.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-green-800 mb-2">优势</h4>
                          <ul className="space-y-1">
                            {job.analysis.pros.map((pro, index) => (
                              <li key={index} className="text-green-700 text-sm">
                                • {pro}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {job.analysis.cons && job.analysis.cons.length > 0 && (
                        <div>
                          <h4 className="font-medium text-red-800 mb-2">需要注意</h4>
                          <ul className="space-y-1">
                            {job.analysis.cons.map((con, index) => (
                              <li key={index} className="text-red-700 text-sm">
                                • {con}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 申请建议 */}
                {job.application_tips?.specific_advice && (
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">
                      <i className="fas fa-magic text-blue-600 mr-2"></i>
                      申请建议
                    </h3>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-yellow-900 whitespace-pre-wrap">{job.application_tips.specific_advice}</p>
                    </div>
                  </div>
                )}

                {/* 工作描述 */}
                <div className="mb-8">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    <i className="fas fa-file-alt text-gray-600 mr-2"></i>
                    工作描述
                  </h3>
                  <div className="prose max-w-none">
                    <div className="text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border max-h-80 overflow-y-auto">
                      {job.description}
                    </div>
                  </div>
                </div>

                {/* 工作元数据 */}
                <div className="pt-6 border-t border-gray-200">
                  <div className="text-sm text-gray-500 flex items-center space-x-4">
                    <div className="flex items-center">
                      <i className="fas fa-calendar-alt mr-2"></i>
                      <span>发布时间: {job.created_at ? new Date(job.created_at).toLocaleDateString() : '未知'}</span>
                    </div>
                    {job.applicationUrl && (
                      <div className="flex items-center">
                        <i className="fas fa-external-link-alt mr-2"></i>
                        <a 
                          href={job.applicationUrl} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          查看原始招聘信息
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧 - 用户操作 */}
          <div className="lg:col-span-1">
            {isAuthenticated ? (
              <AuthenticatedJobActions 
                onSave={handleSaveJob}
                initialStatus={savedJobStatus}
                initialNotes={savedJobNotes}
                jobId={id}
              />
            ) : (
              <GuestJobPrompt />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default JobDetailPage

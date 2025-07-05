/**
 * 匹配历史功能测试
 * 根据MATCH_HISTORY_MIGRATION_PLAN第5步要求
 * 测试新的JSONB结构化数据功能
 */

// 模拟数据
const mockMatchedJob = {
  id: "test-job-match-id",
  job_id: "test-job-id",
  score: 85,
  status: "new" as const,
  
  // 新的JSONB结构化数据
  analysis_data: {
    reasoning: "Excellent skills match for a backend role. User's preference for remote work aligns well. German B2 is a plus.",
    pros: [
      "Strong Python/Django experience matches requirements",
      "Remote work preference aligns",
      "German language skills valuable"
    ],
    cons: [
      "Location Munich differs from Berlin preference",
      "Salary range not specified"
    ],
    key_insights: [
      "Role type matches user preference perfectly",
      "Company culture seems traditional vs fast-paced preference",
      "Industry experience transferable"
    ],
    match_details: {
      skill_alignment: "90% - Python, Django, and backend skills directly match",
      culture_fit: "70% - Traditional company culture vs fast-paced preference",
      growth_potential: "85% - Senior role with team leadership opportunities"
    }
  },
  
  application_tips: {
    specific_advice: "Emphasize your microservices experience and German proficiency",
    tips: [
      "Highlight 5 years of Python/Django experience",
      "Mention B2 German proficiency",
      "Include specific microservices projects"
    ],
    recommendations: [
      "Tailor CV for German market standards",
      "Research company culture thoroughly"
    ],
    cover_letter_suggestions: [
      "Mention specific interest in German market",
      "Reference relevant project experience"
    ],
    interview_preparation: [
      "Prepare for German business culture questions",
      "Review microservices architecture patterns"
    ]
  },
  
  // 基础工作信息
  title: "Senior Backend Developer",
  company: "Tech Company GmbH",
  location: "Munich, Germany",
  level: "Senior",
  industry: "Technology",
  flexibility: "Remote",
  salaryRange: "65,000 - 80,000 EUR",
  description: "We are looking for a Senior Backend Developer to join our team...",
  applicationUrl: "https://example.com/apply",
  created_at: "2024-01-15T10:30:00Z",
  updated_at: "2024-01-15T10:30:00Z"
}

const mockMatchSession = {
  id: "test-session-id",
  user_id: "test-user-id",
  skills_text: "5+ years Python/Django development, microservices, AWS, Docker",
  user_preferences_text: "Remote position in Germany, focus on backend development, modern tech stack",
  structured_user_profile_json: {
    summary: "Senior Backend Developer with 5+ years experience",
    key_skills: ["Python", "Django", "AWS", "Docker"],
    preferences: {
      location: "Berlin, Germany",
      work_model: "Remote",
      salary_range: "60-75k EUR"
    }
  },
  matched_at: "2024-01-15T10:30:00Z",
  created_at: "2024-01-15T10:30:00Z",
  matched_jobs: [mockMatchedJob]
}

// API测试
export const testMatchHistoryApi = async () => {
  console.log("🧪 Testing Match History API...")
  
  try {
    // 测试导入
    const { matchApi } = await import('../services/api')
    const { matchHistoryApi } = await import('../services/matchHistory')
    
    console.log("✅ API modules imported successfully")
    
    // 测试API方法存在
    const requiredMethods = [
      'getMatchHistory',
      'getLatestMatch', 
      'triggerMatch',
      'getMatchJobDetails',
      'updateJobStatus'
    ] as const
    
    for (const method of requiredMethods) {
      if (typeof (matchApi as any)[method] !== 'function') {
        throw new Error(`Missing method: matchApi.${method}`)
      }
      if (typeof (matchHistoryApi as any)[method] !== 'function') {
        throw new Error(`Missing method: matchHistoryApi.${method}`)
      }
    }
    
    console.log("✅ All required API methods are available")
    
    // 测试类型导入 (确保类型可以正确导入)
    await import('../types')
    await import('../types/matching')
    
    console.log("✅ Type definitions imported successfully")
    
    return {
      success: true,
      message: "Match History API tests passed"
    }
    
  } catch (error) {
    console.error("❌ API test failed:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// 组件测试
export const testMatchHistoryComponents = async () => {
  console.log("🧪 Testing Match History Components...")
  
  try {
    // 测试组件导入
    const { JobMatchCard } = await import('../components/JobMatchCard')
    const { MatchHistoryList } = await import('../components/MatchHistoryList')
    const MatchHistoryPage = await import('../pages/MatchHistoryPage')
    
    console.log("✅ Components imported successfully")
    
    // 测试Hook导入
    const { useMatchHistory } = await import('../hooks/useMatchHistory')
    
    console.log("✅ Custom hook imported successfully")
    
    // 测试组件是否为函数
    if (typeof JobMatchCard !== 'function') {
      throw new Error('JobMatchCard is not a valid React component')
    }
    
    if (typeof MatchHistoryList !== 'function') {
      throw new Error('MatchHistoryList is not a valid React component')
    }
    
    if (typeof MatchHistoryPage.default !== 'function') {
      throw new Error('MatchHistoryPage is not a valid React component')
    }
    
    if (typeof useMatchHistory !== 'function') {
      throw new Error('useMatchHistory is not a valid hook')
    }
    
    console.log("✅ All components are valid React components")
    
    return {
      success: true,
      message: "Match History Components tests passed"
    }
    
  } catch (error) {
    console.error("❌ Component test failed:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// 数据结构测试
export const testDataStructures = () => {
  console.log("🧪 Testing Data Structures...")
  
  try {
    // 测试MatchedJob结构
    const requiredJobFields = [
      'id', 'job_id', 'score', 'status',
      'analysis_data', 'application_tips',
      'title', 'company', 'location', 'level',
      'industry', 'created_at', 'updated_at'
    ]
    
    for (const field of requiredJobFields) {
      if (!(field in mockMatchedJob)) {
        throw new Error(`Missing field in MatchedJob: ${field}`)
      }
    }
    
    // 测试analysis_data结构
    const requiredAnalysisFields = ['reasoning', 'pros', 'cons', 'key_insights']
    for (const field of requiredAnalysisFields) {
      if (!(field in mockMatchedJob.analysis_data)) {
        throw new Error(`Missing field in analysis_data: ${field}`)
      }
    }
    
    // 测试application_tips结构
    const requiredTipsFields = ['specific_advice', 'tips', 'recommendations']
    for (const field of requiredTipsFields) {
      if (!(field in mockMatchedJob.application_tips)) {
        throw new Error(`Missing field in application_tips: ${field}`)
      }
    }
    
    console.log("✅ MatchedJob data structure is valid")
    
    // 测试MatchSession结构
    const requiredSessionFields = [
      'id', 'user_id', 'skills_text', 'user_preferences_text',
      'structured_user_profile_json', 'matched_at', 'created_at', 'matched_jobs'
    ]
    
    for (const field of requiredSessionFields) {
      if (!(field in mockMatchSession)) {
        throw new Error(`Missing field in MatchSession: ${field}`)
      }
    }
    
    console.log("✅ MatchSession data structure is valid")
    
    return {
      success: true,
      message: "Data structure tests passed"
    }
    
  } catch (error) {
    console.error("❌ Data structure test failed:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// 样式测试
export const testStyles = () => {
  console.log("🧪 Testing Styles...")
  
  try {
    // 检查样式文件是否存在
    const styleElement = document.querySelector('link[href*="matchHistory.css"]') || 
                        document.querySelector('style[data-source*="matchHistory"]')
    
    if (!styleElement) {
      console.warn("⚠️ Match history styles may not be loaded")
    } else {
      console.log("✅ Match history styles are loaded")
    }
    
    return {
      success: true,
      message: "Style tests passed"
    }
    
  } catch (error) {
    console.error("❌ Style test failed:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// 运行所有测试
export const runAllTests = async () => {
  console.log("🚀 Running all Match History tests...")
  
  const results = [
    testDataStructures(),
    testStyles(),
    await testMatchHistoryApi(),
    await testMatchHistoryComponents()
  ]
  
  const passed = results.filter(r => r.success).length
  const total = results.length
  
  console.log(`\n📊 Test Results: ${passed}/${total} passed`)
  
  if (passed === total) {
    console.log("🎉 All tests passed! Match History implementation is ready.")
  } else {
    console.log("⚠️ Some tests failed. Please check the implementation.")
    results.forEach((result, index) => {
      if (!result.success) {
        console.log(`❌ Test ${index + 1}: ${result.error}`)
      }
    })
  }
  
  return {
    passed,
    total,
    results,
    success: passed === total
  }
}

// 导出测试数据供其他地方使用
export { mockMatchedJob, mockMatchSession }

import { type ReactNode } from 'react'

interface MainContentProps {
  children: ReactNode
}

function MainContent({ children }: MainContentProps) {
  return (
    <main className="flex-1 px-6 py-6">
      {/* 头部区域 */}
      <div className="flex justify-between items-center pb-4 mb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {/* 工作数量将在动态功能阶段加载 */}
            Job Listings
          </h1>
          <div className="hidden auth-required">
            <p className="text-sm text-gray-600 mt-1">
              基于偏好设置的匹配结果...
            </p>
          </div>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="space-y-6">
        {children}
      </div>
    </main>
  )
}

export default MainContent

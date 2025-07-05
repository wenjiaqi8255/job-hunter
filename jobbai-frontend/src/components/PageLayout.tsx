import { type ReactNode } from 'react'
import Navbar from './Navbar'
import Footer from './Footer'

interface PageLayoutProps {
  children: ReactNode
  className?: string
}

function PageLayout({ children, className = '' }: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航栏 */}
      <Navbar />

      {/* 主要内容容器 - 添加顶部间距以避免被固定导航栏遮挡 */}
      <div className={`pt-16 flex-1 ${className}`}>
        {children}
      </div>

      {/* 底部页脚 */}
      <Footer />
    </div>
  )
}

export default PageLayout

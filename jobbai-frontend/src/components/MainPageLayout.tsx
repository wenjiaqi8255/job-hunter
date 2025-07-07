import { type ReactNode } from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

interface MainPageLayoutProps {
  children: ReactNode
}

function MainPageLayout({ children }: MainPageLayoutProps) {
  return (
    <div className="min-h-screen bg-pageBackground">
      <Navbar />
      <div className="flex pt-14">
        <Sidebar />
        <main className="flex-1 md:ml-80 p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

export default MainPageLayout

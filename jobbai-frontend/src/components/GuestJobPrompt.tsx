import { Link } from 'react-router-dom'

function GuestJobPrompt() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 sticky top-6">
      <div className="p-6 text-center">
        <div className="mb-4">
          <i className="fas fa-lock text-gray-400 text-4xl"></i>
        </div>
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          保存您的进度
        </h3>
        
        <p className="text-gray-600 mb-6">
          请登录或注册以保存工作、跟踪申请状态和添加笔记。
        </p>
        
        <Link
          to="/profile"
          className="inline-flex items-center justify-center w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <i className="fas fa-user mr-2"></i>
          登录 / 注册
        </Link>
        
        <div className="mt-4 text-xs text-gray-500">
          <div className="flex items-center justify-center space-x-4">
            <div className="flex items-center">
              <i className="fas fa-check text-green-500 mr-1"></i>
              <span>保存工作</span>
            </div>
            <div className="flex items-center">
              <i className="fas fa-check text-green-500 mr-1"></i>
              <span>跟踪状态</span>
            </div>
            <div className="flex items-center">
              <i className="fas fa-check text-green-500 mr-1"></i>
              <span>添加笔记</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GuestJobPrompt

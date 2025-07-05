import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// 检查环境变量是否存在
if (!supabaseUrl || !supabaseKey) {
  console.error('[Supabase] Missing environment variables')
  throw new Error('Missing Supabase environment variables')
}

// 创建Supabase客户端 - 使用与Django相同的简单配置
export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    // 添加更详细的调试信息
    debug: import.meta.env.VITE_NODE_ENV === 'development'
  }
})

// 开发环境日志
if (import.meta.env.VITE_NODE_ENV === 'development') {
  console.log('[Supabase] Client initialized', {
    url: supabaseUrl,
    key: supabaseKey.substring(0, 20) + '...',
  })
}

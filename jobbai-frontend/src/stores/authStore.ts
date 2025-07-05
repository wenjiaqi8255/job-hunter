import { create } from 'zustand'
import { supabase } from '../services/supabase'
import type { User, AuthState } from '../types'

// 认证状态管理接口
interface AuthStore extends AuthState {
  // 动作方法
  initialize: () => Promise<void>
  signInWithGoogle: () => Promise<boolean>
  signOut: () => Promise<void>
  setUser: (user: User | null) => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
  // 添加缓存字段
  initialized: boolean
  lastSessionCheck: number | null
}

// 创建认证状态管理
export const useAuthStore = create<AuthStore>((set, get) => ({
  // 初始状态
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  initialized: false,
  lastSessionCheck: null,

  // 初始化认证状态 - 优化：避免重复初始化
  initialize: async () => {
    try {
      console.log('[Auth] Initializing...')
      
      // 如果已经初始化且最近5分钟内检查过session，跳过
      const { initialized, lastSessionCheck } = get()
      if (initialized && lastSessionCheck && Date.now() - lastSessionCheck < 5 * 60 * 1000) {
        console.log('[Auth] Skip initialization - recently checked')
        return
      }
      
      set({ isLoading: true, error: null })

      // 获取当前会话
      const { data: { session }, error } = await supabase.auth.getSession()
      
      if (error) {
        console.error('[Auth] Session error:', error)
        set({ error: error.message, isLoading: false })
        return
      }

      if (session?.user) {
        console.log('[Auth] User found:', session.user)
        set({ 
          user: session.user as User,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          initialized: true,
          lastSessionCheck: Date.now()
        })
      } else {
        console.log('[Auth] No user session')
        set({ 
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          initialized: true,
          lastSessionCheck: Date.now()
        })
      }

      // 监听认证状态变化 - 只注册一次
      if (!initialized) {
        supabase.auth.onAuthStateChange((event, session) => {
          console.log('[Auth] State changed:', event, {
            hasSession: !!session,
            user: session?.user?.email,
            accessToken: session?.access_token ? 'present' : 'missing'
          })
          
          if (event === 'SIGNED_IN' && session?.user) {
            console.log('[Auth] User signed in successfully')
            set({ 
              user: session.user as User,
              isAuthenticated: true,
              isLoading: false,
              error: null,
              lastSessionCheck: Date.now()
            })
          } else if (event === 'SIGNED_OUT') {
            console.log('[Auth] User signed out')
            set({ 
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
              lastSessionCheck: Date.now()
            })
          } else if (event === 'TOKEN_REFRESHED' && session?.user) {
            console.log('[Auth] Token refreshed')
            set({ 
              user: session.user as User,
              isAuthenticated: true,
              isLoading: false,
              error: null,
              lastSessionCheck: Date.now()
            })
          } else if (event === 'INITIAL_SESSION') {
            console.log('[Auth] Initial session processed')
            if (session?.user) {
              set({ 
                user: session.user as User,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                lastSessionCheck: Date.now()
              })
            } else {
              set({ 
                user: null,
                isAuthenticated: false,
                isLoading: false,
                error: null,
                lastSessionCheck: Date.now()
              })
            }
          }
        })
      }

    } catch (error) {
      console.error('[Auth] Initialize error:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Authentication failed',
        isLoading: false
      })
    }
  },

  // Google登录
  signInWithGoogle: async () => {
    try {
      console.log('[Auth] Starting Google sign in...')
      set({ isLoading: true, error: null })

      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          // 使用与Django相同的重定向策略
          redirectTo: window.location.origin + '/auth/callback'
        }
      })

      if (error) {
        console.error('[Auth] Google sign in error:', error)
        set({ error: error.message, isLoading: false })
        return false
      }
      
      console.log('[Auth] Google sign in process started')
      // 成功情况下，onAuthStateChange会处理状态更新
      return true
    } catch (error) {
      console.error('[Auth] Google sign in error:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Login failed',
        isLoading: false
      })
      return false
    }
  },

  // 登出
  signOut: async () => {
    try {
      console.log('[Auth] Signing out...')
      set({ isLoading: true, error: null })

      const { error } = await supabase.auth.signOut()
      
      if (error) {
        console.error('[Auth] Sign out error:', error)
        set({ error: error.message, isLoading: false })
      } else {
        set({ 
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null
        })
      }
    } catch (error) {
      console.error('[Auth] Sign out error:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Logout failed',
        isLoading: false
      })
    }
  },

  // 设置用户
  setUser: (user: User | null) => {
    console.log('[Auth] Setting user:', user)
    set({ 
      user,
      isAuthenticated: !!user,
      isLoading: false,
      error: null
    })
  },

  // 设置错误
  setError: (error: string | null) => {
    console.log('[Auth] Setting error:', error)
    set({ error, isLoading: false })
  },

  // 设置加载状态
  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },
}))

// 开发环境日志
if (import.meta.env.VITE_NODE_ENV === 'development') {
  console.log('[Auth] Store initialized')
}

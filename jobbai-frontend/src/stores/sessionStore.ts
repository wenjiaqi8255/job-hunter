import { create } from 'zustand'
import type { MatchSession } from '../types/matching'

interface SessionState {
  // 当前会话状态（仅用于面包屑）
  currentSession: MatchSession | null
  
  // 操作方法
  setCurrentSession: (session: MatchSession | null) => void
  clearCurrentSession: () => void
}

export const useSessionStore = create<SessionState>()((set) => ({
  // 初始状态
  currentSession: null,
  
  // 设置当前会话
  setCurrentSession: (session: MatchSession | null) => {
    set({ currentSession: session })
  },
  
  // 清除当前会话
  clearCurrentSession: () => {
    set({ currentSession: null })
  },
}))

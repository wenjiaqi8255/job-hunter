import { create } from 'zustand'

interface SessionState {
  selectedSessionId: string | null
  setSelectedSessionId: (sessionId: string | null) => void
}

export const useSessionStore = create<SessionState>((set) => ({
  selectedSessionId: null,
  setSelectedSessionId: (sessionId) => set({ selectedSessionId: sessionId }),
}))

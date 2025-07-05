import { create } from 'zustand'
import { userApi } from '../services/api'

interface UserProfile {
  user_id: string
  cv_text: string
  preferences_text: string
  structured_profile?: any
  created_at: string
  updated_at: string
}

interface UserState {
  // 状态
  profile: UserProfile | null
  loading: boolean
  error: string | null
  
  // 动作
  fetchProfile: () => Promise<void>
  updateProfile: (profileData: any) => Promise<void>
  analyzeCV: (cvText: string) => Promise<void>
  clearError: () => void
}

export const useUserStore = create<UserState>()((set, get) => ({
  // 初始状态
  profile: null,
  loading: false,
  error: null,
  
  // 获取用户个人资料
  fetchProfile: async () => {
    console.log('[UserStore] Fetching user profile...')
    set({ loading: true, error: null })
    
    try {
      const response = await userApi.getProfile()
      
      if (response.success && response.data) {
        console.log('[UserStore] Profile fetched successfully')
        set({ 
          profile: response.data.profile, 
          loading: false 
        })
      } else {
        throw new Error(response.error || 'Failed to fetch profile')
      }
    } catch (error) {
      console.error('[UserStore] Error fetching profile:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 更新用户个人资料
  updateProfile: async (profileData: any) => {
    console.log('[UserStore] Updating user profile...')
    set({ loading: true, error: null })
    
    try {
      const response = await userApi.updateProfile(profileData)
      
      if (response.success && response.data) {
        console.log('[UserStore] Profile updated successfully')
        set({ 
          profile: response.data.profile, 
          loading: false 
        })
      } else {
        throw new Error(response.error || 'Failed to update profile')
      }
    } catch (error) {
      console.error('[UserStore] Error updating profile:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 分析CV
  analyzeCV: async (cvText: string) => {
    console.log('[UserStore] Analyzing CV...')
    set({ loading: true, error: null })
    
    try {
      const response = await userApi.analyzeCV(cvText)
      
      if (response.success && response.data) {
        console.log('[UserStore] CV analyzed successfully')
        // 更新profile中的structured_profile
        const currentProfile = get().profile
        if (currentProfile) {
          set({ 
            profile: {
              ...currentProfile,
              structured_profile: response.data.analysis.structured_profile
            },
            loading: false 
          })
        }
      } else {
        throw new Error(response.error || 'Failed to analyze CV')
      }
    } catch (error) {
      console.error('[UserStore] Error analyzing CV:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false 
      })
    }
  },
  
  // 清除错误
  clearError: () => {
    set({ error: null })
  }
}))

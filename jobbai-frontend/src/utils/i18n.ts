interface Language {
  code: string
  name: string
  flag: string
}

interface TranslationKey {
  [key: string]: string
}

interface Translations {
  [languageCode: string]: TranslationKey
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
]

const translations: Translations = {
  en: {
    'home_matching': 'Home & Matching',
    'my_applications': 'My Applications',
    'profile': 'Profile',
    'login': 'Login',
    'logout': 'Logout',
    'welcome_back': 'Welcome back',
    'user_id': 'User ID',
    'personal_profile': 'Personal Profile',
    'manage_info': 'Manage your personal information and preferences',
    'no_applications': 'No applications yet',
    'no_applications_desc': 'You haven\'t submitted any job applications yet. Go to the homepage to start matching jobs!',
    'start_matching': 'Start Matching Jobs',
    'footer_text': 'JobbAI MVP © 2025. Powered by React & Supabase.',
  },
  zh: {
    'home_matching': '首页与匹配',
    'my_applications': '我的申请',
    'profile': '个人资料',
    'login': '登录',
    'logout': '登出',
    'welcome_back': '欢迎回来',
    'user_id': '用户ID',
    'personal_profile': '个人资料',
    'manage_info': '管理您的个人信息和偏好设置',
    'no_applications': '暂无申请记录',
    'no_applications_desc': '您还没有提交任何职位申请。前往主页开始匹配工作！',
    'start_matching': '开始匹配工作',
    'footer_text': 'JobbAI MVP © 2025. 由 React & Supabase 驱动。',
  },
}

class I18nManager {
  private currentLanguage: string = 'zh'
  private listeners: (() => void)[] = []

  getCurrentLanguage(): string {
    return this.currentLanguage
  }

  setLanguage(languageCode: string): void {
    if (translations[languageCode]) {
      this.currentLanguage = languageCode
      this.notifyListeners()
      // 保存到localStorage
      localStorage.setItem('jobbai_language', languageCode)
    }
  }

  t(key: string): string {
    return translations[this.currentLanguage]?.[key] || key
  }

  getLanguages(): Language[] {
    return languages
  }

  addListener(listener: () => void): void {
    this.listeners.push(listener)
  }

  removeListener(listener: () => void): void {
    this.listeners = this.listeners.filter(l => l !== listener)
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener())
  }

  // 初始化语言设置
  init(): void {
    const savedLanguage = localStorage.getItem('jobbai_language')
    if (savedLanguage && translations[savedLanguage]) {
      this.currentLanguage = savedLanguage
    }
  }
}

export const i18n = new I18nManager()
export default i18n

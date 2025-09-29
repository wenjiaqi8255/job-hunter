// sidebar.ts - 侧边栏相关类型定义

export interface User {
  id: number;
  username: string;
  email?: string;
  is_authenticated: boolean;
}

export interface SessionHistory {
  id: number;
  matched_at: string;
  user_preferences_text: string;
  is_current?: boolean;
  job_count?: number;
}

export interface LanguageOption {
  code: string;
  name: string;
  is_selected: boolean;
}

export interface SidebarState {
  isCollapsed: boolean;
  activeNav: string;
  currentSessionId?: string;
  user: User | null;
  sessionHistory: SessionHistory[];
  languages: LanguageOption[];
}

export interface SidebarActions {
  toggleSidebar: () => void;
  setActiveNav: (nav: string) => void;
  setCurrentSession: (sessionId: string) => void;
  changeLanguage: (languageCode: string) => Promise<void>;
  addSessionToHistory: (sessionData: any) => void;
  logout: () => Promise<void>;
}
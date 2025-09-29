/**
 * Custom Resume相关的TypeScript类型定义
 */

export interface CustomResumeData {
  user_id: number;
  job_listing_id: string;
}

export interface CustomResume {
  id: string;
  user_id: number;
  job_listing_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface CustomResumeResponse {
  custom_resume: CustomResume;
  job_title: string;
  company_name: string;
  user_cv_text: string;
  has_existing_resume: boolean;
  generation_error: boolean;
}

// API Error types
export interface ApiError {
  detail: string;
  type?: string;
  loc?: string[];
  msg?: string;
}

// Component state types
export interface CustomResumeState {
  content: string | null;
  isLoading: boolean;
  error: string | null;
  hasExistingResume: boolean;
  jobTitle: string;
  companyName: string;
  userCvText: string;
}

// Hook return type
export interface UseCustomResumeReturn {
  state: CustomResumeState;
  generateResume: (userId: number, jobListingId: string) => Promise<void>;
  downloadPdf: (userId: number, jobListingId: string) => Promise<void>;
  copyToClipboard: () => Promise<void>;
  resetError: () => void;
}
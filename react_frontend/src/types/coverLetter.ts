/**
 * Cover Letter相关的TypeScript类型定义
 */

export interface CoverLetterData {
  saved_job_id: number;
}

export interface CoverLetter {
  id: string;
  saved_job_id: number;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterResponse {
  cover_letter: CoverLetter;
  job_title: string;
  company_name: string;
  user_cv_text: string;
  has_existing_cover_letter: boolean;
  generation_error: boolean;
}

// Component state types
export interface CoverLetterState {
  content: string | null;
  isLoading: boolean;
  error: string | null;
  hasExistingCoverLetter: boolean;
  jobTitle: string;
  companyName: string;
  userCvText: string;
}

// Hook return type
export interface UseCoverLetterReturn {
  state: CoverLetterState;
  generateCoverLetter: (savedJobId: number) => Promise<void>;
  downloadPdf: (savedJobId: number) => Promise<void>;
  copyToClipboard: () => Promise<void>;
  resetError: () => void;
}
/**
 * Custom Resume生成管理Hook
 * 对应Django的custom_resume_page.html交互逻辑
 */
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CustomResumeData, CustomResumeResponse, CustomResumeState, UseCustomResumeReturn } from '../types/customResume';
import { ApplicationsService } from '../services/api_gen/services/ApplicationsService';
import { useToast } from './useToast';

const initialState: CustomResumeState = {
  content: null,
  isLoading: false,
  error: null,
  hasExistingResume: false,
  jobTitle: '',
  companyName: '',
  userCvText: '',
};

export const useCustomResume = (initialData?: Partial<CustomResumeState>): UseCustomResumeReturn => {
  const [state, setState] = useState<CustomResumeState>({
    ...initialState,
    ...initialData,
  });

  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  // 生成定制简历
  const generateResume = useCallback(async (userId: number, jobListingId: string) => {
    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    try {
      const data: CustomResumeData = {
        user_id: userId,
        job_listing_id: jobListingId,
      };

      const response = await ApplicationsService.generateCustomResumeApiV1ApplicationsCustomResumesPost({
        requestBody: data,
      });

      const responseData: CustomResumeResponse = response as unknown as CustomResumeResponse;

      setState(prev => ({
        ...prev,
        content: responseData.custom_resume.content,
        isLoading: false,
        hasExistingResume: responseData.has_existing_resume,
        jobTitle: responseData.job_title,
        companyName: responseData.company_name,
        userCvText: responseData.user_cv_text,
        error: responseData.generation_error ? responseData.custom_resume.content : null,
      }));

      if (!responseData.generation_error) {
        showSuccess('定制简历生成成功！');
      }
    } catch (error: any) {
      console.error('Failed to generate custom resume:', error);

      let errorMessage = '生成定制简历失败，请重试';

      // 处理不同的错误类型
      if (error?.status === 400) {
        errorMessage = error.body?.detail || '用户信息不完整，请先完善个人资料';
        // 如果是CV不完整，引导用户去个人资料页面
        if (errorMessage.includes('CV') || errorMessage.includes('profile')) {
          setState(prev => ({
            ...prev,
            isLoading: false,
            error: errorMessage,
          }));
          return;
        }
      } else if (error?.status === 404) {
        errorMessage = '工作信息不存在';
      } else if (error?.status === 500) {
        errorMessage = '服务器内部错误，请稍后重试';
      }

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      showError(errorMessage);
    }
  }, [showSuccess, showError]);

  // 下载PDF
  const downloadPdf = useCallback(async (userId: number, jobListingId: string) => {
    try {
      const response = await ApplicationsService.downloadCustomResumeApiV1ApplicationsCustomResumesUserIdJobListingIdDownloadGet({
        userId: userId.toString(),
        jobListingId: jobListingId,
      });

      // 处理文件下载
      const blob = new Blob([response as unknown as BlobPart], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `custom_resume_${state.jobTitle}_${state.companyName}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      showSuccess('PDF下载成功！');
    } catch (error: any) {
      console.error('Failed to download PDF:', error);

      let errorMessage = 'PDF下载失败，请重试';
      if (error?.status === 404) {
        errorMessage = '找不到对应的定制简历';
      } else if (error?.status === 500) {
        errorMessage = 'PDF生成失败，请稍后重试';
      }

      showError(errorMessage);
    }
  }, [state.jobTitle, state.companyName, showSuccess, showError]);

  // 复制到剪贴板
  const copyToClipboard = useCallback(async () => {
    if (!state.content) return;

    try {
      await navigator.clipboard.writeText(state.content);
      showSuccess('定制简历已复制到剪贴板！');
    } catch (err) {
      console.error('Failed to copy text:', err);

      // 降级方案：使用document.execCommand
      const textArea = document.createElement('textarea');
      textArea.value = state.content;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      try {
        const successful = document.execCommand('copy');
        if (successful) {
          showSuccess('定制简历已复制到剪贴板！');
        } else {
          throw new Error('execCommand failed');
        }
      } catch (fallbackErr) {
        console.error('Fallback copy failed:', fallbackErr);
        showError('复制失败，请手动选择并复制文本');
      }

      document.body.removeChild(textArea);
    }
  }, [state.content, showSuccess, showError]);

  // 重置错误状态
  const resetError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    state,
    generateResume,
    downloadPdf,
    copyToClipboard,
    resetError,
  };
};
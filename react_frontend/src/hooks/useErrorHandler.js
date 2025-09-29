import { useCallback } from 'react';

/**
 * 统一错误处理Hook
 * 提供标准的错误处理模式和用户友好的错误消息
 */
export const useErrorHandler = () => {
  /**
   * 处理API错误
   */
  const handleApiError = useCallback((error, customMessages = {}) => {
    console.error('API Error:', error);

    // 从error对象中提取错误信息
    let errorMessage = '操作失败，请重试';
    let errorType = 'error';
    let userMessage = null;

    if (error.response) {
      // 服务器响应错误
      const status = error.response.status;
      const data = error.response.data;

      switch (status) {
        case 400:
          errorMessage = data.detail || '请求参数错误';
          errorType = 'warning';
          break;
        case 401:
          errorMessage = '请先登录';
          errorType = 'warning';
          userMessage = '登录状态已过期，请重新登录';
          break;
        case 403:
          errorMessage = '权限不足';
          errorType = 'warning';
          break;
        case 404:
          errorMessage = '请求的资源不存在';
          errorType = 'warning';
          break;
        case 422:
          errorMessage = '数据验证失败';
          if (data.detail) {
            // 处理FastAPI的验证错误
            if (Array.isArray(data.detail)) {
              errorMessage = data.detail.map(err => err.msg).join(', ');
            } else {
              errorMessage = data.detail;
            }
          }
          errorType = 'warning';
          break;
        case 429:
          errorMessage = '请求过于频繁，请稍后再试';
          errorType = 'warning';
          break;
        case 500:
          errorMessage = '服务器内部错误';
          errorType = 'error';
          break;
        case 502:
        case 503:
        case 504:
          errorMessage = '服务器暂时不可用，请稍后再试';
          errorType = 'error';
          break;
        default:
          errorMessage = data.detail || `请求失败 (${status})`;
      }
    } else if (error.request) {
      // 请求发送但没有收到响应
      errorMessage = '网络连接失败，请检查网络设置';
      errorType = 'error';
    } else {
      // 请求配置错误
      errorMessage = error.message || '请求配置错误';
      errorType = 'error';
    }

    // 使用自定义消息覆盖默认消息
    const finalMessage = customMessages[status] || customMessages[errorType] || errorMessage;

    return {
      message: finalMessage,
      type: errorType,
      userMessage: userMessage || finalMessage,
      originalError: error,
      shouldRedirect: status === 401 || status === 403,
    };
  }, []);

  /**
   * 处理网络错误
   */
  const handleNetworkError = useCallback((error) => {
    console.error('Network Error:', error);

    if (error.message === 'Network Error') {
      return {
        message: '网络连接失败，请检查网络设置',
        type: 'error',
        userMessage: '无法连接到服务器，请检查您的网络连接',
        originalError: error,
      };
    }

    return {
      message: error.message || '网络错误',
      type: 'error',
      userMessage: error.message || '网络错误',
      originalError: error,
    };
  }, []);

  /**
   * 处理验证错误
   */
  const handleValidationError = useCallback((errors) => {
    console.error('Validation Error:', errors);

    if (Array.isArray(errors)) {
      // FastAPI格式的验证错误
      const messages = errors.map(err => `${err.loc.join('.')}: ${err.msg}`);
      return {
        message: '数据验证失败',
        type: 'warning',
        userMessage: messages.join('\n'),
        details: errors,
      };
    }

    if (typeof errors === 'object') {
      // 其他格式的验证错误
      const messages = Object.entries(errors).map(([field, message]) => `${field}: ${message}`);
      return {
        message: '数据验证失败',
        type: 'warning',
        userMessage: messages.join('\n'),
        details: errors,
      };
    }

    return {
      message: '数据验证失败',
      type: 'warning',
      userMessage: '请检查输入的数据',
      details: errors,
    };
  }, []);

  /**
   * 处理文件上传错误
   */
  const handleFileUploadError = useCallback((error) => {
    console.error('File Upload Error:', error);

    if (error.response?.status === 413) {
      return {
        message: '文件太大，请选择较小的文件',
        type: 'warning',
        userMessage: '文件大小超过限制，请选择小于10MB的文件',
      };
    }

    if (error.message?.includes('Unsupported file type')) {
      return {
        message: '不支持的文件类型',
        type: 'warning',
        userMessage: '请选择PDF、DOC或DOCX格式的文件',
      };
    }

    return handleApiError(error);
  }, [handleApiError]);

  /**
   * 处理AI服务错误
   */
  const handleAIServiceError = useCallback((error) => {
    console.error('AI Service Error:', error);

    if (error.response?.status === 429) {
      return {
        message: 'AI服务暂时不可用，请稍后再试',
        type: 'warning',
        userMessage: 'AI服务正在处理大量请求，请稍后再试',
      };
    }

    if (error.message?.includes('timeout')) {
      return {
        message: 'AI处理超时',
        type: 'warning',
        userMessage: 'AI处理时间较长，请稍后再试或简化您的需求',
      };
    }

    return {
      message: 'AI服务暂时不可用',
      type: 'error',
      userMessage: 'AI服务暂时不可用，请稍后再试',
      originalError: error,
    };
  }, []);

  return {
    handleApiError,
    handleNetworkError,
    handleValidationError,
    handleFileUploadError,
    handleAIServiceError,
  };
};
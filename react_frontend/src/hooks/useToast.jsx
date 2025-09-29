import { useState, useCallback } from 'react';

/**
 * 全局Toast消息管理Hook
 * 对应Django的messages框架
 *
 * 功能：
 * 1. 显示成功、错误、警告、信息消息
 * 2. 自动消失（3.5秒）
 * 3. 支持手动关闭
 * 4. 消息队列管理
 */
export const useToast = () => {
  const [toasts, setToasts] = useState([]);

  /**
   * 移除Toast消息
   */
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  /**
   * 添加新的Toast消息
   */
  const addToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random();
    const newToast = {
      id,
      message,
      type,
      duration,
    };

    setToasts(prev => [...prev, newToast]);

    // 自动移除
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, [removeToast]);

  /**
   * 显示成功消息
   */
  const showSuccess = useCallback((message, duration) => {
    return addToast(message, 'success', duration);
  }, [addToast]);

  /**
   * 显示错误消息
   */
  const showError = useCallback((message, duration) => {
    return addToast(message, 'error', duration);
  }, [addToast]);

  /**
   * 显示警告消息
   */
  const showWarning = useCallback((message, duration) => {
    return addToast(message, 'warning', duration);
  }, [addToast]);

  /**
   * 显示信息消息
   */
  const showInfo = useCallback((message, duration) => {
    return addToast(message, 'info', duration);
  }, [addToast]);

  /**
   * 清空所有消息
   */
  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    addToast,
    removeToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    clearAll,
  };
};
import { useState, useCallback, useEffect } from 'react';

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
  }, []);

  /**
   * 移除Toast消息
   */
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

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

/**
 * Toast容器组件
 */
export const ToastContainer = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="position-fixed top-0 start-50 translate-middle-x mt-3" style={{
      zIndex: 1080,
      minWidth: '350px',
      maxWidth: '90vw'
    }}>
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={() => onRemove(toast.id)}
        />
      ))}
    </div>
  );
};

/**
 * 单个Toast组件
 */
const ToastItem = ({ toast, onRemove }) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onRemove();
    }, 300); // 等待淡出动画
  };

  const getToastClass = (type) => {
    switch (type) {
      case 'success':
        return 'alert-success';
      case 'error':
        return 'alert-danger';
      case 'warning':
        return 'alert-warning';
      case 'info':
      default:
        return 'alert-info';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return 'fas fa-check-circle';
      case 'error':
        return 'fas fa-exclamation-circle';
      case 'warning':
        return 'fas fa-exclamation-triangle';
      case 'info':
      default:
        return 'fas fa-info-circle';
    }
  };

  return (
    <div
      className={`alert ${getToastClass(toast.type)} alert-dismissible fade show shadow mb-2 ${
        isVisible ? '' : 'fade-out'
      }`}
      role="alert"
      style={{
        transition: 'opacity 0.3s ease-in-out',
        opacity: isVisible ? 1 : 0,
      }}
    >
      <div className="d-flex align-items-center">
        <i className={`${getIcon(toast.type)} me-2`}></i>
        <span>{toast.message}</span>
      </div>
      <button
        type="button"
        className="btn-close"
        onClick={handleClose}
        aria-label="Close"
      ></button>
    </div>
  );
};
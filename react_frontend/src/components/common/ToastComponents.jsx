// ToastComponents.jsx - Toast相关组件
import React, { useState } from 'react';

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
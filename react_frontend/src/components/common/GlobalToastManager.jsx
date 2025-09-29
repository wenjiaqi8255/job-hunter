// GlobalToastManager.jsx - 全局Toast管理器
import React from 'react';
import { useToast } from '../../hooks/useToast';
import { ToastContainer } from './ToastComponents';

const GlobalToastManager = () => {
  const { toasts, removeToast } = useToast();

  return <ToastContainer toasts={toasts} onRemove={removeToast} />;
};

export default GlobalToastManager;
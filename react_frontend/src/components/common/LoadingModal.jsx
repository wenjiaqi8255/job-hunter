// LoadingModal.jsx
// 对应Django main_page.html中的全局Loading弹窗静态部分

import React from 'react';

const LoadingModal = ({ show, text }) => {
  if (!show) return null;
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md text-center">
        <div className="mb-4">
          <div className="animate-spin inline-block mr-2 text-blue-600">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.2"/><path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="4"/></svg>
          </div>
          <h5 className="font-bold text-lg">Matching in progress, please wait...</h5>
          <div className="mt-2 text-gray-500 text-sm">{text || ''}</div>
        </div>
      </div>
    </div>
  );
};

export default LoadingModal;

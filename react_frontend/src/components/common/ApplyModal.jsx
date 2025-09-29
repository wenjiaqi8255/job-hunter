// ApplyModal.jsx
// 对应Django main_page.html中的Apply Confirmation弹窗静态部分

import React from 'react';

const ApplyModal = ({ show, onClose }) => {
  if (!show) return null;
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h5 className="font-bold text-lg">Confirm Application</h5>
          <button onClick={onClose} className="btn btn-sm">×</button>
        </div>
        <div className="mb-4">
          The application page for <strong>this job</strong> has opened in a new tab.<br /><br />Have you submitted your application?
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">Not Yet</button>
          <button className="btn btn-success">Yes, I Applied</button>
        </div>
      </div>
    </div>
  );
};

export default ApplyModal;

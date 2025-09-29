// ApplyConfirmationModal.jsx - 申请确认模态框
import React, { useState, useEffect, useCallback } from 'react';
import { useToast } from '../../hooks/useToast';
import { useApi } from '../../hooks/useApi';
import { useSessionStorage } from '../../hooks/useSessionStorage';

const ApplyConfirmationModal = () => {
  const [showModal, setShowModal] = useState(false);
  const [jobTitle, setJobTitle] = useState('');
  const [jobId, setJobId] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const { showSuccess, showError } = useToast();
  const { updateJobApplicationStatus } = useApi();
  const { getItem, removeItem } = useSessionStorage();

  // 检查是否有待处理的申请
  const checkPendingApplication = useCallback(() => {
    const pendingJobId = getItem('pendingApplicationJobId');
    const pendingJobTitle = getItem('pendingApplicationJobTitle');

    if (pendingJobId && pendingJobTitle) {
      setJobId(pendingJobId);
      setJobTitle(pendingJobTitle);
      setShowModal(true);

      // 清除session storage
      removeItem('pendingApplicationJobId');
      removeItem('pendingApplicationJobTitle');
    }
  }, [getItem, removeItem]);

  // 监听窗口焦点变化
  useEffect(() => {
    const handleFocus = () => {
      checkPendingApplication();
    };

    window.addEventListener('focus', handleFocus);
    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [checkPendingApplication]);

  // 页面加载时检查
  useEffect(() => {
    checkPendingApplication();
  }, [checkPendingApplication]);

  // 确认已申请
  const handleConfirmApplied = async () => {
    if (!jobId) return;

    setIsProcessing(true);
    try {
      const result = await updateJobApplicationStatus(jobId, 'applied');
      if (result.success) {
        showSuccess('Application status updated successfully');
        setShowModal(false);

        // 触发自定义事件更新UI
        window.dispatchEvent(new CustomEvent('jobStatusUpdated', {
          detail: { jobId, status: 'applied' }
        }));
      } else {
        showError(result.error || 'Failed to update application status');
      }
    } catch (error) {
      console.error('Error updating application status:', error);
      showError('An error occurred while updating the application status');
    } finally {
      setIsProcessing(false);
    }
  };

  // 关闭模态框
  const handleClose = () => {
    setShowModal(false);
    setJobTitle('');
    setJobId('');
  };

  if (!showModal) return null;

  return (
    <div
      className="modal fade show"
      id="applyConfirmationModal"
      tabIndex="-1"
      aria-labelledby="applyConfirmationModalLabel"
      aria-hidden="false"
      style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="applyConfirmationModalLabel">
              Confirm Application
            </h5>
            <button
              type="button"
              className="btn-close"
              onClick={handleClose}
              disabled={isProcessing}
            ></button>
          </div>
          <div className="modal-body">
            The application page for <strong id="modalJobTitle">{jobTitle || 'this job'}</strong> has opened in a new tab.
            <br /><br />
            Have you submitted your application?
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClose}
              disabled={isProcessing}
            >
              Not Yet
            </button>
            <button
              type="button"
              className="btn btn-success"
              onClick={handleConfirmApplied}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                  Processing...
                </>
              ) : (
                'Yes, I Applied'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApplyConfirmationModal;
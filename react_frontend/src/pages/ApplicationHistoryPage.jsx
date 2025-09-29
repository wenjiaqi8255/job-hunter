// ApplicationHistoryPage.jsx
// 展示用户申请历史，对应Django的my_applications.html
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApplications } from '../hooks/useApplications';
import { useToast } from '../hooks/useToast';

const ApplicationHistoryPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [statusFilter, setStatusFilter] = useState(null);
  const [generatingLetter, setGeneratingLetter] = useState({});
  const [updatingStatus, setUpdatingStatus] = useState({});

  const {
    applications,
    loading,
    error,
    statusCounts,
    statusChoices,
    currentFilter,
    isEmpty,
    updateApplicationStatus,
    generateCoverLetter
  } = useApplications({ statusFilter, autoFetch: true });

  // 处理状态变更
  const handleStatusChange = async (jobId, newStatus) => {
    setUpdatingStatus(prev => ({ ...prev, [jobId]: true }));
    try {
      await updateApplicationStatus(jobId, newStatus);
      showSuccess('状态更新成功');
    } catch (err) {
      showError('状态更新失败');
    } finally {
      setUpdatingStatus(prev => ({ ...prev, [jobId]: false }));
    }
  };

  // 生成求职信
  const handleGenerateCoverLetter = async (jobId) => {
    setGeneratingLetter(prev => ({ ...prev, [jobId]: true }));
    try {
      await generateCoverLetter(jobId);
      showSuccess('求职信生成成功');
      // 刷新列表
      setTimeout(() => window.location.reload(), 1000);
    } catch (err) {
      showError('求职信生成失败');
    } finally {
      setGeneratingLetter(prev => ({ ...prev, [jobId]: false }));
    }
  };

  // 查看工作详情
  const handleViewJob = (jobId) => {
    navigate(`/jobs/${jobId}`);
  };

  // 获取状态标签样式
  const getStatusBadgeClass = (status) => {
    const statusMap = {
      'not_applied': 'bg-secondary',
      'applied': 'bg-primary',
      'interviewing': 'bg-warning text-dark',
      'offered': 'bg-success',
      'rejected': 'bg-danger'
    };
    return `badge ${statusMap[status] || 'bg-secondary'}`;
  };

  // 获取状态显示文本
  const getStatusDisplay = (status) => {
    const choice = statusChoices.find(c => c.value === status);
    return choice ? choice.label : status;
  };

  return (
    <div className="container-fluid py-4">
      {/* 页面头部 */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h1">Applications</h1>
      </div>

      {/* 状态筛选标签 */}
      <ul className="nav nav-tabs mb-4">
        {statusChoices.map(({ value, label }) => (
          <li className="nav-item" key={value}>
            <button
              className={`nav-link ${currentFilter === value ? 'active' : ''}`}
              onClick={() => setStatusFilter(currentFilter === value ? null : value)}
            >
              {label}{' '}
              <span className="badge rounded-pill bg-secondary text-white">
                {statusCounts[value] || 0}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {/* 错误信息 */}
      {error && (
        <div className="alert alert-danger" role="alert">
          <i className="fas fa-exclamation-circle me-2"></i>
          {error}
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      )}

      {/* 申请列表 */}
      {!loading && !isEmpty && (
        <div className="row row-cols-1 row-cols-md-2 g-4">
          {applications.map((application) => (
            <div className="col" key={application.id}>
              <div className="card h-100 jobbAI-job-card">
                <div className="card-body">
                  <h5 className="card-title">
                    <button
                      className="btn btn-link p-0 text-decoration-none"
                      onClick={() => handleViewJob(application.job_listing?.id)}
                    >
                      {application.job_listing?.job_title}
                    </button>
                  </h5>
                  <h6 className="card-subtitle mb-2 text-muted">
                    {application.job_listing?.company_name}
                  </h6>

                  <p className="card-text">
                    <strong>Status:</strong>{' '}
                    <span className={getStatusBadgeClass(application.status)}>
                      {getStatusDisplay(application.status)}
                    </span>
                  </p>

                  {application.job_listing?.level && (
                    <p className="card-text">
                      <small className="text-muted">
                        Level: {application.job_listing.level}
                      </small>
                    </p>
                  )}

                  <p className="card-text">
                    <small className="text-muted">
                      Location: {application.job_listing?.location || 'N/A'}
                    </small>
                  </p>

                  <p className="card-text">
                    <small className="text-muted">
                      Last updated: {new Date(application.updated_at).toLocaleDateString()}
                    </small>
                  </p>

                  {application.notes && (
                    <p className="mt-2 mb-1">
                      <small>
                        <strong>Notes:</strong>{' '}
                        {application.notes.length > 100
                          ? `${application.notes.substring(0, 100)}...`
                          : application.notes}
                      </small>
                    </p>
                  )}
                </div>

                <div className="card-footer">
                  <button
                    onClick={() => handleViewJob(application.job_listing?.id)}
                    className="btn btn-outline-primary btn-sm me-2"
                  >
                    <i className="fas fa-eye me-1"></i>
                    View Details
                  </button>

                  {application.cover_letter ? (
                    <button
                      onClick={() => navigate(`/cover-letter/${application.id}`)}
                      className="btn btn-outline-primary btn-sm ms-2"
                    >
                      <i className="fas fa-file-alt me-1"></i>
                      View Cover Letter
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate(`/cover-letter/${application.id}`)}
                      className="btn btn-success btn-sm ms-2"
                    >
                      <i className="fas fa-envelope me-1"></i>
                      Generate Cover Letter
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 无申请记录 */}
      {!loading && isEmpty && (
        <div className="alert alert-info mt-4" role="alert">
          {currentFilter ? (
            <>
              No jobs with status "{getStatusDisplay(currentFilter)}" yet.
              <button
                className="btn btn-link p-0 ms-1"
                onClick={() => setStatusFilter(null)}
              >
                View all applications
              </button>
            </>
          ) : (
            <>
              You haven't saved any job applications yet.
              Start by finding jobs on the{' '}
              <button
                className="btn btn-link p-0"
                onClick={() => navigate('/')}
              >
                main page
              </button>{' '}
              and saving their status on the job detail page.
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ApplicationHistoryPage;

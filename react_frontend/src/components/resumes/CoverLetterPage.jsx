/**
 * Cover Letter页面组件
 * 对应Django的cover_letter_page.html
 * 实现求职信生成功能
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCoverLetter } from '../../hooks/useCoverLetter';
import { useAuth } from '../../contexts/AuthContext';
import LoadingModal from '../common/LoadingModal';

const CoverLetterPage = () => {
  const { savedJobId } = useParams();
  const navigate = useNavigate();
  const { user, token } = useAuth();

  // 获取保存的工作信息
  const [savedJobInfo, setSavedJobInfo] = useState({
    job_title: '',
    company_name: '',
  });

  const {
    state,
    generateCoverLetter,
    downloadPdf,
    copyToClipboard,
    resetError,
  } = useCoverLetter({
    jobTitle: savedJobInfo.job_title,
    companyName: savedJobInfo.company_name,
  });

  useEffect(() => {
    // 如果用户未登录，重定向到登录页面
    if (!token) {
      navigate('/login');
      return;
    }

    // 如果没有savedJobId，重定向到申请列表
    if (!savedJobId) {
      navigate('/applications');
      return;
    }

    // 获取保存的工作信息
    const fetchSavedJobInfo = async () => {
      try {
        // TODO: 调用API获取保存的工作详情
        // 这里应该从applications列表中获取对应的工作信息
        // const savedJob = await ApplicationsService.getSavedJob({ savedJobId: parseInt(savedJobId) });
        // setSavedJobInfo({
        //   job_title: savedJob.job_listing.job_title,
        //   company_name: savedJob.job_listing.company_name,
        // });
      } catch (error) {
        console.error('Failed to fetch saved job info:', error);
        navigate('/applications');
      }
    };

    fetchSavedJobInfo();
  }, [savedJobId, token, navigate]);

  // 生成求职信处理函数
  const handleGenerateCoverLetter = async (e) => {
    e.preventDefault();
    if (!savedJobId) return;

    try {
      await generateCoverLetter(parseInt(savedJobId));
    } catch (error) {
      console.error('Generate cover letter failed:', error);
    }
  };

  // 处理CV不完整的错误，引导用户去个人资料页面
  const handleGoToProfile = () => {
    navigate('/profile');
  };

  return (
    <div className="container py-4">
      {/* 面包屑导航 */}
      <nav aria-label="breadcrumb">
        <ol className="breadcrumb">
          <li className="breadcrumb-item">
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }}>
              Home
            </a>
          </li>
          <li className="breadcrumb-item">
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                navigate('/applications');
              }}
            >
              Applications
            </a>
          </li>
          <li className="breadcrumb-item">
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                // TODO: 跳转到对应的工作详情页面
                // navigate(`/jobs/${savedJobInfo.job_listing_id}`);
              }}
            >
              Job Detail: {savedJobInfo.job_title || 'Loading...'}
            </a>
          </li>
          <li className="breadcrumb-item active" aria-current="page">
            Generated Cover Letter
          </li>
        </ol>
      </nav>

      {/* 页面标题 */}
      <div className="mb-4">
        <h2 className="h2">
          Cover Letter for: {savedJobInfo.job_title || 'Loading...'} at {savedJobInfo.company_name || 'Loading...'}
        </h2>
        {state.userCvText && (
          <p className="text-muted">
            Based on your CV: "{state.userCvText.length > 100
              ? `${state.userCvText.substring(0, 100)}...`
              : state.userCvText}"
          </p>
        )}
      </div>

      {/* 错误提示 */}
      {state.error && (
        <div className="alert alert-warning mb-4">
          <div className="d-flex align-items-center">
            <i className="fas fa-exclamation-triangle me-2"></i>
            <div className="flex-grow-1">
              {state.error}
            </div>
            {state.error.includes('CV') || state.error.includes('profile') ? (
              <button
                onClick={handleGoToProfile}
                className="btn btn-sm btn-primary"
              >
                <i className="fas fa-edit me-1"></i>
                Go to Profile to Edit CV
              </button>
            ) : (
              <button
                onClick={resetError}
                className="btn btn-sm btn-outline-secondary"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
        </div>
      )}

      {/* 求职信内容区域 */}
      <div className="card mb-4">
        <div className="card-body">
          {state.content ? (
            <textarea
              id="coverLetterContent"
              className="form-control"
              rows={15}
              value={state.content}
              readOnly
              style={{ fontFamily: 'inherit', fontSize: 'inherit' }}
            />
          ) : (
            <div className="text-center py-8 text-muted">
              <i className="fas fa-envelope fa-3x mb-3"></i>
              <p>Click "Generate" to create your cover letter</p>
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮区域 */}
      <div className="card-footer bg-transparent border-top-0">
        {state.content && (
          <>
            <button
              onClick={copyToClipboard}
              className="btn btn-secondary"
              disabled={state.isLoading}
            >
              <i className="fas fa-copy me-1"></i>
              Copy Full Text
            </button>
            <button
              onClick={() => downloadPdf(parseInt(savedJobId))}
              className="btn btn-primary ms-2"
              disabled={state.isLoading}
            >
              <i className="fas fa-file-pdf me-1"></i>
              Download PDF
            </button>
          </>
        )}

        {/* 重新生成按钮（仅在已有求职信时显示） */}
        {state.hasExistingCoverLetter && state.content && (
          <form onSubmit={handleGenerateCoverLetter} className="d-inline ms-2">
            <button
              type="submit"
              className="btn btn-outline-primary"
              disabled={state.isLoading}
            >
              {state.isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                  Generating...
                </>
              ) : (
                <>
                  <i className="fas fa-sync-alt me-1"></i>
                  Regenerate
                </>
              )}
            </button>
          </form>
        )}
      </div>

      {/* Loading Modal */}
      <LoadingModal
        show={state.isLoading}
        type="cover-letter"
        title="Generating your cover letter, please wait..."
        subtitle="Crafting a compelling introduction for your application..."
      />
    </div>
  );
};

export default CoverLetterPage;
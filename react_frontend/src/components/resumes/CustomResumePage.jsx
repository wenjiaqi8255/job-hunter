/**
 * Custom Resume页面组件
 * 对应Django的custom_resume_page.html
 * 实现定制简历生成功能
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCustomResume } from '../../hooks/useCustomResume';
import { useAuth } from '../../contexts/AuthContext';
import LoadingModal from '../common/LoadingModal';
import { formatResumeText } from '../../utils/formatters';

const CustomResumePage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { user, token } = useAuth();

  // 获取job信息（这里应该从job详情或上下文获取）
  const [jobInfo, setJobInfo] = useState({
    job_title: '',
    company_name: '',
  });

  const {
    state,
    generateResume,
    downloadPdf,
    copyToClipboard,
    resetError,
  } = useCustomResume({
    jobTitle: jobInfo.job_title,
    companyName: jobInfo.company_name,
  });

  useEffect(() => {
    // 如果用户未登录，重定向到登录页面
    if (!token) {
      navigate('/login');
      return;
    }

    // 如果没有jobId，重定向到工作列表
    if (!jobId) {
      navigate('/jobs');
      return;
    }

    // 模拟获取job信息（实际应该从API获取）
    // 这里可以调用getJobDetail API
    const fetchJobInfo = async () => {
      try {
        // TODO: 调用API获取工作详情
        // const jobDetail = await JobsService.getJobDetail({ jobId });
        // setJobInfo({
        //   job_title: jobDetail.job_title,
        //   company_name: jobDetail.company_name,
        // });
      } catch (error) {
        console.error('Failed to fetch job info:', error);
        navigate('/jobs');
      }
    };

    fetchJobInfo();
  }, [jobId, token, navigate]);

  // 生成简历处理函数
  const handleGenerateResume = async (e) => {
    e.preventDefault();
    if (!user?.id) return;

    try {
      await generateResume(user.id, jobId);
    } catch (error) {
      console.error('Generate resume failed:', error);
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
                navigate(`/jobs/${jobId}`);
              }}
            >
              Job Detail: {jobInfo.job_title || 'Loading...'}
            </a>
          </li>
          <li className="breadcrumb-item active" aria-current="page">
            Customize CV
          </li>
        </ol>
      </nav>

      {/* 页面标题 */}
      <div className="mb-4">
        <h2 className="h2">
          Customize CV for: {jobInfo.job_title || 'Loading...'} at {jobInfo.company_name || 'Loading...'}
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

      {/* 简历预览区域 */}
      <div className="card mb-4">
        <div className="card-body">
          {state.content ? (
            <div
              id="customResumePreview"
              className="resume-preview p-4 border rounded bg-white"
              dangerouslySetInnerHTML={{
                __html: formatResumeText(state.content)
              }}
            />
          ) : (
            <div className="text-center py-8 text-muted">
              <i className="fas fa-file-alt fa-3x mb-3"></i>
              <p>Click "Generate" to create your custom resume</p>
            </div>
          )}

          {/* 隐藏的文本区域用于复制功能 */}
          <textarea
            id="customResumeContent"
            className="d-none"
            readOnly
            value={state.content || ''}
          />
        </div>
      </div>

      {/* 操作按钮区域 */}
      <div className="card-footer bg-transparent border-top-0">
        <form onSubmit={handleGenerateResume} className="d-inline">
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
                {state.hasExistingResume ? 'Regenerate' : 'Generate'}
              </>
            )}
          </button>
        </form>

        {state.content && (
          <>
            <button
              onClick={copyToClipboard}
              className="btn btn-secondary ms-2"
              disabled={state.isLoading}
            >
              <i className="fas fa-copy me-1"></i>
              Copy Full Text
            </button>
            <button
              onClick={() => downloadPdf(user?.id, jobId)}
              className="btn btn-primary ms-2"
              disabled={state.isLoading}
            >
              <i className="fas fa-file-pdf me-1"></i>
              Download PDF
            </button>
          </>
        )}
      </div>

      {/* Loading Modal */}
      <LoadingModal
        show={state.isLoading}
        type="resume"
        title="Generating your custom resume, please wait..."
        subtitle="Optimizing your CV for the target position..."
      />
    </div>
  );
};

export default CustomResumePage;
// ProfilePage.jsx
// 用户配置文件页面，对应Django的profile_page.html
import React, { useState } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { useProfile } from '../hooks/useProfile';
import { useApplications } from '../hooks/useApplications';
import { useToast } from '../hooks/useToast';

const ProfilePage = () => {
  const { showSuccess, showError } = useToast();

  const [activeForm, setActiveForm] = useState(null);
  const [cvFile, setCvFile] = useState(null);

  const {
    profile,
    loading,
    error,
    saving,
    uploading,
    fetchProfile,
    updateProfile,
    uploadCvFile,
    updateCvText,
    updatePreferences,
    updateEmail
  } = useProfile({ autoFetch: true });

  const { statusCounts } = useApplications({ autoFetch: false });

  // 处理表单提交
  const handleCvFormSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateCvText(profile.user_cv_text);
      showSuccess('CV信息已更新');
      setActiveForm(null);
    } catch (err) {
      showError('CV信息更新失败');
    }
  };

  const handlePreferencesFormSubmit = async (e) => {
    e.preventDefault();
    try {
      await updatePreferences(profile.user_preferences_text);
      showSuccess('偏好设置已更新');
      setActiveForm(null);
    } catch (err) {
      showError('偏好设置更新失败');
    }
  };

  const handleEmailFormSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateEmail(profile.user_email);
      showSuccess('邮箱已更新');
      setActiveForm(null);
    } catch (err) {
      showError('邮箱更新失败');
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!cvFile) return;

    try {
      await uploadCvFile(cvFile);
      showSuccess('简历上传成功');
      setCvFile(null);
    } catch (err) {
      showError('简历上传失败');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
  };

  // 计算统计数据
  const applicationCount = Object.values(statusCounts).reduce((sum, count) => sum + count, 0);
  const alreadySavedMinutes = applicationCount * 20;

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* 页面头部 */}
      <div className="row mb-8">
        <div className="col-md-8">
          <h1 className="h3 mb-2">个人档案</h1>
          <p className="text-muted">管理您的个人信息、简历和求职偏好</p>
        </div>
        <div className="col-md-4 text-end">
          <div className="d-flex align-items-center justify-content-end">
            <div className="me-3">
              <small className="text-muted">已保存职位</small>
              <div className="fw-bold">{applicationCount}</div>
            </div>
            <div>
              <small className="text-muted">节省时间</small>
              <div className="fw-bold">{alreadySavedMinutes} 分钟</div>
            </div>
          </div>
        </div>
      </div>

      {/* 错误信息 */}
      {error && (
        <div className="alert alert-danger" role="alert">
          <i className="fas fa-exclamation-circle me-2"></i>
          {error}
        </div>
      )}

      <div className="row">
        {/* 左侧：档案信息 */}
        <div className="col-lg-8">
          {/* CV信息卡片 */}
          <div className="card mb-4">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <i className="fas fa-file-alt me-2"></i>
                简历信息
              </h5>
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => setActiveForm(activeForm === 'cv' ? null : 'cv')}
              >
                {activeForm === 'cv' ? '取消' : '编辑'}
              </button>
            </div>
            <div className="card-body">
              {activeForm === 'cv' ? (
                <form onSubmit={handleCvFormSubmit}>
                  <div className="mb-3">
                    <label className="form-label">简历内容</label>
                    <textarea
                      name="user_cv_text"
                      value={profile.user_cv_text || ''}
                      onChange={handleInputChange}
                      className="form-control"
                      rows={6}
                      placeholder="请输入您的简历内容，包括技能、经验、教育背景等..."
                    />
                  </div>
                  <div className="d-flex gap-2">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? '保存中...' : '保存'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setActiveForm(null)}
                    >
                      取消
                    </button>
                  </div>
                </form>
              ) : (
                <div>
                  <p className="text-muted mb-3">
                    您的简历内容将被用于AI匹配和求职信生成
                  </p>
                  {profile.user_cv_text ? (
                    <div className="bg-light p-3 rounded">
                      <pre className="mb-0" style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                        {profile.user_cv_text.length > 500
                          ? `${profile.user_cv_text.substring(0, 500)}...`
                          : profile.user_cv_text}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center text-muted py-4">
                      <i className="fas fa-file-alt fa-2x mb-2"></i>
                      <p>尚未添加简历内容</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 求职偏好卡片 */}
          <div className="card mb-4">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <i className="fas fa-cog me-2"></i>
                求职偏好
              </h5>
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => setActiveForm(activeForm === 'preferences' ? null : 'preferences')}
              >
                {activeForm === 'preferences' ? '取消' : '编辑'}
              </button>
            </div>
            <div className="card-body">
              {activeForm === 'preferences' ? (
                <form onSubmit={handlePreferencesFormSubmit}>
                  <div className="mb-3">
                    <label className="form-label">偏好设置</label>
                    <textarea
                      name="user_preferences_text"
                      value={profile.user_preferences_text || ''}
                      onChange={handleInputChange}
                      className="form-control"
                      rows={4}
                      placeholder="请输入您的求职偏好，如期望的工作地点、职位类型、薪资范围等..."
                    />
                  </div>
                  <div className="d-flex gap-2">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? '保存中...' : '保存'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setActiveForm(null)}
                    >
                      取消
                    </button>
                  </div>
                </form>
              ) : (
                <div>
                  <p className="text-muted mb-3">
                    我们将根据您的偏好为您推荐最合适的工作机会
                  </p>
                  {profile.user_preferences_text ? (
                    <div className="bg-light p-3 rounded">
                      <p className="mb-0">
                        {profile.user_preferences_text}
                      </p>
                    </div>
                  ) : (
                    <div className="text-center text-muted py-4">
                      <i className="fas fa-cog fa-2x mb-2"></i>
                      <p>尚未设置求职偏好</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 邮箱设置卡片 */}
          <div className="card mb-4">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <i className="fas fa-envelope me-2"></i>
                邮箱设置
              </h5>
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => setActiveForm(activeForm === 'email' ? null : 'email')}
              >
                {activeForm === 'email' ? '取消' : '编辑'}
              </button>
            </div>
            <div className="card-body">
              {activeForm === 'email' ? (
                <form onSubmit={handleEmailFormSubmit}>
                  <div className="mb-3">
                    <label className="form-label">邮箱地址</label>
                    <input
                      type="email"
                      name="user_email"
                      value={profile.user_email || ''}
                      onChange={handleInputChange}
                      className="form-control"
                      placeholder="请输入您的邮箱地址"
                    />
                  </div>
                  <div className="d-flex gap-2">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? '保存中...' : '保存'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setActiveForm(null)}
                    >
                      取消
                    </button>
                  </div>
                </form>
              ) : (
                <div>
                  <p className="text-muted mb-3">
                    用于接收申请通知和重要更新
                  </p>
                  <div className="bg-light p-3 rounded">
                    <p className="mb-0">
                      <i className="fas fa-envelope me-2"></i>
                      {profile.user_email || '尚未设置邮箱'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 文件上传卡片 */}
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="fas fa-upload me-2"></i>
                简历文件上传
              </h5>
            </div>
            <div className="card-body">
              <form onSubmit={handleFileUpload}>
                <div className="mb-3">
                  <label className="form-label">选择简历文件</label>
                  <input
                    type="file"
                    className="form-control"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setCvFile(e.target.files[0])}
                  />
                  <div className="form-text">
                    支持 PDF、DOC、DOCX 格式，系统将自动提取文本内容
                  </div>
                </div>
                <button
                  type="submit"
                  className="btn btn-success"
                  disabled={!cvFile || uploading}
                >
                  {uploading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      上传中...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-upload me-2"></i>
                      上传简历
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* 右侧：统计信息 */}
        <div className="col-lg-4">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">账户统计</h5>
            </div>
            <div className="card-body">
              <div className="text-center mb-4">
                <div className="display-4 text-primary">{applicationCount}</div>
                <div className="text-muted">已保存职位</div>
              </div>
              <div className="text-center">
                <div className="display-6 text-success">{alreadySavedMinutes}</div>
                <div className="text-muted">节省时间（分钟）</div>
              </div>
            </div>
          </div>

          <div className="card mt-4">
            <div className="card-header">
              <h5 className="mb-0">快速操作</h5>
            </div>
            <div className="card-body">
              <div className="d-grid gap-2">
                <a href="/applications" className="btn btn-outline-primary">
                  <i className="fas fa-briefcase me-2"></i>
                  查看申请历史
                </a>
                <a href="/sessions" className="btn btn-outline-secondary">
                  <i className="fas fa-history me-2"></i>
                  匹配历史
                </a>
                <a href="/" className="btn btn-outline-info">
                  <i className="fas fa-home me-2"></i>
                  返回首页
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;

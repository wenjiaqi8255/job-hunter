// ProfilePage.jsx
// 用户配置文件页面，展示和编辑用户信息，支持简历上传

import React, { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';
// import { AuthContext } from '../contexts/MockAuthContext';

const ProfilePage = () => {
  const contextValue = useContext(AuthContext) || {};
  const { user, token } = contextValue;
  const [profile, setProfile] = useState({ user_cv_text: '', user_preferences_text: '', user_email: '' });
  const [cvFile, setCvFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (token && user?.id) {
      fetchProfile();
    }
  }, [token, user]);

  const fetchProfile = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const res = await DefaultService.getUserProfileApiV1UserIdGet(user.id);
      setProfile(res);
    } catch {
      setMessage('获取用户信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = e => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handleSave = async e => {
    e.preventDefault();
    if (!user?.id) return;
    setLoading(true);
    setMessage('');
    try {
      await DefaultService.updateUserProfileApiV1UserIdPut(user.id, profile);
      setMessage('保存成功');
    } catch {
      setMessage('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async e => {
    e.preventDefault();
    if (!cvFile || !user?.id) return;
    setLoading(true);
    setMessage('');
    try {
      await DefaultService.uploadCvFileApiV1UserIdUploadCvPost(user.id, { cv_file: cvFile });
      setMessage('简历上传成功');
      fetchProfile();
    } catch {
      setMessage('简历上传失败');
    } finally {
      setLoading(false);
    }
  };

  if (!token) return <div className="p-8 text-center">请先登录</div>;

  return (
    <div className="max-w-xl mx-auto mt-12 p-8 bg-white rounded-xl shadow">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">个人信息</h2>
      <form onSubmit={handleSave} className="flex flex-col gap-4 mb-6">
        <label className="font-semibold">邮箱</label>
        <input name="user_email" value={profile.user_email || ''} onChange={handleChange} className="border rounded p-2" disabled />
        <label className="font-semibold">简历内容</label>
        <textarea name="user_cv_text" value={profile.user_cv_text || ''} onChange={handleChange} rows={4} className="border rounded p-2" />
        <label className="font-semibold">求职偏好</label>
        <textarea name="user_preferences_text" value={profile.user_preferences_text || ''} onChange={handleChange} rows={3} className="border rounded p-2" />
        <button type="submit" className="bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition" disabled={loading}>
          {loading ? '保存中...' : '保存'}
        </button>
      </form>
      <form onSubmit={handleUpload} className="flex flex-col gap-2 mb-4">
        <label className="font-semibold">上传简历文件</label>
        <input type="file" accept=".pdf,.doc,.docx" onChange={e => setCvFile(e.target.files[0])} />
        <button type="submit" className="bg-green-600 text-white py-2 rounded font-semibold hover:bg-green-700 transition" disabled={loading || !cvFile}>
          {loading ? '上传中...' : '上传简历'}
        </button>
      </form>
      {message && <div className="text-blue-600 mt-2">{message}</div>}
    </div>
  );
};

export default ProfilePage;

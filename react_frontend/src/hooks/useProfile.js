// useProfile.js
// 管理用户档案的自定义Hook，对应Django的profile_views.py
import { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';
import { AuthContext } from '../contexts/AuthContext';

export const useProfile = (options = {}) => {
  const { token, user } = useContext(AuthContext) || {};
  const { autoFetch = true } = options;

  const [profile, setProfile] = useState({
    user_cv_text: '',
    user_preferences_text: '',
    user_email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  // 获取用户档案
  const fetchProfile = async () => {
    if (!token || !user?.id) {
      setError('用户未登录');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await DefaultService.getUserProfileApiV1UserIdGet(user.id);
      setProfile(response || {
        user_cv_text: '',
        user_preferences_text: '',
        user_email: ''
      });
    } catch (err) {
      console.error('获取用户档案失败:', err);
      setError('获取用户档案失败');
    } finally {
      setLoading(false);
    }
  };

  // 更新用户档案
  const updateProfile = async (profileData) => {
    if (!token || !user?.id) {
      throw new Error('用户未登录');
    }

    setSaving(true);
    setError(null);

    try {
      const response = await DefaultService.updateUserProfileApiV1UserIdPut(
        user.id,
        profileData
      );

      // 更新本地状态
      setProfile(prev => ({ ...prev, ...profileData }));
      return response;
    } catch (err) {
      console.error('更新用户档案失败:', err);
      setError('更新用户档案失败');
      throw err;
    } finally {
      setSaving(false);
    }
  };

  // 上传CV文件
  const uploadCvFile = async (file) => {
    if (!token || !user?.id) {
      throw new Error('用户未登录');
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('cv_file', file);

      const response = await DefaultService.uploadCvFileApiV1UserIdUploadCvPost(
        user.id,
        { cv_file: file }
      );

      // 刷新档案以获取提取的文本
      await fetchProfile();
      return response;
    } catch (err) {
      console.error('上传CV文件失败:', err);
      setError('上传CV文件失败');
      throw err;
    } finally {
      setUploading(false);
    }
  };

  // 更新CV文本
  const updateCvText = async (cvText) => {
    return await updateProfile({ user_cv_text: cvText });
  };

  // 更新偏好设置
  const updatePreferences = async (preferencesText) => {
    return await updateProfile({ user_preferences_text: preferencesText });
  };

  // 更新邮箱
  const updateEmail = async (email) => {
    return await updateProfile({ user_email: email });
  };

  // 更新档案字段
  const updateProfileField = async (field, value) => {
    return await updateProfile({ [field]: value });
  };

  // 自动获取数据
  useEffect(() => {
    if (autoFetch && token && user?.id) {
      fetchProfile();
    }
  }, [token, user?.id, autoFetch]);

  return {
    // 数据
    profile,
    loading,
    error,
    saving,
    uploading,

    // 操作
    fetchProfile,
    updateProfile,
    uploadCvFile,
    updateCvText,
    updatePreferences,
    updateEmail,
    updateProfileField,

    // 计算属性
    isEmpty: !profile.user_cv_text && !profile.user_preferences_text,
    isComplete: !!(profile.user_cv_text && profile.user_preferences_text)
  };
};
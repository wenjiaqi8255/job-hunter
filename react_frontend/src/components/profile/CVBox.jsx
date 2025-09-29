// CVBox.jsx
// 对应Django main_page.html右侧栏的CV展示静态部分

import React, { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../../services/api_gen/services/DefaultService';
import { AuthContext } from '../../contexts/AuthContext';

const CVBox = () => {
  const contextValue = useContext(AuthContext) || {};
  const { user, token } = contextValue;
  const [profile, setProfile] = useState({ user_cv_text: '' });
  const [loading, setLoading] = useState(true);

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
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="glass-card mb-4 p-4 bg-white/80 rounded-xl shadow">
        <div className="flex justify-between items-center mb-3">
          <h5 className="font-bold text-lg">CV / Resume</h5>
          <a href="/login" className="text-blue-600 hover:underline">
            <i className="fas fa-sign-in-alt mr-1"></i> Login
          </a>
        </div>
        <div className="overflow-auto max-h-40">
          <p className="text-gray-500 text-sm">
            Please <a href="/login" className="text-blue-600">login</a> to view your CV.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-card mb-4 p-4 bg-white/80 rounded-xl shadow">
        <div className="flex justify-between items-center mb-3">
          <h5 className="font-bold text-lg">CV / Resume</h5>
          <a href="/profile" className="text-blue-600 hover:underline">
            <i className="fas fa-edit mr-1"></i> Edit
          </a>
        </div>
        <div className="overflow-auto max-h-40">
          <p className="text-gray-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card mb-4 p-4 bg-white/80 rounded-xl shadow">
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-bold text-lg">CV / Resume</h5>
        <a href="/profile" className="text-blue-600 hover:underline">
          <i className="fas fa-edit mr-1"></i> Edit
        </a>
      </div>
      <div className="overflow-auto max-h-40">
        {profile.user_cv_text ? (
          <p className="text-gray-700 text-sm whitespace-pre-wrap">{profile.user_cv_text}</p>
        ) : (
          <p className="text-gray-500 text-sm">
            No CV found. <a href="/profile" className="text-blue-600">Update your profile</a>.
          </p>
        )}
      </div>
    </div>
  );
};

export default CVBox;

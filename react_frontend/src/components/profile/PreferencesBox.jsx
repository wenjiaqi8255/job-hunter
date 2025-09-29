// PreferencesBox.jsx
// 对应Django main_page.html右侧栏的Job Preferences展示静态部分

import React, { useState, useEffect, useContext } from 'react';
import { DefaultService } from '../../services/api_gen/services/DefaultService';
import { AuthContext } from '../../contexts/AuthContext';

const PreferencesBox = () => {
  const contextValue = useContext(AuthContext) || {};
  const { user, token } = contextValue;
  const [profile, setProfile] = useState({ user_preferences_text: '' });
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
      <div className="glass-card p-4 bg-white/80 rounded-xl shadow">
        <div className="flex justify-between items-center mb-3">
          <h5 className="font-bold text-lg">Job Preferences</h5>
          <a href="/login" className="text-blue-600 hover:underline">
            <i className="fas fa-sign-in-alt mr-1"></i> Login
          </a>
        </div>
        <div className="overflow-auto max-h-40">
          <p className="text-gray-500 text-sm">
            Please <a href="/login" className="text-blue-600">login</a> to view your preferences.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-card p-4 bg-white/80 rounded-xl shadow">
        <div className="flex justify-between items-center mb-3">
          <h5 className="font-bold text-lg">Job Preferences</h5>
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
    <div className="glass-card p-4 bg-white/80 rounded-xl shadow">
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-bold text-lg">Job Preferences</h5>
        <a href="/profile" className="text-blue-600 hover:underline">
          <i className="fas fa-edit mr-1"></i> Edit
        </a>
      </div>
      <div className="overflow-auto max-h-40">
        {profile.user_preferences_text ? (
          <p className="text-gray-700 text-sm whitespace-pre-wrap">{profile.user_preferences_text}</p>
        ) : (
          <p className="text-gray-500 text-sm">
            No preferences set. <a href="/profile" className="text-blue-600">Add them in your profile</a>.
          </p>
        )}
      </div>
    </div>
  );
};

export default PreferencesBox;

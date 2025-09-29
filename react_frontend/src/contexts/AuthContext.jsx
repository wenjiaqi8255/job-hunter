// AuthContext.js
// 全局用户认证状态管理，支持JWT登录态

import React, { createContext, useState, useEffect, useRef, useContext } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('jwtToken') || null);
  const [loading, setLoading] = useState(false);
  const hasFetchedUser = useRef(false);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Only fetch user if we haven't already done so with this token
      if (!hasFetchedUser.current) {
        fetchMe();
      }
    } else {
      setUser(null);
      hasFetchedUser.current = false;
    }
  }, [token]);

  const fetchMe = async () => {
    setLoading(true);
    try {
      console.log('DEBUG: AuthContext fetching user info...');
      const res = await axios.get('/api/v1/auth/me');
      setUser(res.data);
      hasFetchedUser.current = true;
    } catch {
      setUser(null);
      setToken(null);
      localStorage.removeItem('jwtToken');
      hasFetchedUser.current = false;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      console.log('DEBUG: AuthContext logging in...');
      const res = await axios.post('/api/v1/auth/login', { email, password });
      setToken(res.data.access_token);
      localStorage.setItem('jwtToken', res.data.access_token);
      hasFetchedUser.current = false; // Reset for new token
      return true;
    } catch {
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    console.log('DEBUG: AuthContext logging out...');
    setUser(null);
    setToken(null);
    localStorage.removeItem('jwtToken');
    hasFetchedUser.current = false;
    delete axios.defaults.headers.common['Authorization'];
  };

  const register = async (email, password, username) => {
    setLoading(true);
    try {
      console.log('DEBUG: AuthContext registering...');
      const res = await axios.post('/api/v1/auth/register', { email, password, username });
      setToken(res.data.access_token);
      localStorage.setItem('jwtToken', res.data.access_token);
      hasFetchedUser.current = false; // Reset for new token
      return true;
    } catch {
      return false;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

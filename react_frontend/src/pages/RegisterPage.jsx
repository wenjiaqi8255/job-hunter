// RegisterPage.jsx
// 用户注册页面，对应Django注册功能

import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
// import { AuthContext } from '../../contexts/MockAuthContext';   
import { useNavigate } from 'react-router-dom';

const RegisterPage = () => {
  const { register, loading } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const success = await register(email, password, username);
    if (success) {
      navigate('/');
    } else {
      setError('注册失败，请检查信息');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 p-8 bg-white rounded-xl shadow">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">注册</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          type="email"
          placeholder="邮箱"
          value={email}
          onChange={e => setEmail(e.target.value)}
          className="border rounded p-2"
          required
        />
        <input
          type="text"
          placeholder="用户名"
          value={username}
          onChange={e => setUsername(e.target.value)}
          className="border rounded p-2"
          required
        />
        <input
          type="password"
          placeholder="密码"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className="border rounded p-2"
          required
        />
        <button type="submit" className="bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition" disabled={loading}>
          {loading ? '注册中...' : '注册'}
        </button>
        {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
      </form>
      <div className="mt-4 text-sm text-gray-500">
        已有账号？<a href="/login" className="text-blue-600 ml-1">登录</a>
      </div>
    </div>
  );
};

export default RegisterPage;

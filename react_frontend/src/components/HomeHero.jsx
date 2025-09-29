// HomeHero.jsx
// 对应Django main_page.html首页欢迎区静态部分
// 仅静态展示，不涉及登录状态和动态数据

import React from 'react';

const HomeHero = () => (
  <div className="bg-white/80 rounded-xl shadow-lg p-8 text-center max-w-xl mx-auto mt-12">
    <h1 className="text-3xl font-bold mb-4 text-blue-700">JobbAI - Your AI Job Copilot</h1>
    <p className="text-gray-600 mb-6">
      Transform Your Job Hunt with AI.<br />
      Get personalized job matches, save applications, and use all features by logging in.
    </p>
    <div className="flex flex-col gap-3">
          <button
      className="btn btn-primary w-full py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
      onClick={() => window.location.href = '/matching/start'}
    >
      <i className="fas fa-search mr-2"></i> Start Matching!
    </button>
      <a href="/login" className="btn btn-outline w-full py-2 rounded-lg border-blue-600 text-blue-600 font-semibold hover:bg-blue-50 transition">
        <i className="fas fa-sign-in-alt mr-2"></i> Login or Sign Up
      </a>
    </div>
  </div>
);

export default HomeHero;

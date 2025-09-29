// api.js
// 对应FastAPI jobs.py接口，负责获取工作列表数据

import axios from 'axios';

const API_BASE_URL = '/api/v1';

export const fetchJobs = async () => {
  // 对应FastAPI /api/v1/jobs/ 端点
  const response = await axios.get(`${API_BASE_URL}/jobs/`);
  return response.data;
};

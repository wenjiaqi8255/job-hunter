// httpClient.js - 统一的HTTP客户端
// 遵循SOLID原则：单一职责、开闭原则、依赖倒置
import axios from 'axios';
import { CONFIG } from '../config';

class HttpClient {
  constructor() {
    this.client = axios.create({
      baseURL: CONFIG.API.BASE_URL,
      timeout: CONFIG.API.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('jwtToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 添加CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
          config.headers['X-CSRFToken'] = csrfToken;
        }

        console.log(`DEBUG: ${config.method.toUpperCase()} ${config.url}`, config);
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(this.handleError(error));
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => {
        console.log(`DEBUG: Response ${response.status} from ${response.config.url}`, response.data);
        return response;
      },
      (error) => {
        console.error('Response error:', error);
        return Promise.reject(this.handleError(error));
      }
    );
  }

  handleError(error) {
    if (!error.response) {
      // 网络错误或超时
      return {
        message: CONFIG.ERROR.NETWORK,
        code: 'NETWORK_ERROR',
        originalError: error,
      };
    }

    const { status, data } = error.response;

    // 根据状态码返回标准化的错误信息
    switch (status) {
      case CONFIG.STATUS.UNAUTHORIZED:
        return {
          message: CONFIG.ERROR.UNAUTHORIZED,
          code: 'UNAUTHORIZED',
          status,
          data,
          originalError: error,
        };

      case CONFIG.STATUS.FORBIDDEN:
        return {
          message: CONFIG.ERROR.FORBIDDEN,
          code: 'FORBIDDEN',
          status,
          data,
          originalError: error,
        };

      case CONFIG.STATUS.NOT_FOUND:
        return {
          message: CONFIG.ERROR.NOT_FOUND,
          code: 'NOT_FOUND',
          status,
          data,
          originalError: error,
        };

      case CONFIG.STATUS.BAD_REQUEST:
        return {
          message: data?.detail || CONFIG.ERROR.VALIDATION_ERROR,
          code: 'VALIDATION_ERROR',
          status,
          data,
          originalError: error,
        };

      case CONFIG.STATUS.SERVER_ERROR:
        return {
          message: CONFIG.ERROR.SERVER_ERROR,
          code: 'SERVER_ERROR',
          status,
          data,
          originalError: error,
        };

      default:
        return {
          message: CONFIG.ERROR.UNKNOWN,
          code: 'UNKNOWN_ERROR',
          status,
          data,
          originalError: error,
        };
    }
  }

  async request(config, retryCount = 0) {
    try {
      const response = await this.client.request(config);
      return response.data;
    } catch (error) {
      // 检查是否需要重试
      if (
        retryCount < CONFIG.API.RETRY_COUNT &&
        error.status &&
        CONFIG.RETRY_STATUS_CODES.includes(error.status)
      ) {
        console.log(`Retrying request (${retryCount + 1}/${CONFIG.API.RETRY_COUNT})...`);
        await new Promise(resolve => setTimeout(resolve, CONFIG.API.RETRY_DELAY));
        return this.request(config, retryCount + 1);
      }

      throw error;
    }
  }

  // 便捷方法
  async get(url, config = {}) {
    return this.request({ method: 'GET', url, ...config });
  }

  async post(url, data = {}, config = {}) {
    return this.request({ method: 'POST', url, data, ...config });
  }

  async put(url, data = {}, config = {}) {
    return this.request({ method: 'PUT', url, data, ...config });
  }

  async patch(url, data = {}, config = {}) {
    return this.request({ method: 'PATCH', url, data, ...config });
  }

  async delete(url, config = {}) {
    return this.request({ method: 'DELETE', url, ...config });
  }
}

// 创建单例实例
const httpClient = new HttpClient();

export default httpClient;
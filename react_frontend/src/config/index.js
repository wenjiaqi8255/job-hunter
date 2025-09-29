// config/index.js - 统一配置管理
// 遵循SOLID原则：单一职责、开闭原则、依赖倒置

// API配置
export const API_CONFIG = {
  BASE_URL: '/api/v1',
  TIMEOUT: 30000, // 30秒超时
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000,
};

// 后端服务配置
export const SERVER_CONFIG = {
  HOST: 'localhost',
  PORT: 8001,
  FULL_URL: 'http://localhost:8001',
};

// 应用配置
export const APP_CONFIG = {
  NAME: 'JobbAI',
  VERSION: '1.0.0',
  DEBUG: import.meta.env.DEV,

  // 分页配置
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 10,
    MAX_PAGE_SIZE: 100,
  },

  // 会话历史配置
  SESSION_HISTORY: {
    MAX_ITEMS: 10,
    STORAGE_KEY: 'sessionHistory',
  },

  // 侧边栏配置
  SIDEBAR: {
    STORAGE_KEY: 'sidebarCollapsed',
    DEFAULT_COLLAPSED: false,
  },

  // Toast配置
  TOAST: {
    DEFAULT_DURATION: 3500,
    MAX_ITEMS: 5,
  },
};

// 错误消息配置
export const ERROR_MESSAGES = {
  NETWORK: '网络连接失败，请检查网络设置',
  TIMEOUT: '请求超时，请稍后重试',
  SERVER_ERROR: '服务器错误，请稍后重试',
  UNAUTHORIZED: '登录已过期，请重新登录',
  FORBIDDEN: '权限不足',
  NOT_FOUND: '请求的资源不存在',
  VALIDATION_ERROR: '数据验证失败',
  UNKNOWN: '未知错误，请稍后重试',
};

// 状态码映射
export const STATUS_CODES = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};

// 重试状态码（这些状态码下会重试请求）
export const RETRY_STATUS_CODES = [
  408, // Request Timeout
  429, // Too Many Requests
  500, // Internal Server Error
  502, // Bad Gateway
  503, // Service Unavailable
  504, // Gateway Timeout
];

// 导出所有配置
export const CONFIG = {
  API: API_CONFIG,
  SERVER: SERVER_CONFIG,
  APP: APP_CONFIG,
  ERROR: ERROR_MESSAGES,
  STATUS: STATUS_CODES,
  RETRY: RETRY_STATUS_CODES,
};

export default CONFIG;
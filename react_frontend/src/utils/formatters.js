/**
 * 文本格式化工具函数
 * 对应Django模板中的format_resume_text等过滤器
 */

/**
 * 格式化简历文本
 * 对应Django的format_resume_text过滤器
 * @param {string} text - 原始文本
 * @returns {string} - 格式化后的HTML
 */
export const formatResumeText = (text) => {
  if (!text) return '';

  return text
    // 保留换行
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .map(line => {
      // 处理标题行（以:结尾或全大写的行）
      if (line.endsWith(':') || line === line.toUpperCase()) {
        return `<strong>${escapeHtml(line)}</strong>`;
      }

      // 处理列表项（以•、-、*开头的行）
      if (line.match(/^[\s]*[•\-*]/)) {
        return `• ${escapeHtml(line.replace(/^[\s]*[•\-*]/, '').trim())}`;
      }

      // 处理加粗文本（用**包围的文本）
      return line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    })
    .join('<br>');
};

/**
 * 截断文本
 * 对应Django的truncatechars过滤器
 * @param {string} text - 原始文本
 * @param {number} length - 最大长度
 * @returns {string} - 截断后的文本
 */
export const truncateText = (text, length = 100) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length).trim() + '...';
};

/**
 * HTML转义
 * @param {string} text - 原始文本
 * @returns {string} - 转义后的文本
 */
export const escapeHtml = (text) => {
  if (!text) return '';

  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };

  return text.replace(/[&<>"']/g, m => map[m]);
};

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @returns {string} - 格式化后的日期字符串
 */
export const formatDate = (date) => {
  if (!date) return '';

  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} - 格式化后的文件大小
 */
export const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 高亮关键词
 * @param {string} text - 原始文本
 * @param {string} keyword - 关键词
 * @returns {string} - 高亮后的HTML
 */
export const highlightKeyword = (text, keyword) => {
  if (!text || !keyword) return escapeHtml(text);

  const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

/**
 * 转义正则表达式特殊字符
 * @param {string} string - 字符串
 * @returns {string} - 转义后的字符串
 */
export const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

/**
 * 清理文本（移除多余的空格和换行）
 * @param {string} text - 原始文本
 * @returns {string} - 清理后的文本
 */
export const cleanText = (text) => {
  if (!text) return '';

  return text
    .replace(/\r\n/g, '\n') // 统一换行符
    .replace(/\n\s*\n/g, '\n\n') // 移除多余的空行
    .replace(/^\s+|\s+$/g, '') // 移除首尾空格
    .replace(/[ \t]+/g, ' '); // 多个空格替换为一个
};

/**
 * 检查文本是否为空（包含空格和换行）
 * @param {string} text - 文本
 * @returns {boolean} - 是否为空
 */
export const isEmptyText = (text) => {
  return !text || text.trim().length === 0;
};

/**
 * 生成文件名（安全版本）
 * @param {string} filename - 原始文件名
 * @returns {string} - 安全的文件名
 */
export const sanitizeFilename = (filename) => {
  if (!filename) return 'untitled';

  return filename
    .replace(/[^\w\s\-_.]/g, '') // 移除特殊字符
    .replace(/\s+/g, '_') // 空格替换为下划线
    .replace(/_+/g, '_') // 多个下划线合并为一个
    .toLowerCase();
};

export default {
  formatResumeText,
  truncateText,
  escapeHtml,
  formatDate,
  formatFileSize,
  highlightKeyword,
  escapeRegExp,
  cleanText,
  isEmptyText,
  sanitizeFilename,
};
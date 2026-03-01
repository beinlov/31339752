/**
 * API配置模块
 * 统一管理API基础URL
 */

// 获取环境变量中的API地址
// Vite会在构建时替换 import.meta.env.VITE_API_BASE_URL
const getApiBaseUrl = () => {
  // 优先使用环境变量
  const envApiUrl = import.meta.env.VITE_API_BASE_URL;
  
  // 如果环境变量为空或未定义，使用当前域名（生产环境）
  if (!envApiUrl || envApiUrl === '') {
    // 生产环境：使用当前访问的域名和协议
    return window.location.origin;
  }
  
  // 开发环境或明确指定的API地址
  return envApiUrl;
};

// 导出API基础URL
export const API_BASE_URL = getApiBaseUrl();

// 导出构建完整API路径的辅助函数
export const getApiUrl = (path) => {
  // 确保path以/开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

// 打印当前使用的API地址（方便调试）
console.log('API Base URL:', API_BASE_URL);

export default {
  API_BASE_URL,
  getApiUrl
};

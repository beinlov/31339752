/**
 * API配置模块
 * 统一管理API基础URL
 */

// 获取环境变量中的API地址
// Vite会在构建时替换 import.meta.env.VITE_API_BASE_URL
const getApiBaseUrl = () => {
  // 优先使用环境变量
  const envApiUrl = import.meta.env.VITE_API_BASE_URL;
  
  console.log('[API Config] 环境变量 VITE_API_BASE_URL:', envApiUrl);
  console.log('[API Config] window.location.origin:', window.location.origin);
  
  // 如果环境变量为空或未定义，使用当前域名的8000端口
  if (!envApiUrl || envApiUrl === '') {
    // 从当前访问地址推断后端API地址
    const origin = window.location.origin;
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const backendUrl = `${protocol}//${hostname}:8000`;
    console.log('[API Config] 未找到环境变量，使用推断的后端地址:', backendUrl);
    return backendUrl;
  }
  
  // 开发环境或明确指定的API地址
  console.log('[API Config] 使用环境变量指定的地址:', envApiUrl);
  return envApiUrl;
};

// 导出API基础URL
export const API_BASE_URL = getApiBaseUrl();

// 导出构建完整API路径的辅助函数
export const getApiUrl = (path) => {
  // 确保path以/开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const fullUrl = `${API_BASE_URL}${normalizedPath}`;
  console.log('[API Config] 生成完整URL:', fullUrl);
  return fullUrl;
};

// 打印当前使用的API地址（方便调试）
console.log('[API Config] 最终API Base URL:', API_BASE_URL);

export default {
  API_BASE_URL,
  getApiUrl
};

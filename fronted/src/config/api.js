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
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // ⚠️ 特殊处理：如果访问的是映射地址，使用映射后的后端地址
    // 前后端共用83端口，本地Nginx通过路径区分：
    // 10.10.66.95:83/api/ → 本地Nginx → localhost:8000 (后端)
    // 10.10.66.95:83/     → 本地Nginx → dist静态文件  (前端)
    if (hostname === '10.10.66.95') {
      const backendUrl = 'http://10.10.66.95:83';  // 与前端相同端口，通过/api/路径区分
      console.log('[API Config] 检测到映射地址，使用映射后的后端地址:', backendUrl);
      return backendUrl;
    }
    
    // 其他情况，继续使用推断逻辑
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

import fetch from 'dva/fetch';

function parseJSON(response) {
  return response.json();
}

function checkStatus(response) {
  if (response.status >= 200 && response.status < 300) {
    return response;
  }

  const error = new Error(response.statusText);
  error.response = response;
  throw error;
}

export default function request(url, options = {}) {
  // 设置默认headers
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // 合并选项
  const newOptions = { ...defaultOptions, ...options };
  
  // 如果有data且是POST/PUT请求，自动将data转为JSON字符串
  if (newOptions.data && (newOptions.method === 'POST' || newOptions.method === 'PUT')) {
    newOptions.body = JSON.stringify(newOptions.data);
    delete newOptions.data;
  }

  return fetch(url, newOptions)
    .then(checkStatus)
    .then(parseJSON)
    .then(data => data)
    .catch(err => {
      console.error('Request Error:', err);
      throw err;
    });
}

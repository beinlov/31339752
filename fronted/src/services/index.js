import request from '../utils/request';

// 获取中间界面数据请求
export const getCenterPageData = async () => {
  return request('http://localhost:8000/api/centerPageData').then(response => {
    return response.data;
  });
};

// 获取左侧界面数据请求
export const getLeftPageData = async () => {
  return request('http://localhost:8000/api/leftPageData').then(response => {
    return response.data;
  });
};

// 获取右侧界面数据请求
export const getRightPageData = async () => {
  return request('http://localhost:8000/api/rightPageData').then(response => {
    return response.data;
  });
};

// 服务器管理API

// 获取服务器列表
export const getServers = async (page = 1, pageSize = 10) => {
  return request(`http://localhost:8000/api/server/servers?page=${page}&page_size=${pageSize}`).then(response => {
    return response;
  });
};

// 获取单个服务器详情
export const getServerById = async (id) => {
  return request(`http://localhost:8000/api/server/servers/${id}`).then(response => {
    return response;
  });
};

// 创建服务器
export const createServer = async (serverData) => {
  return request('http://localhost:8000/api/server/servers', {
    method: 'POST',
    data: serverData,
  }).then(response => {
    return response;
  });
};

// 更新服务器
export const updateServer = async (id, serverData) => {
  return request(`http://localhost:8000/api/server/servers/${id}`, {
    method: 'PUT',
    data: serverData,
  }).then(response => {
    return response;
  });
};

// 删除服务器
export const deleteServer = async (id) => {
  return request(`http://localhost:8000/api/server/servers/${id}`, {
    method: 'DELETE',
  }).then(response => {
    return response;
  });
};

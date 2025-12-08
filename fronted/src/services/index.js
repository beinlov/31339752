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

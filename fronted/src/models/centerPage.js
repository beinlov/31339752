import { getCenterPageData } from '../services/index';

export default {
  // 命名空间 (必填)
  namespace: 'centerPage',

  // 数据
  state: {
    detailsList: null,
    mapData: null,
    userSitua: null,
  },

  // 路由监听
  subscriptions: {
    setup({ dispatch, history }) {
      return history.listen(({ pathname }) => {
        if (pathname === '/') {
          dispatch({ type: 'getCenterPageData' });
        }
      });
    },
  },

  // 异步请求
  effects: {
    *getCenterPageData({ payload }, { call, put }) {
      const data = yield call(getCenterPageData);
      if (data) {
        yield put({
          type: 'setData',
          payload: {
            detailsList: data.detailsList,
            mapData: data.mapData,
            userSitua: data.userSitua,
          },
        });
      } else {
        console.log(`获取中间数据数据失败`);
      }
    },
  },

  // 同步操作
  reducers: {
    setData(state, { payload }) {
      return { ...state, ...payload };
    },
  },
};

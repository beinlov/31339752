import { getLeftPageData } from '../services/index';
export default {
  // 命名空间 (必填)
  namespace: 'leftPage',

  // 数据
  state: {
    trafficSitua: null,
    accessFrequency: null,
    peakFlow: null,
    worldMapData: {
      citys: [
        { name: '纽约', value: [-74.006, 40.7127] },
        { name: '伦敦', value: [-0.1262, 51.5002] },
        { name: '东京', value: [139.6917, 35.6895] },
        { name: '巴黎', value: [2.3522, 48.8566] },
        { name: '北京', value: [116.4074, 39.9042] },
        { name: '莫斯科', value: [37.6173, 55.7558] },
        { name: '新加坡', value: [103.8198, 1.3521] },
        { name: '迪拜', value: [55.2708, 25.2048] },
        { name: '悉尼', value: [151.2093, -33.8688] },
        { name: '圣保罗', value: [-46.6333, -23.5505] }
      ],
    },
  },

  // 路由监听
  // subscriptions: {
  //   setup({ dispatch, history }) {
  //     return history.listen((location, action) => {
  //       // 参数可以直接简写成{pathname}
  //       if (location.pathname === '/') {
  //         dispatch({ type: 'getLeftPageData' });
  //       }
  //     });
  //   },
  // },

  // // 异步请求
  // effects: {
  //   *getLeftPageData({ payload }, { call, put }) {
  //     const data = yield call(getLeftPageData);
  //     if (data) {
  //       yield put({
  //         type: 'setData',
  //         payload: data,
  //       });
  //     } else {
  //       console.log(`获取左侧数据数据失败`);
  //     }
  //   },
  // },

  // 同步操作
  reducers: {
    setData(state, action) {
      return { ...state, ...action.payload };
    },
  },
};

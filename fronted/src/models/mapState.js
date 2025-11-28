import { delay } from '../utils';
import request from '../utils/request';

// 规范化省份名称（与options.js中的逻辑保持一致）
const normalizeProvince = (rawName) => {
  if (!rawName) return '';

  let name = rawName.trim();
  // 去掉"中国"前缀
  name = name.replace(/^中国/, '');

  // 在第一个行政区关键字处截断后面全部内容
  const match = name.match(/(壮族自治区|回族自治区|维吾尔自治区|特别行政区|自治区|省|市)/);
  if (match) {
    const index = match.index;
    if (index > 0) {
      name = name.slice(0, index);
    } else if (index === 0) {
      return rawName;
    }
  }

  return name;
};

export default {
  namespace: 'mapState',

  state: {
    currentMap: 'china',
    selectedNetwork: 'asruex',
    botnetData: {
      china_amount: 0,
      global_amount: 0
    },
    showFlyLines: false,
    provinceData: null,  // Store province data here
    lastFetchTime: 0,     // Track last fetch time
    botnetDistribution: [], // Store botnet distribution data
    worldData: null,  // Store world map data
    cityData: null,  // Add city data state
    currentProvince: null  // Add current province state
  },

  reducers: {
    setCurrentMap(state, { payload }) {
      return {
        ...state,
        currentMap: payload,
      };
    },
    setSelectedNetwork(state, { payload }) {
      return { ...state, selectedNetwork: payload };
    },
    updateBotnetData(state, { payload }) {
      return { ...state, botnetData: payload };
    },
    triggerFlyLines(state, { payload }) {
      return { ...state, showFlyLines: payload };
    },
    updateProvinceData(state, { payload }) {
      return {
        ...state,
        provinceData: payload,
        lastFetchTime: Date.now()
      };
    },
    updateBotnetDistribution(state, { payload }) {
      return {
        ...state,
        botnetDistribution: payload
      };
    },
    updateWorldData(state, { payload }) {
      return {
        ...state,
        worldData: payload
      };
    },
    updateCityData(state, { payload }) {
      return {
        ...state,
        cityData: payload
      };
    },
    setCurrentProvince(state, { payload }) {
      return {
        ...state,
        currentProvince: payload
      };
    }
  },

  effects: {
    *handleFlyLines({ payload }, { put }) {
      yield put({ type: 'triggerFlyLines', payload: true });
      yield new Promise(resolve => setTimeout(resolve, 10000));
      yield put({ type: 'triggerFlyLines', payload: false });
    },

    *fetchProvinceData({ payload }, { call, put, select }) {
      try {
        const state = yield select(state => state.mapState);
        const networkToUse = payload || state.selectedNetwork || '`asruex`';

        // Fetch province data
        const response = yield call(request, `http://localhost:8000/api/province-amounts?botnet_type=${networkToUse}`);

        if (response) {
          yield put({
            type: 'updateProvinceData',
            payload: response
          });
        }
      } catch (error) {
        console.error('获取省份数据失败:', error);
      }
    },

    *fetchBotnetDistribution({ payload }, { call, put, select }) {
      try {
        // Fetch botnet distribution data
        const response = yield call(request, 'http://localhost:8000/api/botnet-distribution');

        if (response) {
          // Update the full distribution data
          yield put({
            type: 'updateBotnetDistribution',
            payload: response
          });

          // Also update the selected network's data
          const state = yield select(state => state.mapState);
          const networkToUse = payload || state.selectedNetwork || 'asruex';
          const matchedData = response.find(item => item.name === networkToUse) || {
            china_amount: 0,
            global_amount: 0
          };

          yield put({
            type: 'updateBotnetData',
            payload: matchedData
          });
        }
      } catch (error) {
        console.error('获取僵尸网络分布数据失败:', error);
      }
    },

    *fetchWorldData({ payload }, { call, put, select }) {
      try {
        const state = yield select(state => state.mapState);
        const networkToUse = payload || state.selectedNetwork || 'asruex';

        // Fetch world map data
        const response = yield call(request, `http://localhost:8000/api/world-amounts?botnet_type=${networkToUse}`);

        if (response) {
          yield put({
            type: 'updateWorldData',
            payload: response
          });
        }
      } catch (error) {
        console.error('获取世界地图数据失败:', error);
      }
    },

    *fetchCityData({ payload }, { call, put, select }) {
      try {
        const state = yield select(state => state.mapState);
        const networkToUse = state.selectedNetwork || 'asruex';
        const provinceName = payload || state.currentProvince;

        if (!provinceName || provinceName === 'china') {
          yield put({ type: 'updateCityData', payload: null });
          return;
        }

        // 使用 normalizeProvince 函数规范化省份名称
        const shortName = normalizeProvince(provinceName);

        const response = yield call(
          request,
          `http://localhost:8000/api/city-amounts/${encodeURIComponent(shortName)}?botnet_type=${networkToUse}`
        );

        if (response && response.data) {
          yield put({
            type: 'updateCityData',
            payload: response.data
          });
        }
      } catch (error) {
        console.error('获取城市数据失败:', error);
        yield put({ type: 'updateCityData', payload: null });
      }
    },

    *changeMap({ payload }, { put }) {
      yield put({ type: 'setCurrentMap', payload });
      yield put({ type: 'setCurrentProvince', payload });
      if (payload !== 'china') {
        yield put({ type: 'fetchCityData', payload });
      } else {
        yield put({ type: 'updateCityData', payload: null });
      }
    },

    *changeNetwork({ payload }, { put, select }) {
      yield put({ type: 'setSelectedNetwork', payload });
      const state = yield select(state => state.mapState);

      // 重新获取所有需要的数据
      yield put({ type: 'fetchProvinceData', payload });
      yield put({ type: 'fetchWorldData', payload });
      yield put({ type: 'fetchBotnetDistribution', payload });

      // 如果在省份视图中，也重新获取城市数据
      if (state.currentMap !== 'china') {
        yield put({ type: 'fetchCityData' });
      }
    }
  },

  subscriptions: {
    setup({ dispatch, history }) {
      // Initial data fetch on app start
      dispatch({ type: 'fetchBotnetDistribution' });

      let dataTimer = null;

      return history.listen(({ pathname }) => {
        // Clear existing timer
        if (dataTimer) clearInterval(dataTimer);

        if (pathname === '/index') {
          // Initial data fetch
          dispatch({ type: 'fetchProvinceData' });
          dispatch({ type: 'fetchBotnetDistribution' });
          dispatch({ type: 'fetchWorldData' });

          // Set up single timer for all data updates with 30 second interval
          dataTimer = setInterval(() => {
            dispatch({ type: 'fetchProvinceData' });
            dispatch({ type: 'fetchBotnetDistribution' });
            dispatch({ type: 'fetchWorldData' });
            // Only fetch city data if we're in a province view
            const state = window.g_app._store.getState().mapState;
            if (state.currentMap !== 'china') {
              dispatch({ type: 'fetchCityData' });
            }
          }, 1700); // Changed from 1000ms to 30000ms (30 seconds)
        }
      });
    }
  }
};

import * as echarts from 'echarts';
import { registerMap } from 'echarts/core';
import chinaJson from "../../../china.json";

// 注册中国地图数据
registerMap('china', chinaJson);

// 导出省份映射关系
export const provinceMap = {
  '北京': '110000',
  '天津': '120000',
  '河北': '130000',
  '山西': '140000',
  '内蒙古': '150000',
  '辽宁': '210000',
  '吉林': '220000',
  '黑龙江': '230000',
  '上海': '310000',
  '江苏': '320000',
  '浙江': '330000',
  '安徽': '340000',
  '福建': '350000',
  '江西': '360000',
  '山东': '370000',
  '河南': '410000',
  '湖北': '420000',
  '湖南': '430000',
  '广东': '440000',
  '广西': '450000',
  '海南': '460000',
  '重庆': '500000',
  '四川': '510000',
  '贵州': '520000',
  '云南': '530000',
  '西藏': '540000',
  '陕西': '610000',
  '甘肃': '620000',
  '青海': '630000',
  '宁夏': '640000',
  '新疆': '650000',
  '台湾': '710000',
  '香港': '810000',
  '澳门': '820000'
};

// 导出省份名称映射
export const provinceNameMap = {
  '北京市': '北京',
  '天津市': '天津',
  '河北省': '河北',
  '山西省': '山西',
  '内蒙古自治区': '内蒙古',
  '辽宁省': '辽宁',
  '吉林省': '吉林',
  '黑龙江省': '黑龙江',
  '上海市': '上海',
  '江苏省': '江苏',
  '浙江省': '浙江',
  '安徽省': '安徽',
  '福建省': '福建',
  '江西省': '江西',
  '山东省': '山东',
  '河南省': '河南',
  '湖北省': '湖北',
  '湖南省': '湖南',
  '广东省': '广东',
  '广西省': '广西',
  '海南省': '海南',
  '重庆市': '重庆',
  '四川省': '四川',
  '贵州省': '贵州',
  '云南省': '云南',
  '西藏自治区': '西藏',
  '陕西省': '陕西',
  '甘肃省': '甘肃',
  '青海省': '青海',
  '宁夏回族自治区': '宁夏',
  '新疆': '新疆',
  '台湾省': '台湾',
  '香港特别行政区': '香港',
  '澳门特别行政区': '澳门'
};

// 添加省会城市坐标
const provinceCoordinates = {
  '北京': [116.405285, 39.904989],
  '天津': [117.190182, 39.125596],
  '河北': [114.502461, 38.045474],
  '山西': [112.549248, 37.857014],
  '内蒙古': [111.670801, 40.818311],
  '辽宁': [123.429096, 41.796767],
  '吉林': [125.324501, 43.886841],
  '黑龙江': [126.642464, 45.756967],
  '上海': [121.472644, 31.231706],
  '江苏': [118.767413, 32.041544],
  '浙江': [120.153576, 30.287459],
  '安徽': [117.283042, 31.86119],
  '福建': [119.306239, 26.075302],
  '江西': [115.892151, 28.676493],
  '山东': [117.000923, 36.675807],
  '河南': [113.665412, 34.757975],
  '湖北': [114.298572, 30.584355],
  '湖南': [112.982279, 28.19409],
  '广东': [113.280637, 23.125178],
  '广西': [108.320004, 22.82402],
  '海南': [110.33119, 20.031971],
  '重庆': [106.504962, 29.533155],
  '四川': [104.065735, 30.659462],
  '贵州': [106.713478, 26.578343],
  '云南': [102.712251, 25.040609],
  '西藏': [91.132212, 29.660361],
  '陕西': [108.948024, 34.263161],
  '甘肃': [103.823557, 36.058039],
  '青海': [101.778916, 36.623178],
  '宁夏': [106.278179, 38.46637],
  '新疆': [87.617733, 43.792818],
  '台湾': [121.509062, 25.044332],
  '香港': [114.165460, 22.275340],
  '澳门': [113.549090, 22.198951],
};

// 获取所有省份数据的最大和最小值
const getMinMaxValues = (data) => {
  if (!Array.isArray(data) || !data.length) return { min: 0, max: 0 };
  const values = data.map(item => item.amount);
  return {
    min: Math.min(...values),
    max: Math.max(...values)
  };
};

// 计算数据的分位数
const calculateQuantiles = (data) => {
  if (!Array.isArray(data) || !data.length) return [0, 0, 0, 0, 0, 0];

  const values = data.map(item => item.amount).sort((a, b) => a - b);
  const maxValue = values[values.length - 1];

  // 计算分位数
  const q1Index = Math.floor(values.length * 0.2);
  const q2Index = Math.floor(values.length * 0.4);
  const q3Index = Math.floor(values.length * 0.6);
  const q4Index = Math.floor(values.length * 0.8);

  return [
    0,
    values[q1Index] || 0,
    values[q2Index] || 0,
    values[q3Index] || 0,
    values[q4Index] || 0,
    maxValue
  ];
};

// 获取省份颜色的函数，使用相对比例
const getProvinceColorByRatio = (value, maxValue) => {
  if (value === 0) return '#1D1E4C';  // 零值使用深蓝色
  if (value === maxValue) return '#5C0011';  // 最大值使用深红色

  // 使用相对比例而不是绝对值，颜色从深到浅
  const ratio = maxValue > 0 ? value / maxValue : 0;

  if (ratio >= 0.8) return '#5C0011';      // 深红色 - 最高等级
  if (ratio >= 0.6) return '#B71D1C';      // 红色
  if (ratio >= 0.4) return '#F75D59';      // 浅红色
  if (ratio >= 0.2) return '#3B5998';      // 蓝色
  return '#6495ED';  // 其他非零值使用浅蓝色
};

// 将数据转换为地图所需格式
const convertData = (data) => {
  if (!Array.isArray(data)) return [];

  // 找出最大值用于相对比例计算
  const maxValue = Math.max(...data.map(item => item.amount));

  // 创建一个包含所有省份的映射，初始值为0
  const provinceDataMap = {};

  // 创建反向映射，从简称到全称
  const reverseProvinceMap = {};
  Object.entries(provinceNameMap).forEach(([fullName, shortName]) => {
    reverseProvinceMap[shortName] = fullName;
  });

  // 初始化所有省份数据为0
  Object.keys(provinceNameMap).forEach(provinceName => {
    provinceDataMap[provinceName] = 0;
  });

  // 更新有数据的省份
  data.forEach(item => {
    // 获取省份全称
    const fullName = reverseProvinceMap[item.province];
    if (fullName) {
      provinceDataMap[fullName] = item.amount;
    }
  });

  // 转换为ECharts需要的格式
  return Object.entries(provinceDataMap).map(([name, value]) => ({
    name,
    value,
    itemStyle: {
      areaColor: getProvinceColorByRatio(value, maxValue),
      borderColor: 'rgba(147, 235, 248, 0.3)'
    },
    emphasis: {
      itemStyle: {
        areaColor: 'rgba(147, 235, 248, 0.5)',
        borderWidth: 1
      }
    }
  }));
};

// 将城市数据转换为地图所需格式
const convertCityData = (data) => {
  if (!Array.isArray(data)) return [];

  // 找出最大值用于相对比例计算
  const maxValue = data.length > 0 ? Math.max(...data.map(item => item.amount)) : 0;

  return data.map(item => ({
    name: item.city + '市',  // 添加"市"后缀以匹配地图数据
    value: item.amount,
    itemStyle: {
      areaColor: getProvinceColorByRatio(item.amount, maxValue),
      borderColor: 'rgba(147, 235, 248, 0.3)'
    }
  }));
};

export const mapOptions = (params, currentMap, isLeftPage = false) => {
  const maxValue = params.provinceData ? getMinMaxValues(params.provinceData).max : 0;
  const quantiles = params.provinceData ? calculateQuantiles(params.provinceData) : [0, 0, 0, 0, 0, 0];

  // 根据当前地图类型调整配置
  const isProvince = currentMap !== 'china';

  // 计算城市数据的最大值和分位数
  let cityMaxValue = 0;
  let cityQuantiles = [0, 0, 0, 0, 0, 0];
  if (isProvince && params.cityData && Array.isArray(params.cityData)) {
    cityMaxValue = Math.max(...params.cityData.map(item => item.amount));
    const cityValues = params.cityData.map(item => item.amount).sort((a, b) => a - b);
    const len = cityValues.length;
    cityQuantiles = [
      0,
      cityValues[Math.floor(len * 0.2)] || 0,
      cityValues[Math.floor(len * 0.4)] || 0,
      cityValues[Math.floor(len * 0.6)] || 0,
      cityValues[Math.floor(len * 0.8)] || 0,
      cityMaxValue
    ];
  }

  // 获取城市感染数据映射
  const cityAmountMap = {};
  if (params.cityData && Array.isArray(params.cityData)) {
    params.cityData.forEach(item => {
      cityAmountMap[item.city] = item.amount;
    });
  }

  // 添加飞线配置
  const lines = [];
  if (params.showLines && currentMap === 'china') {
    const guangdongCoord = [113.280637, 23.125178];  // 广东省坐标

    // 创建飞线数据，确保只从广东发出
    Object.entries(provinceCoordinates).forEach(([province, coord]) => {
      if (province !== '广东') {
        lines.push({
          coords: [guangdongCoord, coord],  // 始终从广东出发到其他省份
          lineStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: 'rgba(255, 77, 77, 0.8)'  // 起点更亮的红色
              }, {
                offset: 1,
                color: 'rgba(255, 77, 77, 0.1)'  // 终点渐隐的红色
              }]
            },
            width: 1,
            opacity: 0.8,
            curveness: 0.2
          }
        });
      }
    });
  }

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: params => {
        const value = params.value || (params.data && params.data.value);
        if (value !== undefined) {
          return `${params.name.replace(/(市|州|地区)$/, '')}<br/>感染节点数量：${value}`;
        }
        return params.name;
      }
    },
    visualMap: {
      show: true,
      type: 'piecewise',
      min: 0,
      max: isProvince ? cityMaxValue : maxValue,
      splitNumber: 6,
      pieces: isProvince ? [
        {min: cityQuantiles[4], max: cityMaxValue, color: '#5C0011'},
        {min: cityQuantiles[3], max: cityQuantiles[4], color: '#B71D1C'},
        {min: cityQuantiles[2], max: cityQuantiles[3], color: '#F75D59'},
        {min: cityQuantiles[1], max: cityQuantiles[2], color: '#3B5998'},
        {min: 1, max: cityQuantiles[1], color: '#6495ED'},
        {value: 0, color: '#1D1E4C'}
      ] : [
        {min: quantiles[4], max: maxValue, color: '#5C0011'},
        {min: quantiles[3], max: quantiles[4], color: '#B71D1C'},
        {min: quantiles[2], max: quantiles[3], color: '#F75D59'},
        {min: quantiles[1], max: quantiles[2], color: '#3B5998'},
        {min: 1, max: quantiles[1], color: '#6495ED'},
        {value: 0, color: '#1D1E4C'}
      ],
      text: ['高', '低'],
      realtime: false,
      calculable: false,
      textStyle: {
        color: '#fff'
      },
      left: '4%'
    },
    geo: {
      map: currentMap,
      roam: false,
      scaleLimit: {
        min: 1,
        max: 8
      },
      zoom: isProvince ?
        (currentMap === '海南' ? 8 : 0.9) : 1.6,
      center: isProvince && currentMap === '海南' ?
        [109.844902, 19.0392] : undefined,
      top: isProvince ? '20%' : '34%',
      label: {
        show: true,
        formatter: (params) => {
          return params.name.replace(/(省|市|自治区|特别行政区|地区|州)$/, '');
        },
        textStyle: {
          color: 'rgba(255,255,255,0.8)',
          fontSize: isProvince ? 14 : 14,
          fontWeight: 'normal',
          textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
        }
      },
      itemStyle: {
        areaColor: '#1D1E4C',
        borderColor: 'rgba(147, 235, 248, 0.3)',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          areaColor: 'rgba(147, 235, 248, 0.5)',
          borderWidth: 1
        }
      }
    },
    series: [
      {
        name: '感染数量',
        type: 'map',
        geoIndex: 0,
        data: isProvince ?
          (params.cityData ? convertCityData(params.cityData) : []) :
          (params.provinceData ? convertData(params.provinceData) : []),
        nameProperty: 'name'
      },
      {
        name: '清除路线',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 2,
        effect: {
          show: true,
          period: 3,
          trailLength: 0.5,
          symbol: 'circle',
          symbolSize: 2,
          loop: true,
          color: 'rgb(255, 255, 204)'
        },
        lineStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{
            offset: 0,
            color: 'rgba(255, 153, 0, 0.9)'
          }, {
            offset: 1,
            color: 'rgba(255, 255, 204, 0.1)'
          }]),
          width: 1,
          opacity: 0.9,
          curveness: 0.2
        },
        data: lines
      },
      {
        name: '光晕效果',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 1,
        effect: {
          show: true,
          period: 20,
          trailLength: 0.3,
          symbol: 'circle',
          symbolSize: 3,
          loop: true,
          color: 'rgb(255, 255, 204)'
        },
        lineStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{
            offset: 0,
            color: 'rgba(255, 153, 0, 0.6)'
          }, {
            offset: 1,
            color: 'rgba(255, 255, 204, 0)'
          }]),
          width: 2,
          opacity: 0.3,
          curveness: 0.2
        },
        data: lines
      }
    ]
  };
};

export const userOptions = (data) => {
  return {
    header: ['时间', 'IP', '地区', '指令'],
    data: data || [],
  };
};

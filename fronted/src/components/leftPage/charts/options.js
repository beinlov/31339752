import * as echarts from 'echarts';

export const userOptions = (params = {}) => ({
  header: params.header,
  data: params.data,
});

// 添加获取世界地图颜色的函数，与地图组件保持一致
const getWorldMapColor = (value) => {
  if (value >= 1000) return '#5C0011';     // 深红
  if (value >= 800)  return '#B71D1C';     // 红
  if (value >= 500)  return '#F75D59';     // 浅红
  if (value >= 300)  return '#3B5998';     // 蓝
  if (value >= 100)  return '#6495ED';     // 浅蓝
  return '#1D1E4C';                        // 深蓝
};


// 将世界地图数据转换为所需格式
const convertWorldMapData = (data) => {
  if (!Array.isArray(data) || data.length === 0) return [];

  // 找出最大值用于相对比例计算
  const maxValue = Math.max(...data.map(item => item.amount));

  return data.map(item => ({
    name: item.country,
    value: item.amount,
    itemStyle: {
      normal: {
          areaColor: getWorldMapColor(item.amount)
      }
    }
  }));
};

export const worldMapOptions = (params, isLeftPage = false) => {
  const countryData = params.countryData || [];

  // 计算数据的最大值和分位点
  let maxValue = 0;
  let quantiles = [0, 0, 0, 0, 0];

  if (countryData.length > 0) {
    const values = countryData.map(item => item.amount).sort((a, b) => a - b);
    maxValue = values[values.length - 1];

    // 计算分位数
    const q1Index = Math.floor(values.length * 0.2);
    const q2Index = Math.floor(values.length * 0.4);
    const q3Index = Math.floor(values.length * 0.6);
    const q4Index = Math.floor(values.length * 0.8);

    quantiles = [
      0,
      values[q1Index] || 0,
      values[q2Index] || 0,
      values[q3Index] || 0,
      values[q4Index] || 0,
      maxValue
    ];
  }

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: params => {
        if (params.value) {
          return `${params.name}<br/>感染节点数量：${params.value}`;
        }
        return params.name;
      }
    },
    visualMap: {
      show: !isLeftPage,  // 在左侧页面隐藏visualMap
      type: 'piecewise',
      min: 0,
      max: maxValue,
      splitNumber: 6,
      pieces: [
        { min: 1000, color: '#5C0011' },
        { min: 800,  max: 999,  color: '#B71D1C' },
        { min: 500,  max: 799,  color: '#F75D59' },
        { min: 300,  max: 499,  color: '#3B5998' },
        { min: 100,  max: 299,  color: '#6495ED' },
        { min: 1,    max: 99,   color: '#1D1E4C' },
        { min: 0,    max: 0,    color: '#000000' }
      ],
      text: ['高', '低'],
      realtime: false,
      calculable: false,
      textStyle: {
        color: '#fff'
      },
      left: '4%',
      bottom: '4%'
    },
    geo: {
      map: 'world',
      roam: true, // 启用缩放和平移
      zoom: 1.2,
      center: [0, 0], // 调整地图中心点
      label: {
        normal: {
          show: false,
        },
        emphasis: {
          show: true,
          color: '#fff',
          textStyle: {
            fontSize: 12,
          },
        },
      },
      itemStyle: {
        normal: {
          borderColor: 'rgba(147, 235, 248, 0.3)',
          borderWidth: 1,
          areaColor: '#000000', // 使用深蓝色作为默认底色
          shadowColor: 'rgba(0, 0, 0, 0.5)',
          shadowOffsetX: 0,
          shadowOffsetY: 2,
          shadowBlur: 10
        },
        emphasis: {
          areaColor: 'rgba(147, 235, 248, 0.5)',  // 使用浅蓝色作为悬停效果
          borderWidth: 1
        }
      },
    },
    series: [
      {
        name: '感染数量',
        type: 'map',
        geoIndex: 0,
        data: convertWorldMapData(countryData)
      },
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: params.citys || [],
        symbolSize: 8,
        showEffectOn: 'render',
        rippleEffect: {
          brushType: 'stroke',
          scale: 4,
          period: 4
        },
        hoverAnimation: true,
        itemStyle: {
          normal: {
            color: '#f4e925',
            shadowBlur: 10,
            shadowColor: '#333'
          }
        },
        zlevel: 1
      }
    ]
  };
};

// 修改获取地图颜色的函数，与地图组件保持一致
const getMapColor = (value) => {
  if (value >= 1000) return '#5C0011';
  if (value >= 800)  return '#B71D1C';
  if (value >= 500)  return '#F75D59';
  if (value >= 300)  return '#3B5998';
  if (value >= 100)  return '#6495ED';
  return '#1D1E4C';
};

export const affectedOptions = (params) => {
  const { provinces = [], data = [], isWorldView = false, isCityView = false } = params;

  // 计算最大值用于相对比例
  const maxValue = Math.max(...data.map(item => item.value));

  // 将数据和省份名称组合
  const sortedValues = data.map((item, index) => ({
    value: item.value,
    name: provinces[index],
    percentage: item.percentage
  }));

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        const data = params[0].data;
        return `${data.name}<br/>数量：${data.value}<br/>占比：${data.percentage}%`;
      }
    },
    grid: {
      top: '5%',
      left: '3%',
      right: '15%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      show: false,
      type: 'value'
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: provinces,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#BCDCFF',
        fontSize: isWorldView ? 10 : (isCityView ? 11 : 12),
        margin: 10,
        formatter: function(value) {
          if (value.length > 6) {
            return value.substring(0, 6) + '...';
          }
          return value;
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: sortedValues,
        barWidth: isWorldView ? '45%' : (isCityView ? '40%' : '35%'),
        barCategoryGap: isWorldView ? '20%' : (isCityView ? '30%' : '40%'),
        barGap: '15%',
        label: {
          show: true,
          position: 'right',
          color: '#fff',
          fontSize: 12,
          distance: 10,
          formatter: function(params) {
            return `${params.value}(${params.data.percentage}%)`;
          },
          textBorderColor: 'rgba(0,0,0,0.3)',
          textBorderWidth: 2
        },
        itemStyle: {
          color: function(params) {
  const value = params.data.value;

  if (value >= 1000) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#5C0011' },
      { offset: 1, color: '#B71D1C' }
    ]);
  } else if (value >= 800) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#B71D1C' },
      { offset: 1, color: '#F75D59' }
    ]);
  } else if (value >= 500) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#F75D59' },
      { offset: 1, color: '#F89880' }
    ]);
  } else if (value >= 300) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#3B5998' },
      { offset: 1, color: '#6495ED' }
    ]);
  } else if (value >= 100) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#6495ED' },
      { offset: 1, color: '#89CFF0' }
    ]);
  } else {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#000000' },
      { offset: 1, color: '#2B3856' }
    ]);
  }
},
          borderRadius: [0, 4, 4, 0]
        },
        emphasis: {
          itemStyle: {
            opacity: 0.8,
            shadowBlur: 20,
            shadowColor: 'rgba(0,144,255,0.5)'
          }
        }
      }
    ]
  };
};

import * as echarts from 'echarts';

// 动态计算Y轴范围的函数
const calculateYAxisRange = (data) => {
  if (!data || data.length === 0) return { min: 0, max: 1000 };
  
  const maxValue = Math.max(...data.filter(val => typeof val === 'number' && !isNaN(val)));
  
  // 重新设计档位，让数据显示在纵坐标70-80%的位置
  if (maxValue <= 1000) {
    return { min: 0, max: 1500 };
  } else if (maxValue <= 3000) {
    return { min: 0, max: 4000 };
  } else if (maxValue <= 8000) {
    return { min: 0, max: 10000 };
  } else if (maxValue <= 20000) {
    return { min: 0, max: 25000 };
  } else if (maxValue <= 40000) {
    return { min: 0, max: 50000 };
  } else if (maxValue <= 80000) {
    return { min: 0, max: 100000 };
  } else if (maxValue <= 200000) {
    return { min: 0, max: 250000 };
  } else if (maxValue <= 400000) {
    return { min: 0, max: 500000 };
  } else if (maxValue <= 800000) {
    return { min: 0, max: 1000000 };
  } else if (maxValue <= 2000000) {
    return { min: 0, max: 2500000 };
  } else {
    // 对于更大的值，设置为最大值的1.3倍，让数据显示在75%左右的位置
    const targetMax = Math.ceil(maxValue * 1.3 / 100000) * 100000;
    return { min: 0, max: targetMax };
  }
};

// 行业分布饼图配置
export const IndustryDistributionOptions = (params) => ({
  tooltip: {
    show: false
  },
  legend: {
    orient: 'vertical',
    left: '2%',
    top: 'middle',  // 垂直居中
    textStyle: {
      color: '#BCDCFF',
      fontSize: 15  // 增加图例字体大小
    },
    icon: 'circle',
    itemWidth: 10,  // 略微增加图例标记的大小
    itemHeight: 10,
    itemGap: 15,  // 增加图例项之间的间距
  },
  series: [
    {
      name: '行业分布',
      type: 'pie',
      radius: ['60%', '98%'],
      center: ['65%', '50%'],  // 将饼图中心点向右移动
      avoidLabelOverlap: false,
      zlevel: 1,
      itemStyle: {
        borderRadius: 4,
        borderWidth: 2,
        borderColor: '#0B1837'
      },
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        fontSize: 14,  // 增加饼图标签字体大小
        color: '#fff'
      },
      labelLine: {
        show: false
      },
      data: (params && params.data) ? params.data : []
    }
  ],
  color: [
    '#37A2DA',
    '#32C5E9',
    '#67E0E3',
    '#9FE6B8',
    '#FFDB5C',
    '#FF9F7F',
    '#FB7293',
    '#E062AE',
    '#E690D1',
    '#E7BCF3'
  ]
});

// 传播态势折线图配置
export const DiffusionTrendOptions = ({ nationalData, globalData, timeData }) => {
  // 计算动态Y轴范围
  const nationalYRange = calculateYAxisRange(nationalData);
  const globalYRange = calculateYAxisRange(globalData);

  // 根据数据点数量动态计算X轴标签间隔
  const dataLength = timeData.length;
  let xAxisInterval;
  if (dataLength <= 10) {
    xAxisInterval = 0; // 显示所有标签
  } else if (dataLength <= 15) {
    xAxisInterval = 1; // 每隔1个显示
  } else if (dataLength <= 31) {
    xAxisInterval = 2; // 每隔2个显示（30天约显示10个标签）
  } else {
    xAxisInterval = Math.floor(dataLength / 10); // 显示约10个标签
  }

  return {
    grid: [
      {
        top: '9%',
        left: '3%',
        right: '4%',
        bottom: '54%',
        containLabel: true
      },
      {
        top: '57%',
        left: '3%',
        right: '4%',
        bottom: '6%',
        containLabel: true
      }
    ],
    title: [
      {
        text: '全国传播态势',
        left: 'center',
        top: '0%',
        textStyle: {
          color: '#BCDCFF',
          fontSize: 18  // 增加标题字体大小
        }
      },
      {
        text: '全球传播态势',
        left: 'center',
        top: '51%',
        textStyle: {
          color: '#BCDCFF',
          fontSize: 18  // 增加标题字体大小
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#283b56'
        }
      }
    },
    xAxis: [
      {
        gridIndex: 0,
        type: 'category',
        boundaryGap: false,
        data: timeData,
        axisLine: {
          lineStyle: {
            color: '#BCDCFF'
          }
        },
        axisLabel: {
          color: '#BCDCFF',
          fontSize: 14,
          interval: xAxisInterval,
          rotate: 0,
          formatter: (value) => {
            return value;
          }
        },
        axisTick: {
          alignWithLabel: true,
          interval: xAxisInterval
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(188, 220, 255, 0.1)',
            type: 'dashed'
          }
        }
      },
      {
        gridIndex: 1,
        type: 'category',
        boundaryGap: false,
        data: timeData,
        axisLine: {
          lineStyle: {
            color: '#BCDCFF'
          }
        },
        axisLabel: {
          color: '#BCDCFF',
          fontSize: 14,
          interval: xAxisInterval,
          rotate: 0,
          formatter: (value) => {
            return value;
          }
        },
        axisTick: {
          alignWithLabel: true,
          interval: xAxisInterval
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(188, 220, 255, 0.1)',
            type: 'dashed'
          }
        }
      }
    ],
    yAxis: [
      {
        gridIndex: 0,
        type: 'value',
        min: nationalYRange.min,
        max: nationalYRange.max,
        splitNumber: 5,
        name: '节点数/个',
        nameTextStyle: {
          color: '#BCDCFF',
          fontSize: 14  // 增加Y轴名称字体大小
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: '#BCDCFF'
          }
        },
        axisLabel: {
          color: '#BCDCFF',
          fontSize: 14,  // 增加Y轴标签字体大小
          formatter: (value) => {
            return value >= 1000 ? `${value/1000}k` : value;
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(188, 220, 255, 0.1)',
            type: 'dashed'
          }
        }
      },
      {
        gridIndex: 1,
        type: 'value',
        min: globalYRange.min,
        max: globalYRange.max,
        splitNumber: 5,
        name: '节点数/个',
        nameTextStyle: {
          color: '#BCDCFF',
          fontSize: 14  // 增加Y轴名称字体大小
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: '#BCDCFF'
          }
        },
        axisLabel: {
          color: '#BCDCFF',
          fontSize: 14,  // 增加Y轴标签字体大小
          formatter: (value) => {
            return value >= 1000 ? `${value/1000}k` : value;
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(188, 220, 255, 0.1)',
            type: 'dashed'
          }
        }
      }
    ],
    series: [
      {
        name: '全国传播',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: nationalData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: false,    // 默认不显示数据点
        itemStyle: {
          color: '#4A90E2'
        },
        emphasis: {
          scale: true,
          focus: 'series',
          itemStyle: {
            color: '#357ABD',
            borderColor: '#FFFFFF',
            borderWidth: 2
          }
        },
        // 只在刻度位置显示数据点
        markPoint: {
          symbol: 'circle',
          symbolSize: 5,
          itemStyle: {
            color: '#4A90E2',
            borderColor: '#FFFFFF',
            borderWidth: 1
          },
          label: {
            show: false  // 不显示数字标签
          },
          data: nationalData.map((value, index) => {
            // 只在每5个数据点（对应刻度）位置显示
            if (index % 5 === 0 || index === nationalData.length - 1) {
              return {
                value: value,
                xAxis: index,
                yAxis: value
              };
            }
            return null;
          }).filter(item => item !== null)
        },
        lineStyle: {
          width: 2,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#4FACFE' },
            { offset: 1, color: '#00F2FE' }
          ])
        },
        areaStyle: {
          opacity: 0.3,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79, 172, 254, 0.8)' },
            { offset: 1, color: 'rgba(0, 242, 254, 0.1)' }
          ])
        }
      },
      {
        name: '全球传播',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: globalData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: false,    // 默认不显示数据点
        itemStyle: {
          color: '#E74C3C'     // 红色数据点
        },
        emphasis: {
          scale: true,
          focus: 'series',
          itemStyle: {
            color: '#C0392B',   // 悬浮时的深红色
            borderColor: '#FFFFFF',
            borderWidth: 2
          }
        },
        // 只在刻度位置显示数据点
        markPoint: {
          symbol: 'circle',
          symbolSize: 5,
          itemStyle: {
            color: '#E74C3C',   // 红色数据点
            borderColor: '#FFFFFF',
            borderWidth: 1
          },
          label: {
            show: false  // 不显示数字标签
          },
          data: globalData.map((value, index) => {
            // 只在每5个数据点（对应刻度）位置显示
            if (index % 5 === 0 || index === globalData.length - 1) {
              return {
                value: value,
                xAxis: index,
                yAxis: value
              };
            }
            return null;
          }).filter(item => item !== null)
        },
        lineStyle: {
          width: 2,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#FF9A9E' },
            { offset: 1, color: '#FECFEF' }
          ])
        },
        areaStyle: {
          opacity: 0.3,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 154, 158, 0.8)' },
            { offset: 1, color: 'rgba(254, 207, 239, 0.1)' }
          ])
        }
      }
    ]
  };
};

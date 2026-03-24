import React, { PureComponent } from 'react';
import Chart from '../../../utils/chart';
import { connect } from 'dva';

class IndustryDistribution extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      renderer: 'canvas'
    };
    this.chartRef = React.createRef();
    this.chart = null;
  }

  componentDidMount() {
    this.initChart();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.industryData !== this.props.industryData ||
        prevProps.selectedNetwork !== this.props.selectedNetwork ||
        prevProps.displayMode !== this.props.displayMode) {
      // 清空图表后再更新，避免残留
      if (this.chart) {
        this.chart.clear();
      }
      this.updateChart();
    }
  }

  componentWillUnmount() {
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
  }

  initChart = () => {
    if (this.chartRef.current) {
      this.chart = this.chartRef.current.getInstance();
      this.updateChart();
    }
  };

  updateChart = () => {
    if (!this.chart) return;

    const { industryData } = this.props;
    
    // 使用真实数据，如果没有数据则显示空图表
    const data = industryData || [];
    
    // 如果没有数据，清除图表并显示提示
    if (!data || data.length === 0) {
      this.chart.setOption({
        backgroundColor: 'transparent',
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#00d4ff',
            fontSize: 16
          }
        },
        series: []  // 清除所有系列
      }, { notMerge: true });  // 完全替换配置
      return;
    }
    
    const total = data.reduce((sum, item) => sum + item.value, 0);

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const { name, value, percent } = params;
          return `<div style="padding: 8px;">
            <div style="font-size: 14px; font-weight: bold; color: #00d4ff; margin-bottom: 6px;">${name}</div>
            <div style="font-size: 13px; color: #fff;">节点数量：<span style="color: #00d4ff; font-weight: bold;">${value}</span></div>
            <div style="font-size: 13px; color: #fff;">占比：<span style="color: #00d4ff; font-weight: bold;">${percent}%</span></div>
          </div>`;
        },
        backgroundColor: 'rgba(0, 15, 35, 0.95)',
        borderColor: '#00d4ff',
        borderWidth: 2,
        padding: 0,
        extraCssText: 'box-shadow: 0 0 15px rgba(0, 212, 255, 0.5); border-radius: 8px;'
      },
      legend: {
        orient: 'vertical',
        right: '0',
        top: 'middle',
        align: 'left',
        textStyle: {
          color: '#fff',
          fontSize: 14,
          fontWeight: 500
        },
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 10,
        formatter: (name) => {
          const item = data.find(d => d.name === name);
          return item ? `${name}  ${item.percentage}%` : name;
        }
      },
      series: [
        {
          name: '行业分布',
          type: 'pie',
          radius: ['40%', '65%'],
          center: ['30%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: 'rgba(0, 0, 0, 0.8)',
            borderWidth: 2,
            shadowBlur: 15,
            shadowColor: 'rgba(0, 212, 255, 0.3)'
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#fff',
              formatter: '{b}\n{c}个\n({d}%)',
              textShadowColor: 'rgba(0, 0, 0, 0.8)',
              textShadowBlur: 5
            },
            itemStyle: {
              shadowBlur: 25,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 212, 255, 0.8)',
              borderWidth: 3,
              borderColor: '#00d4ff'
            },
            scale: true,
            scaleSize: 10
          },
          labelLine: {
            show: false
          },
          data: data.map((item, index) => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: this.getIndustryColor(index)
            }
          }))
        },
        // 中心显示总数
        {
          name: '总计',
          type: 'pie',
          radius: ['0%', '35%'],
          center: ['30%', '50%'],
          silent: true,
          label: {
            show: true,
            position: 'center',
            formatter: () => `{title|总计}\n{value|${total}}\n{unit|节点}`,
            rich: {
              title: {
                fontSize: 16,
                fontWeight: 'bold',
                color: '#00d4ff',
                lineHeight: 25,
                textShadowColor: 'rgba(0, 212, 255, 0.8)',
                textShadowBlur: 10
              },
              value: {
                fontSize: 24,
                fontWeight: 'bold',
                color: '#fff',
                lineHeight: 35,
                fontFamily: 'DINAlternate-Bold, Arial',
                textShadowColor: 'rgba(0, 212, 255, 0.6)',
                textShadowBlur: 8
              },
              unit: {
                fontSize: 14,
                color: '#00d4ff',
                lineHeight: 20
              }
            }
          },
          data: [{
            value: 1,
            itemStyle: {
              color: 'transparent'
            }
          }]
        }
      ]
    };

    this.chart.setOption(option, { notMerge: true });
  };

  // 获取行业对应的颜色 - 科技感渐变色
  getIndustryColor = (index) => {
    const colors = [
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#00d4ff' },
          { offset: 1, color: '#0088cc' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#ff6b6b' },
          { offset: 1, color: '#cc3333' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#4ecdc4' },
          { offset: 1, color: '#2a9d8f' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#45b7d1' },
          { offset: 1, color: '#2980b9' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#96ceb4' },
          { offset: 1, color: '#5a9e7f' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#feca57' },
          { offset: 1, color: '#ee9a00' }
        ]
      },
      {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 1,
        colorStops: [
          { offset: 0, color: '#ff9ff3' },
          { offset: 1, color: '#cc66cc' }
        ]
      }
    ];
    return colors[index % colors.length];
  };

  render() {
    const { renderer } = this.state;

    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      >
        <Chart
          ref={this.chartRef}
          renderer={renderer}
          option={{}}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    );
  }
}

// 从全局状态中获取行业数据
const mapStateToProps = state => ({
  selectedNetwork: state.mapState.selectedNetwork || 'utg_q_008',
  industryData: state.mapState.industryData,
  displayMode: state.mapState.displayMode || 'active'
});

export default connect(mapStateToProps)(IndustryDistribution);

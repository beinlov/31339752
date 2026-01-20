import React, { PureComponent } from 'react';
import { connect } from '../../../utils/ModernConnect';
import Chart from '../../../utils/chart';
import { DiffusionTrendOptions } from './options';
import request from '../../../utils/request';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  GraphicComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// Register the required components
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  GraphicComponent,
  LineChart,
  CanvasRenderer
]);

class DiffusionTrend extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      renderer: 'canvas',
      nationalData: [],
      globalData: [],
      timeData: []
    };
    this.chartInstance = null;
    this.fetchTimer = null;
  }

  componentDidMount() {
    // 初始加载数据
    this.fetchNodeHistory();
    
    // 每5分钟更新一次数据
    this.fetchTimer = setInterval(this.fetchNodeHistory, 5 * 60 * 1000);
  }
  
  componentWillUnmount() {
    if (this.fetchTimer) {
      clearInterval(this.fetchTimer);
    }
  }

  componentDidUpdate(prevProps) {
    // 当选中的僵尸网络发生变化时，重新获取数据
    if (prevProps.selectedNetwork !== this.props.selectedNetwork) {
      this.fetchNodeHistory();
    }

    // 当时间范围发生变化时，重新获取数据
    if (prevProps.timeRange !== this.props.timeRange) {
      this.fetchNodeHistory();
    }
  }

  // 从后端API获取节点数量历史记录
  fetchNodeHistory = async () => {
    const { selectedNetwork } = this.props;
    const { timeRange = '7days' } = this.props;
    
    if (!selectedNetwork) {
      console.warn('No botnet network selected');
      return;
    }

    try {
      // 根据时间粒度设置不同的查询参数
      let queryParams = '';
      switch (timeRange) {
        case '7days':
          queryParams = 'days=7'; // 近7天
          break;
        case '30days':
          queryParams = 'days=30'; // 近30天
          break;
        default:
          queryParams = 'days=7';
      }
      
      const response = await request(
        `http://localhost:8000/api/node-count-history/${selectedNetwork}?${queryParams}`
      );
      
      if (response && Array.isArray(response)) {
        console.log('API返回数据:', response);
        const timeData = response.map(item => item.timestamp);
        const nationalData = response.map(item => item.china_count);
        const globalData = response.map(item => item.global_count);
        
        console.log('时间数据:', timeData);
        console.log('全国数据:', nationalData);
        console.log('全球数据:', globalData);
        
        this.setState({
          timeData,
          nationalData,
          globalData
        });
      } else {
        console.warn('API返回数据格式错误:', response);
        // 即使数据格式错误，也设置空数组以显示空图表
        this.setState({
          timeData: [],
          nationalData: [],
          globalData: []
        });
      }
    } catch (error) {
      console.error('获取节点历史数据失败:', error);
      // 即使请求失败，也设置空数组以显示空图表
      this.setState({
        timeData: [],
        nationalData: [],
        globalData: []
      });
    }
  };

  render() {
    const { renderer, nationalData, globalData, timeData } = this.state;
    
    const option = DiffusionTrendOptions({
      nationalData,
      globalData,
      timeData
    });

    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <Chart
          renderer={renderer}
          option={option}
          ref={chart => this.chartInstance = chart}
        />
      </div>
    );
  }
}

const mapStateToProps = ({ mapState }) => ({
  selectedNetwork: mapState.selectedNetwork,
  botnetData: mapState.botnetData
});

export default connect(mapStateToProps)(DiffusionTrend); 
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
  }

  // 从后端API获取节点数量历史记录
  fetchNodeHistory = async () => {
    const { selectedNetwork } = this.props;
    
    if (!selectedNetwork) {
      console.warn('No botnet network selected');
      return;
    }

    try {
      const response = await request(
        `http://localhost:8000/api/node-count-history/${selectedNetwork}?hours=2`
      );
      
      if (response && Array.isArray(response)) {
        const timeData = response.map(item => item.timestamp);
        const nationalData = response.map(item => item.china_count);
        const globalData = response.map(item => item.global_count);
        
        this.setState({
          timeData,
          nationalData,
          globalData
        });
      }
    } catch (error) {
      console.error('获取节点历史数据失败:', error);
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
      <div style={{ width: '100%', height: '100%' }}>
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
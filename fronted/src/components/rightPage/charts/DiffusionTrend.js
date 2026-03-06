import React, { PureComponent } from 'react';
import { connect } from '../../../utils/ModernConnect';
import Chart from '../../../utils/chart';
import { DiffusionTrendOptions } from './options';
import request from '../../../utils/request';
import { getApiUrl } from '../../../config/api';
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
      timeData: [],
      realtimeData: {
        nationalData: [],
        globalData: [],
        timeData: []
      }
    };
    this.chartInstance = null;
    this.fetchTimer = null;
    this.realtimeTimer = null;
  }

  componentDidMount() {
    // 初始加载数据
    this.fetchNodeHistory();
    
    // 每5分钟更新一次数据
    this.fetchTimer = setInterval(this.fetchNodeHistory, 5 * 60 * 1000);
    
    // 如果是实时模式，启动实时数据更新
    if (this.props.timeRange === 'realtime') {
      this.startRealtimeUpdates();
    }
  }
  
  componentWillUnmount() {
    if (this.fetchTimer) {
      clearInterval(this.fetchTimer);
    }
    if (this.realtimeTimer) {
      clearInterval(this.realtimeTimer);
    }
  }

  componentDidUpdate(prevProps) {
    // 当选中的僵尸网络发生变化时，重新获取数据
    if (prevProps.selectedNetwork !== this.props.selectedNetwork) {
      this.fetchNodeHistory();
    }

    // 当时间范围发生变化时，重新获取数据
    if (prevProps.timeRange !== this.props.timeRange) {
      if (this.props.timeRange === 'realtime') {
        this.startRealtimeUpdates();
      } else {
        this.stopRealtimeUpdates();
        this.fetchNodeHistory();
      }
    }

    // 当显示模式发生变化时，重新获取数据
    if (prevProps.displayMode !== this.props.displayMode) {
      this.fetchNodeHistory();
    }
  }

  // 从后端API获取节点数量历史记录
  fetchNodeHistory = async () => {
    const { selectedNetwork, displayMode } = this.props;
    const { timeRange = '7days' } = this.props;
    
    if (!selectedNetwork) {
      console.warn('No botnet network selected');
      return;
    }

    try {
      // 如果是实时模式，使用实时数据
      if (timeRange === 'realtime') {
        this.updateRealtimeData();
        return;
      }

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
        getApiUrl(`/api/node-count-history/${selectedNetwork}?${queryParams}`)
      );
      
      if (response && Array.isArray(response)) {
        console.log('API返回数据:', response);
        const timeData = response.map(item => item.timestamp);
        
        // 根据displayMode选择使用哪个数据字段
        let nationalData, globalData;
        if (displayMode === 'cleaned') {
          nationalData = response.map(item => item.china_cleaned);
          globalData = response.map(item => item.global_cleaned);
          console.log('清理模式 - 全国数据:', nationalData);
          console.log('清理模式 - 全球数据:', globalData);
        } else {
          nationalData = response.map(item => item.china_active);
          globalData = response.map(item => item.global_active);
          console.log('活跃模式 - 全国数据:', nationalData);
          console.log('活跃模式 - 全球数据:', globalData);
        }
        
        console.log('时间数据:', timeData);
        
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

  // 启动实时数据更新
  startRealtimeUpdates = () => {
    // 立即更新一次
    this.updateRealtimeData();
    
    // 每5秒更新一次实时数据
    this.realtimeTimer = setInterval(() => {
      this.updateRealtimeData();
    }, 5000);
  };

  // 停止实时数据更新
  stopRealtimeUpdates = () => {
    if (this.realtimeTimer) {
      clearInterval(this.realtimeTimer);
      this.realtimeTimer = null;
    }
  };

  // 更新实时数据
  updateRealtimeData = () => {
    const { botnetData, displayMode } = this.props;
    
    if (!botnetData) {
      return;
    }

    // 获取当前时间，格式为 HH:mm:ss
    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    // 根据displayMode获取对应的数据
    const nationalValue = displayMode === 'cleaned' ? botnetData.china_cleaned : botnetData.china_active;
    const globalValue = displayMode === 'cleaned' ? botnetData.global_cleaned : botnetData.global_active;

    this.setState(prevState => {
      const newRealtimeData = { ...prevState.realtimeData };
      
      // 添加新的数据点
      newRealtimeData.timeData.push(timeString);
      newRealtimeData.nationalData.push(nationalValue || 0);
      newRealtimeData.globalData.push(globalValue || 0);
      
      // 保持最近30个数据点（2.5分钟的数据）
      if (newRealtimeData.timeData.length > 30) {
        newRealtimeData.timeData = newRealtimeData.timeData.slice(-30);
        newRealtimeData.nationalData = newRealtimeData.nationalData.slice(-30);
        newRealtimeData.globalData = newRealtimeData.globalData.slice(-30);
      }
      
      return {
        realtimeData: newRealtimeData,
        // 在实时模式下，使用实时数据更新主数据
        timeData: newRealtimeData.timeData,
        nationalData: newRealtimeData.nationalData,
        globalData: newRealtimeData.globalData
      };
    });
  };

  render() {
    const { renderer, nationalData, globalData, timeData } = this.state;
    const { displayMode } = this.props;
    
    const option = DiffusionTrendOptions({
      nationalData,
      globalData,
      timeData,
      displayMode
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
  botnetData: mapState.botnetData,
  displayMode: mapState.displayMode
});

export default connect(mapStateToProps)(DiffusionTrend); 
import React, { PureComponent } from 'react';
import { connect } from '../../../utils/ModernConnect';
import Chart from '../../../utils/chart';
import { DiffusionTrendOptions } from './options';
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
    this.timer = null;
  }

  componentDidMount() {
    // 初始化时间数据
    this.updateTimeData();
    
    // 每秒更新时间数据
    this.timer = setInterval(this.updateTimeData, 1000);
  }

  componentWillUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  componentDidUpdate(prevProps) {
    // 当botnetData发生变化时，更新图表数据
    if (prevProps.botnetData !== this.props.botnetData) {
      this.updateChartData();
    }
  }

  // 更新时间数据
  updateTimeData = () => {
    // 生成最近25秒的实时时间数据
    const now = new Date();
    const newTimeData = Array.from({ length: 25 }, (_, i) => {
      const time = new Date(now.getTime() - (24 - i) * 1000);
      return time.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit', 
        second: '2-digit'
      });
    });

    this.setState({ timeData: newTimeData }, () => {
      // 同时更新图表数据
      this.updateChartData();
    });
  };

  // 更新图表数据
  updateChartData = () => {
    const { botnetData } = this.props;
    
    if (!botnetData) return;

    this.setState(prevState => {
      // 更新数据数组，保持最近25个数据点
      const newNationalData = [...(prevState.nationalData || []), botnetData.china_amount].slice(-25);
      const newGlobalData = [...(prevState.globalData || []), botnetData.global_amount].slice(-25);

      return {
        nationalData: newNationalData,
        globalData: newGlobalData
      };
    });
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
import React, { PureComponent } from 'react';
import Chart from '../../../utils/chart';
import { worldMapOptions } from './options';
import * as echarts from 'echarts';
import { RetweetOutlined } from '@ant-design/icons';
import { connect } from 'dva';
import { registerMap } from 'echarts/core';
import worldJson from '../../../world.zh.json';

// 注册世界地图数据
registerMap('world', worldJson);

class WorldMap extends PureComponent {
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
    if (prevProps.selectedNetwork !== this.props.selectedNetwork ||
        prevProps.worldData !== this.props.worldData ||
        prevProps.mapData !== this.props.mapData ||
        prevProps.isLeftPage !== this.props.isLeftPage) {
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

    const { worldData, selectedNetwork, mapData, isLeftPage } = this.props;
    if (!worldData) return;

    const networkToUse = selectedNetwork || 'ramnit';
    const countryData = worldData[networkToUse] || [];

    const option = worldMapOptions({
      ...mapData,
      countryData
    }, isLeftPage !== false);

    this.chart.setOption(option);
  };

  render() {
    const { renderer } = this.state;
    const { onSwitchMap, isLeftPage = true } = this.props;

    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          justifyContent: 'center',
          position: 'relative'
        }}
      >
        <div
          style={{
            position: 'absolute',
            right: '10px',
            top: '7%',
            zIndex: 999,
            cursor: 'pointer',
            background: 'rgba(0,0,0,0.3)',
            padding: '8px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            color: '#fff',
            transition: 'all 0.3s ease',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            backdropFilter: 'blur(4px)',
            border: '1px solid rgba(255,255,255,0.1)'
          }}
          onClick={onSwitchMap}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0,0,0,0.5)';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0,0,0,0.3)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          <RetweetOutlined style={{
            fontSize: '20px',
            transition: 'transform 0.3s ease',
          }} />
        </div>
        <Chart
          ref={this.chartRef}
          renderer={renderer}
          option={worldMapOptions({}, isLeftPage)}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    );
  }
}

// 从全局状态中获取选择的网络类型和世界数据
const mapStateToProps = state => ({
  selectedNetwork: state.mapState.selectedNetwork || 'ramnit',
  worldData: state.mapState.worldData
});

export default connect(mapStateToProps)(WorldMap);

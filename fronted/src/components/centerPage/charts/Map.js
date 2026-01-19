import React, { PureComponent } from 'react';
import { connect } from 'dva';
import Chart from '../../../utils/chart';
import { mapOptions, provinceMap, provinceNameMap } from './options';
import { RetweetOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';
import request from '../../../utils/request';
import { registerMap } from 'echarts/core';
import chinaJson from "../../../china.json";

// 注册中国地图数据
registerMap('china', chinaJson);

// 规范化省份名称
const normalizeProvince = (rawName) => {
  if (!rawName) return '';
  let name = rawName.trim();
  name = name.replace(/^中国/, '');
  const match = name.match(/(壮族自治区|回族自治区|维吾尔自治区|特别行政区|自治区|省|市)/);
  if (match && match.index > 0) {
    name = name.slice(0, match.index);
  }
  return name;
};

// 动态加载省份地图数据
const loadProvinceMap = async (provinceName) => {
  try {
    if (provinceName === 'china') return 'china';

    // 使用 normalizeProvince 规范化省份名称
    const shortName = normalizeProvince(provinceName);

    // 获取省份的地图文件名
    const mapCode = provinceMap[shortName];
    if (!mapCode) {
      console.error('未找到省份对应的地图文件:', provinceName);
      return null;
    }

    // 如果地图已经注册过，直接返回shortName
    if (echarts.getMap(shortName)) return shortName;

    // 动态导入省份地图数据
    const mapData = await import(`../../../province/${mapCode}.json`);
    if (!mapData || !mapData.default) {
      console.error(`省份地图数据无效 ${shortName}`);
      return null;
    }

    echarts.registerMap(shortName, mapData.default || mapData);
    return shortName;  // 返回处理后的省份名称

  } catch (error) {
    console.error('加载省份地图失败:', error);
    return null;
  }
};

// 获取省份颜色的函数，使用相对比例
const getProvinceColorByRatio = (value, maxValue) => {
  // 使用相对比例而不是绝对值，颜色从深到浅
  const ratio = maxValue > 0 ? value / maxValue : 0;

  if (ratio >= 0.8) return '#5C0011';      // 深红色 - 最高等级
  if (ratio >= 0.6) return '#B71D1C';      // 红色
  if (ratio >= 0.4) return '#F75D59';      // 浅红色
  if (ratio >= 0.2) return '#3B5998';      // 蓝色
  if (ratio >= 0.1) return '#6495ED';      // 浅蓝色
  // 确保所有非零值都有颜色
  return value > 0 ? '#6495ED' : '#1D1E4C';  // 对于非零但很小的值使用浅蓝色，零值使用深蓝色
};

class Map extends PureComponent {
  state = {
    currentProvinceColor: null,
    isShowingFlyLines: false
  };

  constructor(props) {
    super(props);
    this.chartRef = React.createRef();
    this.chart = null;
    this.flyLinesTimer = null;
  }

  componentDidMount() {
    this.initChart();
    window.addEventListener('startCleaning', this.handleStartCleaning);
  }

  componentDidUpdate(prevProps, prevState) {
    this.handleMapTypeChange(prevProps);
    this.handleFlyLinesChange(prevProps);
    this.handleDataChange(prevProps);
  }

  componentWillUnmount() {
    if (this.chart) {
      this.chart.off('click', this.handleMapClick);
      this.chart.dispose();
      this.chart = null;
    }
    window.removeEventListener('startCleaning', this.handleStartCleaning);
    if (this.flyLinesTimer) {
      clearTimeout(this.flyLinesTimer);
    }
  }

  initChart = () => {
    if (this.chartRef.current) {
      this.chart = this.chartRef.current.getInstance();
      if (this.chart) {
        this.chart.on('click', this.handleMapClick);
        this.updateChart();
      }
    }
  };

  handleMapTypeChange = (prevProps) => {
    if (prevProps.currentMap !== this.props.currentMap && this.props.currentMap !== 'china') {
      const color = this.getProvinceColor(this.props.currentMap);
      if (color !== this.state.currentProvinceColor) {
        this.setState({ currentProvinceColor: color }, this.updateChart);
      }
    }
  };

  handleFlyLinesChange = (prevProps) => {
    if (prevProps.showFlyLines !== this.props.showFlyLines && this.props.showFlyLines) {
      this.showFlyLines();
    }
  };

  handleDataChange = (prevProps) => {
    if (prevProps.selectedNetwork !== this.props.selectedNetwork ||
        prevProps.provinceData !== this.props.provinceData ||
        prevProps.mapData !== this.props.mapData ||
        prevProps.isLeftPage !== this.props.isLeftPage) {
      this.updateChart();
    }
  };

  // 更新图表
  updateChart = () => {
    if (!this.chart) return;

    const { mapData, currentMap, isLeftPage, cityData } = this.props;
    const { currentProvinceColor, isShowingFlyLines } = this.state;
    const provinceData = this.getProvinceDataForCurrentNetwork();

    const option = mapOptions({
      ...mapData,
      provinceData,
      currentProvinceColor,
      showLines: isShowingFlyLines,
      cityData: currentMap !== 'china' ? (cityData && cityData[this.props.selectedNetwork]) : null
    }, currentMap, isLeftPage || false);

    this.chart.setOption(option);
  };

  // 获取当前选择网络的省份数据
  getProvinceDataForCurrentNetwork = () => {
    const { provinceData, selectedNetwork } = this.props;
    if (!provinceData) return null;

    const networkToUse = selectedNetwork || 'ramnit';
    return provinceData[networkToUse];
  }

  handleMapClick = async (params) => {
    const { dispatch, currentMap } = this.props;

    if (currentMap === 'china') {
      try {
        // 先加载地图数据
        const mapShortName = await loadProvinceMap(params.name);
        if (!mapShortName) {
          console.error('加载省份地图失败');
          return;
        }

        // 获取省份颜色
        const provinceColor = this.getProvinceColor(params.name);

        // 切换地图和获取数据
        dispatch({
          type: 'mapState/changeMap',
          payload: mapShortName
        });

        // 设置省份颜色
        this.setState({ currentProvinceColor: provinceColor });

      } catch (error) {
        console.error('切换省份地图失败:', error);
      }
    } else {
      // 返回中国地图
      dispatch({
        type: 'mapState/changeMap',
        payload: 'china'
      });

      this.setState({
        currentProvinceColor: null
      });
    }
  }

  // 添加获取省份颜色的方法
  getProvinceColor = (provinceName) => {
    const provinceData = this.getProvinceDataForCurrentNetwork();
    if (!provinceData) return null;

    // 规范化省份名称以便匹配
    const normalizedProvinceName = normalizeProvince(provinceName);
    
    // 找到对应省份的数据（支持多种匹配方式）
    const province = provinceData.find(p => {
      const normalizedP = normalizeProvince(p.province);
      return normalizedP === normalizedProvinceName || 
             p.province === provinceName ||
             provinceNameMap[p.province] === provinceName;
    });
    if (!province) return null;

    // 计算最大值用于相对比例
    const maxValue = Math.max(...provinceData.map(p => p.amount));

    // 使用相对比例来确定颜色，确保非零值有颜色
    const value = province.amount;
    return value > 0 ? getProvinceColorByRatio(value, maxValue) : '#1D1E4C';
  }

  handleStartCleaning = () => {
    // 设置飞线显示状态
    this.setState({ isShowingFlyLines: true }, this.updateChart);
  };

  // 修改 showFlyLines 方法
  showFlyLines = () => {
    // 清除之前的定时器
    if (this.flyLinesTimer) {
      clearTimeout(this.flyLinesTimer);
    }

    // 设置飞线显示状态
    this.setState({ isShowingFlyLines: true }, this.updateChart);

    // 30秒后隐藏飞线
    this.flyLinesTimer = setTimeout(() => {
      this.setState({ isShowingFlyLines: false }, this.updateChart);
    }, 50000);  // 修改为50秒
  };

  render() {
    const { mapData, onSwitchMap, currentMap, isLeftPage } = this.props;
    const { currentProvinceColor, isShowingFlyLines } = this.state;
    const provinceData = this.getProvinceDataForCurrentNetwork();

    const combinedMapData = {
      ...mapData,
      provinceData,
      currentProvinceColor,
      showLines: isShowingFlyLines,
    };

    return (
      <div style={{                       //整体地图控件
        width: '100%',
        height: '100%',
        position: 'relative',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: '-0.4rem',  // 调整整体上移
      }}>
        <div
          style={{
            position: 'absolute',
            right: '10px',
            top: '10%',
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
          renderer="canvas"
          option={mapOptions(combinedMapData, currentMap, isLeftPage || false)}
          style={{
            width: '100%',  // 改为100%以充满容器
            height: '100%',
            marginTop: '5rem'  // 增加顶部边距使地图下移
          }}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  currentMap: state.mapState.currentMap,
  showFlyLines: state.mapState.showFlyLines,
  selectedNetwork: state.mapState.selectedNetwork,
  provinceData: state.mapState.provinceData,
  cityData: state.mapState.cityData  // Add cityData from state
});

export default connect(mapStateToProps)(Map);

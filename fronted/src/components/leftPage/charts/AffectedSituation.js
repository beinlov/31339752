import React, { PureComponent } from 'react';
import Chart from '../../../utils/chart';
import { affectedOptions } from './options';
import request from '../../../utils/request';
import { connect } from 'dva';  // 添加 connect 以获取全局状态

class AffectedSituation extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      renderer: 'canvas',
      affectedData: null,
      isWorldView: false
    };
    this.chartRef = React.createRef();
    this.pollingInterval = null;
  }

  componentDidMount() {
    this.updateChartData();
    this.pollingInterval = setInterval(() => {
      this.updateChartData();
    }, 30000);
  }

  componentDidUpdate(prevProps) {
    if (
      prevProps.selectedNetwork !== this.props.selectedNetwork ||
      prevProps.isSwapped !== this.props.isSwapped ||
      prevProps.currentMap !== this.props.currentMap ||
      prevProps.provinceData !== this.props.provinceData ||
      prevProps.cityData !== this.props.cityData
    ) {
      this.updateChartData();
    }
  }

  componentWillUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  }

  updateChartData = () => {
    const { selectedNetwork, isSwapped, currentMap, provinceData, cityData } = this.props;

    // 优先判断：如果是全球视图，显示国家数据
    if (isSwapped) {
      this.fetchCountryData(selectedNetwork);
    }
    // 如果有当前选中的省份（非中国地图且非全球视图），显示城市数据
    // 但香港和澳门只显示整体数据，不显示城市详细数据
    else if (currentMap !== 'china' && cityData && !isSwapped) {
      // 香港和澳门特殊处理：只显示整体数据
      if (currentMap === '香港' || currentMap === '澳门') {
        // 从provinceData中获取香港/澳门的整体数据
        if (provinceData) {
          const networkData = provinceData[selectedNetwork] || [];
          const currentProvinceData = networkData.find(item => 
            item.province === currentMap || 
            item.province === `${currentMap}特别行政区`
          );
          
          if (currentProvinceData) {
            this.setState({
              affectedData: {
                provinces: [currentMap],
                data: [{
                  value: currentProvinceData.amount,
                  percentage: '100.0'
                }],
                isWorldView: false,
                isCityView: false
              }
            });
          }
        }
      } else {
        // 其他省份显示城市详细数据
        const currentCityData = cityData[selectedNetwork] || [];
        const sortedCityData = [...currentCityData]
          .sort((a, b) => b.amount - a.amount)
          .slice(0, 15);

        const total = currentCityData.reduce((sum, item) => sum + (item.amount || 0), 0);

        const cities = sortedCityData.map(item => item.city);
        const data = sortedCityData.map(item => ({
          value: item.amount || 0,
          percentage: ((item.amount || 0) / (total || 1) * 100).toFixed(1)
        }));

        this.setState({
          affectedData: {
            provinces: cities,
            data,
            isWorldView: false,
            isCityView: true
          }
        });
      }
    }
    // 默认显示省份数据（中国地图）
    else if (provinceData) {
      const networkData = provinceData[selectedNetwork] || [];
      const sortedNetworkData = [...networkData]
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 15);

      const total = networkData.reduce((sum, item) => sum + item.amount, 0);

      const provinces = sortedNetworkData.map(item => item.province);
      const data = sortedNetworkData.map(item => ({
        value: item.amount,
        percentage: ((item.amount / total) * 100).toFixed(1)
      }));

      this.setState({
        affectedData: {
          provinces,
          data,
          isWorldView: false,
          isCityView: false
        }
      });
    }
  };

  fetchCountryData = async (botnetType) => {
    try {
      const network = botnetType || this.props.selectedNetwork;
      const url = `http://localhost:8000/api/world-amounts?botnet_type=${network}`;
      const response = await request(url);
      
      if (response) {
        // 处理全球国家数据
        const countryData = response[network] || [];
        
        // 按数量降序排列，取前15个
        const sortedCountryData = [...countryData]
          .sort((a, b) => b.amount - a.amount)
          .slice(0, 15);
        
        const total = countryData.reduce((sum, item) => sum + (item.amount || 0), 0);
        
        const countries = sortedCountryData.map(item => item.country);
        const data = sortedCountryData.map(item => ({
          value: item.amount || 0,
          percentage: ((item.amount || 0) / (total || 1) * 100).toFixed(1)
        }));
        
        this.setState({
          affectedData: {
            provinces: countries,  // 使用 provinces 字段存储国家名
            data,
            isWorldView: true,
            isCityView: false
          }
        });
      }
    } catch (error) {
      console.error('获取国家数据失败:', error);
    }
  };

  render() {
    const { renderer, affectedData } = this.state;
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        position: 'relative'
      }}>
        {affectedData ? (
          <Chart
            ref={this.chartRef}
            renderer={renderer}
            option={affectedOptions(affectedData)}
            style={{ width: '100%', height: '100%' }}
          />
        ) : ''}
      </div>
    );
  }
}

const mapStateToProps = state => ({
  selectedNetwork: state.mapState.selectedNetwork,
  isSwapped: state.mapPosition.isSwapped,
  currentMap: state.mapState.currentMap,
  provinceData: state.mapState.provinceData,
  cityData: state.mapState.cityData
});

export default connect(mapStateToProps)(AffectedSituation);

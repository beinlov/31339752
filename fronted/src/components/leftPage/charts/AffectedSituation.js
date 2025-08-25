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

    // 如果有当前选中的省份，显示城市数据
    if (currentMap !== 'china' && cityData) {
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
    // 如果是世界视图，显示国家数据
    else if (isSwapped) {
      this.fetchCountryData(selectedNetwork);
    }
    // 默认显示省份数据
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
      const network = botnetType || selectedNetwork;
      const url = `http://localhost:8000/api/world-amounts?botnet_type=${network}`;
      const response = await request(url);
      if (response) {
        this.setState({
          allCountryData: response
        }, this.updateChartData);
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

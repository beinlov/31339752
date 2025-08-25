import React, { PureComponent } from 'react';
import { CenterPage, MapContainer, CenterBottom } from './style';
import Map from './charts/Map';
import WorldMap from '../leftPage/charts/WorldMap';
import Takeover from './charts/Takeover';
import ActivityStream from './charts/ActivityStream';
import NetworkTitle from './charts/NetworkTitle';
import { Select } from 'antd';
import { ModuleTitle } from '../../style/globalStyledSet';
import { connect } from '../../utils/ModernConnect';
import axios from 'axios';

const { Option } = Select;

class index extends PureComponent {
  state = {
    selectedNetwork: 'ramnit',  // 默认选择
    networkTypes: [],  // 存储从后端获取的网络类型
    loading: true
  };



  componentDidMount() {
    this.fetchNetworkTypes();
  }

  fetchNetworkTypes = async () => {
    try {
      const response = await axios.get('/api/botnet-types');
      if (response.data.status === 'success') {
        this.setState({
          networkTypes: response.data.data,
          loading: false
        });
      }
      this.handleNetworkChange("ramnit")
    } catch (error) {
      console.error('Error fetching network types:', error);
      this.setState({ loading: false });
    }
  };

  handleNetworkChange = (value) => {
    const { dispatch } = this.props;

    this.setState({
      selectedNetwork: value
    });

    // 更新全局状态
    dispatch({
      type: 'mapState/setSelectedNetwork',
      payload: value
    });
  };

  render() {
    const {
      detailsList,
      mapData,
      userSitua,
      worldMapData,
      isSwapped,
      onSwitchMap
    } = this.props;

    const { networkTypes, loading } = this.state;

    const MapComponent = isSwapped ? WorldMap : Map;
    const mapDataToUse = isSwapped ? worldMapData : mapData;

    return (
      <CenterPage>
        {/* 固定的僵尸网络类型选择下拉框 */}
        <div
          style={{
            position: 'absolute',
            left: '0%',
            top: '3%',
            zIndex: 1000,
            background: 'rgba(15, 19, 37, 0)',
            padding: '10px',
            borderRadius: '4px',
            minWidth: '240px'
          }}
        >
          <ModuleTitle className='module-title' style={{ marginBottom: '5px' }}>
            <i className='iconfont'>&#xe7fd;</i>
            <span>僵尸网络类型</span>
          </ModuleTitle>

          <Select
            value={this.state.selectedNetwork}
            onChange={this.handleNetworkChange}
            loading={loading}
            style={{
              width: '180px',
            }}
            dropdownStyle={{
              backgroundColor: '#0f1325',
              borderRadius: '4px',
              border: '1px solid rgba(147, 235, 248, 0.3)'
            }}
          >
            {networkTypes.map(network => (
              <Option
                key={network.name}
                value={network.name}
                style={{
                  color: '#BCDCFF',
                  backgroundColor: '#0f1325'
                }}
              >
                {network.display_name}
              </Option>
            ))}
          </Select>
        </div>

        <MapContainer>
          <NetworkTitle selectedNetwork={this.state.selectedNetwork} />
          <MapComponent
            mapData={mapDataToUse}
            onSwitchMap={onSwitchMap}
            isLeftPage={false}
            selectedNetwork={this.state.selectedNetwork}
          />
          <div style={{
            position: 'absolute',
            left: '90%',
            top: '50%',
            zIndex: 999,
          }}>
            <Takeover />
          </div>
        </MapContainer>

        <CenterBottom>
          <div className="user-situation">
            <ActivityStream userSitua={userSitua} />
          </div>
        </CenterBottom>
      </CenterPage>
    );
  }
}

const mapStateToProps = state => ({
  detailsList: state.centerPage.detailsList,
  mapData: state.centerPage.mapData,
  userSitua: state.centerPage.userSitua,
  worldMapData: state.leftPage.worldMapData,
  isSwapped: state.mapPosition.isSwapped,
});

export default connect(mapStateToProps)(index);

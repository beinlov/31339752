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
import styled, { createGlobalStyle } from 'styled-components';

const { Option } = Select;

// 科技风格下拉框容器
const StyledSelectWrapper = styled.div`
  .ant-select {
    width: 100%;
    
    .ant-select-selector {
      background: linear-gradient(135deg, rgba(26, 35, 126, 0.3) 0%, rgba(15, 19, 37, 0.5) 100%) !important;
      border: 1px solid rgba(91, 192, 222, 0.5) !important;
      border-radius: 4px !important;
      box-shadow: 0 0 15px rgba(91, 192, 222, 0.2), inset 0 0 10px rgba(91, 192, 222, 0.1) !important;
      backdrop-filter: blur(5px);
      transition: all 0.3s ease;
      height: 36px !important;
      padding: 0 12px !important;
      
      &:hover {
        border-color: rgba(91, 192, 222, 0.8) !important;
        box-shadow: 0 0 20px rgba(91, 192, 222, 0.4), inset 0 0 15px rgba(91, 192, 222, 0.15) !important;
      }
    }
    
    &.ant-select-focused .ant-select-selector {
      border-color: rgba(91, 192, 222, 1) !important;
      box-shadow: 0 0 25px rgba(91, 192, 222, 0.6), inset 0 0 20px rgba(91, 192, 222, 0.2) !important;
    }
    
    .ant-select-selection-item {
      color: #BCDCFF !important;
      font-weight: 500;
      text-shadow: 0 0 5px rgba(188, 220, 255, 0.5);
      line-height: 34px !important;
    }
    
    .ant-select-selection-placeholder {
      color: rgba(188, 220, 255, 0.5) !important;
      line-height: 34px !important;
    }
    
    .ant-select-arrow {
      color: rgba(91, 192, 222, 0.8) !important;
      
      .anticon {
        transition: all 0.3s ease;
      }
    }
    
    &.ant-select-open .ant-select-arrow .anticon {
      transform: rotate(180deg);
    }
  }
`;

// 全局样式注入（用于下拉菜单）- 使用createGlobalStyle确保样式应用到Portal
const GlobalSelectStyle = createGlobalStyle`
  .tech-select-dropdown {
    background: linear-gradient(135deg, rgba(10, 15, 30, 0.98) 0%, rgba(20, 25, 45, 0.95) 100%) !important;
    border: 1px solid rgba(91, 192, 222, 0.6) !important;
    border-radius: 6px !important;
    box-shadow: 
      0 0 30px rgba(91, 192, 222, 0.5), 
      0 8px 32px rgba(0, 0, 0, 0.6),
      inset 0 0 20px rgba(91, 192, 222, 0.1) !important;
    backdrop-filter: blur(15px);
    padding: 6px !important;
    overflow: hidden;
    position: relative;
  }
  
  .tech-select-dropdown .ant-select-item {
    color: #E0F0FF !important;
    background: transparent !important;
    padding: 10px 16px !important;
    margin: 2px 4px !important;
    border-radius: 4px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    font-size: 14px !important;
    font-weight: 500;
  }
  
  /* 左侧渐变指示条 */
  .tech-select-dropdown .ant-select-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 4px;
    height: 0;
    background: linear-gradient(180deg, #5bc0de, #3498db);
    transition: height 0.3s ease;
    border-radius: 0 2px 2px 0;
  }
  
  /* 悬停背景光效 */
  .tech-select-dropdown .ant-select-item::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: radial-gradient(circle, rgba(91, 192, 222, 0.3) 0%, transparent 70%);
    transform: translate(-50%, -50%);
    transition: all 0.4s ease;
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
  }
  
  .tech-select-dropdown .ant-select-item:hover {
    background: linear-gradient(90deg, rgba(91, 192, 222, 0.25) 0%, rgba(91, 192, 222, 0.08) 100%) !important;
    color: #ffffff !important;
    text-shadow: 0 0 10px rgba(188, 220, 255, 0.8);
    transform: translateX(4px);
  }
  
  .tech-select-dropdown .ant-select-item:hover::before {
    height: 100%;
    box-shadow: 0 0 10px rgba(91, 192, 222, 0.6);
  }
  
  .tech-select-dropdown .ant-select-item:hover::after {
    width: 200%;
    height: 200%;
  }
  
  .tech-select-dropdown .ant-select-item-option-selected {
    background: linear-gradient(90deg, rgba(91, 192, 222, 0.35) 0%, rgba(91, 192, 222, 0.15) 100%) !important;
    color: #ffffff !important;
    font-weight: 700;
    text-shadow: 0 0 12px rgba(188, 220, 255, 1);
    border: 1px solid rgba(91, 192, 222, 0.4);
  }
  
  .tech-select-dropdown .ant-select-item-option-selected::before {
    height: 100%;
    width: 4px;
    background: linear-gradient(180deg, #00ff88, #00ccff);
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.8);
  }
  
  .tech-select-dropdown .ant-select-item-option-selected::after {
    content: '✓';
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    width: auto;
    height: auto;
    background: none;
    color: #00ff88;
    font-size: 16px;
    font-weight: bold;
    text-shadow: 0 0 12px rgba(0, 255, 136, 1);
    z-index: 1;
  }
  
  .tech-select-dropdown .ant-select-item-option-selected:hover {
    background: linear-gradient(90deg, rgba(91, 192, 222, 0.45) 0%, rgba(91, 192, 222, 0.2) 100%) !important;
  }
  
  /* 禁用状态 */
  .tech-select-dropdown .ant-select-item-option-disabled {
    color: rgba(188, 220, 255, 0.3) !important;
    cursor: not-allowed;
  }
  
  .tech-select-dropdown .ant-select-item-option-disabled:hover {
    background: transparent !important;
    transform: none;
  }
  
  /* 滚动条样式 */
  .tech-select-dropdown .rc-virtual-list-scrollbar {
    width: 8px !important;
    background: rgba(15, 19, 37, 0.5);
    border-radius: 4px;
  }
  
  .tech-select-dropdown .rc-virtual-list-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(91, 192, 222, 0.6), rgba(91, 192, 222, 0.4)) !important;
    border-radius: 4px !important;
    border: 1px solid rgba(91, 192, 222, 0.3);
    box-shadow: 0 0 10px rgba(91, 192, 222, 0.4);
    transition: all 0.3s ease;
  }
  
  .tech-select-dropdown .rc-virtual-list-scrollbar-thumb:hover {
    background: linear-gradient(180deg, rgba(91, 192, 222, 0.9), rgba(91, 192, 222, 0.7)) !important;
    box-shadow: 0 0 15px rgba(91, 192, 222, 0.6);
  }
  
  /* 空状态 */
  .tech-select-dropdown .ant-empty {
    color: rgba(188, 220, 255, 0.5);
  }
  
  .tech-select-dropdown .ant-empty-image svg {
    fill: rgba(91, 192, 222, 0.3);
  }
`;

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
      const response = await axios.get('http://localhost:8000/api/botnet-types');
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

          <GlobalSelectStyle />
          <StyledSelectWrapper>
            <Select
              value={this.state.selectedNetwork}
              onChange={this.handleNetworkChange}
              loading={loading}
              style={{
                width: '180px',
              }}
              dropdownClassName="tech-select-dropdown"
              suffixIcon={
                <span style={{
                  fontSize: '12px',
                  color: 'rgba(91, 192, 222, 0.8)',
                  textShadow: '0 0 5px rgba(91, 192, 222, 0.5)'
                }}>▼</span>
              }
            >
              {networkTypes.map(network => (
                <Option
                  key={network.name}
                  value={network.name}
                >
                  {network.display_name}
                </Option>
              ))}
            </Select>
          </StyledSelectWrapper>
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

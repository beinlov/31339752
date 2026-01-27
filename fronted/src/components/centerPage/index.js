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

const StyledSelectWrapper = styled.div``;

const TechDropdownTrigger = styled.div`
  width: 220px;
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid rgba(91, 192, 222, 0.6);
  background: linear-gradient(135deg, rgba(12, 32, 64, 0.95), rgba(22, 58, 120, 0.75));
  color: #d9f0ff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 0 18px rgba(91, 192, 222, 0.35), inset 0 0 20px rgba(4, 10, 24, 0.8);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  letter-spacing: 0.5px;

  &:before {
    content: '';
    position: absolute;
    inset: 2px;
    border-radius: 12px;
    border: 1px solid rgba(91, 192, 222, 0.2);
    pointer-events: none;
  }

  &:after {
    content: '';
    position: absolute;
    width: 120%;
    height: 60%;
    top: -40%;
    left: -10%;
    background: radial-gradient(circle, rgba(91, 192, 222, 0.35), transparent 60%);
    opacity: 0.6;
    pointer-events: none;
    transform: rotate(6deg);
  }

  &:hover {
    border-color: rgba(123, 220, 255, 0.9);
    box-shadow: 0 0 25px rgba(91, 192, 222, 0.45), inset 0 0 25px rgba(4, 12, 30, 0.9);
    color: #ffffff;
  }

  .label {
    font-weight: 600;
    font-size: 15px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    text-shadow: 0 0 8px rgba(91, 192, 222, 0.6);
  }

  .icon {
    font-size: 12px;
    color: rgba(91, 192, 222, 0.9);
    text-shadow: 0 0 10px rgba(91, 192, 222, 0.7);
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
    rankings: { global: [], china: [] },
    activeRanking: null,
    dropdownOpen: false,
    loading: true
  };



  componentDidMount() {
    this.fetchRankings();
  }

  fetchRankings = async () => {
    try {
      const [globalRes, chinaRes] = await Promise.all([
        axios.get('http://localhost:8000/api/botnet-rankings', { params: { mode: 'global' } }),
        axios.get('http://localhost:8000/api/botnet-rankings', { params: { mode: 'china' } }),
      ]);

      if (globalRes.data.status === 'success' && chinaRes.data.status === 'success') {
        this.setState({
          rankings: {
            global: globalRes.data.data || [],
            china: chinaRes.data.data || [],
          },
          loading: false
        });
      }
      this.handleNetworkChange("ramnit")
    } catch (error) {
      console.error('Error fetching botnet rankings:', error);
      this.setState({ loading: false });
    }
  };

  handleNetworkChange = (value) => {
    const { dispatch } = this.props;

    this.setState({
      selectedNetwork: value,
      dropdownOpen: false
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

    const { rankings, activeRanking, dropdownOpen, loading } = this.state;

    const activeList = activeRanking
      ? (activeRanking === 'global' ? rankings.global : rankings.china)
      : [];

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

          <StyledSelectWrapper style={{ position: 'relative' }}>
            <TechDropdownTrigger
              onClick={() => {
                if (loading) return;
                this.setState(prev => ({
                  dropdownOpen: !prev.dropdownOpen,
                  activeRanking: !prev.dropdownOpen ? null : prev.activeRanking
                }));
              }}
            >
              <span className="label">{this.state.selectedNetwork}</span>
              <span className="icon">▼</span>
            </TechDropdownTrigger>

            {dropdownOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '110%',
                  left: 0,
                  width: activeRanking ? '380px' : '220px',
                  background: 'rgba(6, 14, 30, 0.94)',
                  border: '1px solid rgba(91, 192, 222, 0.25)',
                  borderRadius: '14px',
                  boxShadow: '0 20px 45px rgba(4, 10, 24, 0.8), inset 0 0 30px rgba(91,192,222,0.12)',
                  display: 'flex',
                  flexDirection: 'row',
                  overflow: 'hidden',
                  zIndex: 2000,
                  backdropFilter: 'blur(6px)'
                }}
              >
                <div
                  style={{
                    borderRight: activeRanking ? '1px solid rgba(91, 192, 222, 0.15)' : 'none',
                    minWidth: '130px',
                    flexShrink: 0,
                    background: 'rgba(8, 18, 40, 0.7)'
                  }}
                >
                  {[
                    { key: 'global', label: '按照全球节点数量排序' },
                    { key: 'china', label: '按照对中国影响程度排序' },
                  ].map(cat => (
                    <div
                      key={cat.key}
                      onClick={() =>
                        this.setState(prev => ({
                          activeRanking: prev.activeRanking === cat.key ? null : cat.key
                        }))
                      }
                      style={{
                        padding: '16px 18px',
                        color: activeRanking === cat.key ? '#f4fbff' : '#9abef3',
                        background: activeRanking === cat.key ? 'linear-gradient(90deg, #166ad3, #0f2c55)' : 'transparent',
                        cursor: 'pointer',
                        fontWeight: 600,
                        fontSize: 14,
                        letterSpacing: 0.3,
                        lineHeight: 1.35,
                        textShadow: activeRanking === cat.key ? '0 0 12px rgba(91,192,222,0.9)' : '0 0 4px rgba(91,192,222,0.2)',
                        borderLeft: activeRanking === cat.key ? '3px solid #5bc0de' : '3px solid transparent',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {cat.label}
                    </div>
                  ))}
                </div>
                {activeRanking && (
                  <div
                    style={{
                      flex: 1,
                      maxHeight: '240px',
                      overflowY: 'auto',
                      background: 'rgba(4, 10, 24, 0.8)'
                    }}
                  >
                    {(activeList || []).map(item => (
                      <div
                        key={item.name}
                        onClick={() => this.handleNetworkChange(item.name)}
                        style={{
                          padding: '12px 14px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          color: '#dbefff',
                          cursor: 'pointer',
                          background: this.state.selectedNetwork === item.name ? 'rgba(91,192,222,0.18)' : 'transparent',
                          transition: 'all 0.2s ease',
                          borderBottom: '1px solid rgba(91, 192, 222, 0.08)'
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>{item.display_name || item.name}</span>
                        <span style={{ color: '#7ad1ff', fontSize: 13, fontWeight: 700 }}>
                          {activeRanking === 'global' ? item.global_count : item.china_count}
                        </span>
                      </div>
                    ))}
                    {(activeList || []).length === 0 && (
                      <div style={{ padding: '12px', color: '#8fb7e4' }}>暂无数据</div>
                    )}
                  </div>
                )}
              </div>
            )}
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
            top: '85%',
            zIndex: 999,
          }}>
            <Takeover />
          </div>
        </MapContainer>

        <CenterBottom>
          <div className="user-situation">
            <ActivityStream userSitua={userSitua} selectedNetwork={this.state.selectedNetwork} />
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
  selectedNetwork: state.mapState.selectedNetwork,
});

export default connect(mapStateToProps)(index);

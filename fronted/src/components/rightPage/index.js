import React, { PureComponent } from 'react';
import { BorderBox13, Decoration1 } from '@jiaminghi/data-view-react';
import DataDisplay from './charts/DataDisplay';
import DiffusionTrend from './charts/DiffusionTrend';
import { ModuleTitle } from '../../style/globalStyledSet';
import { connect } from '../../utils/ModernConnect';
import earthRotateGif from '../../assets/images/earth-rotate.gif';
import { Select } from 'antd';
import styled from 'styled-components';
import CleanupModal from '../CleanupModal';
import {
  RightPageStyle,
  RightTopBox,
  RightBottomBox,
} from './style';

const { Option } = Select;

const CleanupButton = styled.button`
  width: calc(100% - 2.5rem);
  height: 0.6rem;
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.6);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
  font-size: 0.22rem;
  font-weight: 600;
  color: #f34236ff;
  text-shadow: 0 0 5px rgba(255, 215, 0, 0.5);

  &:hover:not(:disabled) {
    background: rgba(0, 212, 255, 0.15);
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
    border-color: rgba(0, 212, 255, 0.9);
    transform: translateY(-1px);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: rgba(100, 100, 100, 0.2);
    border-color: rgba(100, 100, 100, 0.3);
    box-shadow: none;
    color: rgba(255, 255, 255, 0.3);
  }
`;

const TimeRangeBar = styled.div`
  width: 100%;
  height: 0.55rem;
  margin: 0.2rem 0 0.18rem 0;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0 0;
  box-sizing: border-box;
  position: relative;

  .ant-select {
    width: calc(100% - 0.5rem);
    height: 100%;
    z-index: 10;

    .ant-select-selector {
      background: rgba(0, 212, 255, 0.06) !important;
      border: 2px solid rgba(0, 212, 255, 0.9) !important;
      border-radius: 6px !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      box-shadow: 0 0 10px rgba(0, 212, 255, 0.3) !important;
      height: 100% !important;
      display: flex !important;
      align-items: center !important;
      padding: 0 0.2rem !important;
    }

    .ant-select-selection-item {
      color: #ffffff !important;
      font-weight: 700 !important;
      font-size: 0.22rem !important;
      text-shadow: 0 0 8px rgba(0, 212, 255, 0.6) !important;
      line-height: normal !important;
    }

    .ant-select-arrow {
      color: rgba(0, 212, 255, 0.9) !important;
      font-size: 0.18rem !important;
    }
  }
`;

const TechDecoration = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;

  .tech-line {
    position: absolute;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.4), transparent);
    height: 1px;
    width: 100%;
    animation: scanLine 3s linear infinite;
  }

  .tech-corner {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 2px solid rgba(0, 212, 255, 0.5);

    &.top-left {
      top: 0;
      left: 0;
      border-right: none;
      border-bottom: none;
    }

    &.top-right {
      top: 0;
      right: 0;
      border-left: none;
      border-bottom: none;
    }

    &.bottom-left {
      bottom: 0;
      left: 0;
      border-right: none;
      border-top: none;
    }

    &.bottom-right {
      bottom: 0;
      right: 0;
      border-left: none;
      border-top: none;
    }
  }

  .glow-dot {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #00d4ff;
    border-radius: 50%;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes scanLine {
    0% { top: 0%; opacity: 0; }
    50% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.5); }
  }
`;

const EarthContainer = styled.div`
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;

  .earth-wrapper {
    position: relative;
    width: 85%;
    
    .earth-gif {
      width: 100%;
      height: auto;
      border-radius: 50%;
      box-shadow: 0 0 30px rgba(0, 212, 255, 0.4),
                  inset 0 0 20px rgba(0, 212, 255, 0.2);
      border: 2px solid rgba(0, 212, 255, 0.3);
    }

    .orbit-ring {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border: 1px solid rgba(0, 212, 255, 0.2);
      border-radius: 50%;
      animation: rotate 20s linear infinite;

      &.ring-1 {
        width: 110%;
        height: 110%;
      }

      &.ring-2 {
        width: 120%;
        height: 120%;
        animation-duration: 25s;
        animation-direction: reverse;
      }
    }

    .orbit-dot {
      position: absolute;
      width: 6px;
      height: 6px;
      background: #00d4ff;
      border-radius: 50%;
      box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
      top: 0;
      left: 50%;
      transform: translateX(-50%);
    }
  }

  @keyframes rotate {
    from { transform: translate(-50%, -50%) rotate(0deg); }
    to { transform: translate(-50%, -50%) rotate(360deg); }
  }
`;

class RightPage extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      timeRange: 'realtime',
      showCleanupModal: false
    };
  }

  handleTimeRangeChange = (value) => {
    this.setState({ timeRange: value });
  };

  handleCleanup = () => {
    const userRole = localStorage.getItem('role');
    const canOperate = userRole === '管理员' || userRole === '操作员';
    if (canOperate) {
      this.setState({ showCleanupModal: true });
    }
  };

  render() {
    return (
      <RightPageStyle>
        <RightTopBox>
          <TechDecoration>
            <div className='tech-corner top-left' />
            <div className='tech-corner top-right' />
            <div className='glow-dot' style={{ top: '5%', left: '10%', animationDelay: '0s' }} />
            <div className='glow-dot' style={{ top: '15%', right: '15%', animationDelay: '0.5s' }} />
            <div className='glow-dot' style={{ bottom: '20%', left: '5%', animationDelay: '1s' }} />
          </TechDecoration>
          <div className='right-top'>
            <ModuleTitle>
              <i className='iconfont'>&#xe7f7;</i>
              <span>接管僵尸节点数量</span>
            </ModuleTitle>
            <div className='right-top-content'>
              <DataDisplay />
              <EarthContainer>
                <div className='earth-wrapper'>
                  <div className='orbit-ring ring-1'>
                    <div className='orbit-dot' />
                  </div>
                  <div className='orbit-ring ring-2'>
                    <div className='orbit-dot' />
                  </div>
                  <img
                    alt='地球'
                    src={earthRotateGif}
                    className='earth-gif'
                  />
                </div>
              </EarthContainer>
            </div>
          </div>
        </RightTopBox>

        <CleanupButton 
          onClick={this.handleCleanup}
          disabled={localStorage.getItem('role') === '访客'}
          title={localStorage.getItem('role') === '访客' ? '访客无操作权限' : '一键清除僵尸网络节点'}
        >
          一键清除
        </CleanupButton>

        <TimeRangeBar>
          <Select
            value={this.state.timeRange}
            onChange={this.handleTimeRangeChange}
            dropdownStyle={{
              backgroundColor: 'rgba(11, 24, 55, 0.95)',
              border: '2px solid rgba(0, 212, 255, 0.9)',
              boxShadow: '0 0 15px rgba(0, 212, 255, 0.4)'
            }}
          >
            <Option value='realtime' style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.2rem', padding: '0.15rem 0' }}>实时情况</Option>
            <Option value='7days' style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.2rem', padding: '0.15rem 0' }}>近7天</Option>
            <Option value='30days' style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.2rem', padding: '0.15rem 0' }}>近30天</Option>
          </Select>
        </TimeRangeBar>

        <RightBottomBox>
          <BorderBox13 className='right-bottom-borderBox13'>
            <TechDecoration>
              <div className='tech-line' style={{ top: '30%' }} />
              <div className='tech-corner bottom-left' />
              <div className='tech-corner bottom-right' />
              <div className='glow-dot' style={{ top: '10%', right: '8%', animationDelay: '0.3s' }} />
              <div className='glow-dot' style={{ top: '50%', left: '3%', animationDelay: '0.8s' }} />
              <div className='glow-dot' style={{ bottom: '15%', right: '5%', animationDelay: '1.2s' }} />
            </TechDecoration>
            <div className='right-bottom'>
              <ModuleTitle>
                <i className='iconfont'>&#xe790;</i>
                <span>传播态势</span>
              </ModuleTitle>
              <div style={{ position: 'absolute', right: '0.3rem', top: '0.3rem' }}>
                <Decoration1 style={{ width: '150px', height: '20px' }} />
              </div>
              <div className='diffusion-trend-box'>
                <DiffusionTrend 
                  timeRange={this.state.timeRange} 
                  botnetData={this.props.botnetData}
                  displayMode={this.props.displayMode}
                  selectedNetwork={this.props.selectedNetwork}
                />
              </div>
            </div>
          </BorderBox13>
        </RightBottomBox>

        {/* 清除模态框 */}
        {this.state.showCleanupModal && (
          <CleanupModal 
            onClose={() => this.setState({ showCleanupModal: false })} 
            dispatch={this.props.dispatch}
            selectedNetwork={this.props.selectedNetwork}
          />
        )}
      </RightPageStyle>
    );
  }
}

const mapStateToProps = ({ mapState }) => ({
  botnetData: mapState.botnetData,
  displayMode: mapState.displayMode,
  selectedNetwork: mapState.selectedNetwork
});

export default connect(mapStateToProps)(RightPage);

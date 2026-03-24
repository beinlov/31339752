import React from 'react';
import { BorderBox11 } from '@jiaminghi/data-view-react';
import styled from 'styled-components';
import { connect } from '../../../utils/ModernConnect';

const DataBox = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 12.5%;
  width: 100%;
  padding: 0.1rem 0;
  position: relative;

  .toggle-container {
    display: flex;
    justify-content: center;
    margin-bottom: 0.2rem;
    position: relative;
    z-index: 2;
    
    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
      z-index: -1;
    }
    
    .toggle-button {
      background: linear-gradient(135deg, #1e3c72, #2a5298);
      border: 2px solid #4FD8FF;
      border-radius: 0.3rem;
      color: #fff;
      cursor: pointer;
      font-size: 0.22rem;
      font-weight: 600;
      padding: 0.15rem 0.3rem;
      margin: 0 0.1rem;
      transition: all 0.3s ease;
      min-width: 1.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
      }
      
      &:hover {
        background: linear-gradient(135deg, #2a5298, #4FD8FF);
        box-shadow: 0 0 0.15rem rgba(79, 216, 255, 0.8);
        transform: translateY(-2px);
        
        &::before {
          left: 100%;
        }
      }
      
      &.active {
        background: linear-gradient(135deg, #4FD8FF, #00BFFF);
        color: #000;
        font-weight: bold;
        box-shadow: 0 0 0.25rem rgba(79, 216, 255, 1),
                    inset 0 0 0.1rem rgba(255, 255, 255, 0.5);
        animation: activeGlow 2s ease-in-out infinite;
      }
    }
  }

  @keyframes activeGlow {
    0%, 100% { box-shadow: 0 0 0.25rem rgba(79, 216, 255, 1), inset 0 0 0.1rem rgba(255, 255, 255, 0.5); }
    50% { box-shadow: 0 0 0.4rem rgba(79, 216, 255, 1), inset 0 0 0.15rem rgba(255, 255, 255, 0.7); }
  }

  .border-box-wrapper {
    height: 1.2rem;
    margin-top: 0.25rem;
    width: 100%;
    position: relative;

    .dv-border-box-11-title {
      font-size: 0.26rem !important;
      font-weight: bold !important;
      color: #fff !important;
      text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
    }

    &:first-child {
      .dv-border-box-11 {
        top: -43%;
      }
    }

    &:last-child {
      .dv-border-box-11 {
        top: -15%;
      }
    }

    .dv-border-box-11 {
      width: 100%;
      height: 150%;
      position: absolute;
      left: 0;
      filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.3));
    }
    
    &::after {
      content: '';
      position: absolute;
      bottom: -0.1rem;
      left: 50%;
      transform: translateX(-50%);
      width: 80%;
      height: 2px;
      background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.4), transparent);
    }
  }

  .data-item {
    position: absolute;
    width: 100%;
    height: 100%;
    left: 0;
    top: 0.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    
    .number {
      font-size: 0.35rem;
      font-weight: bold;
      color: #4FD8FF;
      font-family: DINAlternate-Bold, Arial;
      text-align: center;
      transition: all 0.3s ease;
      transform: translateY(0.1rem);
      text-shadow: 0 0 15px rgba(79, 216, 255, 0.8),
                   0 0 30px rgba(79, 216, 255, 0.4);
      animation: numberPulse 3s ease-in-out infinite;
      
      &::before {
        content: attr(data-value);
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        color: rgba(79, 216, 255, 0.3);
        filter: blur(8px);
        z-index: -1;
      }
    }
  }
  
  @keyframes numberPulse {
    0%, 100% { 
      text-shadow: 0 0 15px rgba(79, 216, 255, 0.8), 0 0 30px rgba(79, 216, 255, 0.4);
    }
    50% { 
      text-shadow: 0 0 20px rgba(79, 216, 255, 1), 0 0 40px rgba(79, 216, 255, 0.6);
    }
  }
`;

const DataDisplay = ({ botnetData, displayMode, dispatch }) => {
  const handleToggleMode = (mode) => {
    dispatch({
      type: 'mapState/setDisplayMode',
      payload: mode
    });
    // 切换显示模式时重新获取行业分布数据
    dispatch({
      type: 'mapState/fetchIndustryData'
    });
  };

  // 根据显示模式获取相应的数据
  const getChinaCount = () => {
    return displayMode === 'active' ? botnetData.china_active : botnetData.china_cleaned;
  };

  const getGlobalCount = () => {
    return displayMode === 'active' ? botnetData.global_active : botnetData.global_cleaned;
  };

  const getModeTitle = () => {
    return displayMode === 'active' ? '活跃节点' : '已清理节点';
  };

  return (
    <DataBox>
      <div className="toggle-container">
        <div 
          className={`toggle-button ${displayMode === 'active' ? 'active' : ''}`}
          onClick={() => handleToggleMode('active')}
        >
          活跃节点
        </div>
        <div 
          className={`toggle-button ${displayMode === 'cleaned' ? 'active' : ''}`}
          onClick={() => handleToggleMode('cleaned')}
        >
          已清理节点
        </div>
      </div>
      <div className="border-box-wrapper">
        <BorderBox11 title={`全国${getModeTitle()}`} >
          <div className="data-item">
            <div className="number">{getChinaCount().toLocaleString()}</div>
          </div>
        </BorderBox11>
      </div>
    </DataBox>
  );
};

const mapStateToProps = ({ mapState }) => ({
  botnetData: mapState.botnetData,
  displayMode: mapState.displayMode
});

export default connect(mapStateToProps)(DataDisplay); 
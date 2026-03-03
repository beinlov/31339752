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

  .toggle-container {
    display: flex;
    justify-content: center;
    margin-bottom: 0.15rem;
    
    .toggle-button {
      background: linear-gradient(135deg, #1e3c72, #2a5298);
      border: 2px solid #4FD8FF;
      border-radius: 0.25rem;
      color: #fff;
      cursor: pointer;
      font-size: 0.18rem;
      font-weight: 500;
      padding: 0.1rem 0.2rem;
      margin: 0 0.05rem;
      transition: all 0.3s ease;
      min-width: 1.2rem;
      text-align: center;
      
      &:hover {
        background: linear-gradient(135deg, #2a5298, #4FD8FF);
        box-shadow: 0 0 0.15rem rgba(79, 216, 255, 0.8);
        transform: translateY(-1px);
      }
      
      &.active {
        background: linear-gradient(135deg, #4FD8FF, #00BFFF);
        color: #000;
        font-weight: bold;
        box-shadow: 0 0 0.2rem rgba(79, 216, 255, 1);
      }
    }
  }

  .border-box-wrapper {
    height: 1.0rem;
    margin-top: 0.2rem;
    width: 100%;
    position: relative;

    .dv-border-box-11-title {
      font-size: 0.24rem !important;
      font-weight: bold !important;
      color: #fff !important;
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
      font-size: 0.3rem;
      font-weight: bold;
      color: #4FD8FF;
      font-family: DINAlternate-Bold;
      text-align: center;
      transition: all 0.3s ease;
      transform: translateY(0.1rem);
    }
  }
`;

const DataDisplay = ({ botnetData, displayMode, dispatch }) => {
  const handleToggleMode = (mode) => {
    dispatch({
      type: 'mapState/setDisplayMode',
      payload: mode
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
      <div className="border-box-wrapper">
        <BorderBox11 title={`全球${getModeTitle()}`}>
          <div className="data-item">
            <div className="number">{getGlobalCount().toLocaleString()}</div>
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
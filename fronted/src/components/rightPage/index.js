import React, { PureComponent } from 'react';
import { BorderBox13 } from '@jiaminghi/data-view-react';
import DataDisplay from './charts/DataDisplay';
import DiffusionTrend from './charts/DiffusionTrend';
import { ModuleTitle } from '../../style/globalStyledSet';
import { connect } from '../../utils/ModernConnect';
import earthRotateGif from '../../assets/images/earth-rotate.gif';
import { Select } from 'antd';
import styled from 'styled-components';
import {
  RightPageStyle,
  RightTopBox,
  RightBottomBox,
} from './style';

const { Option } = Select;

const TimeRangeBar = styled.div`
  width: 100%;
  margin: 0 0 0.06rem 0;
  display: flex;
  justify-content: flex-end;
  padding: 0 0.25rem;
  box-sizing: border-box;

  .ant-select {
    width: 120px;

    .ant-select-selector {
      background: rgba(0, 212, 255, 0.06) !important;
      border: 1px solid rgba(0, 212, 255, 0.9) !important;
      border-radius: 4px !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      box-shadow: 0 0 6px rgba(0, 212, 255, 0.18) !important;
    }

    .ant-select-selection-item {
      color: #ffffff !important;
      font-weight: 700 !important;
      text-shadow: none !important;
    }

    .ant-select-arrow {
      color: rgba(0, 212, 255, 0.9) !important;
    }
  }
`;

class RightPage extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      timeRange: '7days'
    };
  }

  handleTimeRangeChange = (value) => {
    this.setState({ timeRange: value });
  };

  render() {
    return (
      <RightPageStyle>
        <RightTopBox>
          <div className='right-top'>
            <ModuleTitle>
              <i className='iconfont'>&#xe7f7;</i>
              <span>接管僵尸节点数量</span>
            </ModuleTitle>
            <div className='right-top-content'>
              <DataDisplay />
              <img
                alt='地球'
                src={earthRotateGif}
                className='earth-gif'
              />
            </div>
          </div>
        </RightTopBox>

        <TimeRangeBar>
          <Select
            value={this.state.timeRange}
            onChange={this.handleTimeRangeChange}
            dropdownStyle={{
              backgroundColor: 'rgba(11, 24, 55, 0.95)',
              border: '1px solid rgba(0, 212, 255, 0.9)'
            }}
          >
            <Option value='7days' style={{ color: '#ffffff', fontWeight: 700 }}>近7天</Option>
            <Option value='30days' style={{ color: '#ffffff', fontWeight: 700 }}>近30天</Option>
          </Select>
        </TimeRangeBar>

        <RightBottomBox>
          <BorderBox13 className='right-bottom-borderBox13'>
            <div className='right-bottom'>
              <ModuleTitle>
                <i className='iconfont'>&#xe790;</i>
                <span>传播态势</span>
              </ModuleTitle>
              <div className='diffusion-trend-box'>
                <DiffusionTrend timeRange={this.state.timeRange} />
              </div>
            </div>
          </BorderBox13>
        </RightBottomBox>
      </RightPageStyle>
    );
  }
}

const mapStateToProps = state => ({
});

export default connect(mapStateToProps)(RightPage);

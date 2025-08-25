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

  .border-box-wrapper {
    height: 1.0rem;
    margin-top: 0.2rem;
    width: 100%;
    position: relative;

    .dv-border-box-11-title {
      font-size: 0.20rem !important;
      font-weight: normal !important;
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

const DataDisplay = ({ botnetData }) => {
  return (
    <DataBox>
      <div className="border-box-wrapper">
        <BorderBox11 title="全国数量" >
          <div className="data-item">
            <div className="number">{botnetData.china_amount.toLocaleString()}</div>
          </div>
        </BorderBox11>
      </div>
      <div className="border-box-wrapper">
        <BorderBox11 title="全球数量">
          <div className="data-item">
            <div className="number">{botnetData.global_amount.toLocaleString()}</div>
          </div>
        </BorderBox11>
      </div>
    </DataBox>
  );
};

const mapStateToProps = ({ mapState }) => ({
  botnetData: mapState.botnetData
});

export default connect(mapStateToProps)(DataDisplay); 
import React, { PureComponent } from 'react';
import { BorderBox13 } from '@jiaminghi/data-view-react';
import DataDisplay from './charts/DataDisplay';
import IndustryDistribution from './charts/IndustryDistribution';
import DiffusionTrend from './charts/DiffusionTrend';
import { ModuleTitle } from '../../style/globalStyledSet';
import { connect } from '../../utils/ModernConnect';
import earthRotateGif from '../../assets/images/earth-rotate.gif';
import {
  RightPageStyle,
  RightTopBox,
  RightCenterBox,
  RightBottomBox,
} from './style';

class RightPage extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    const { industryData } = this.props;
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

        <RightCenterBox>
          <BorderBox13 className='right-center-borderBox13'>
            <div className='right-center'>
              <ModuleTitle>
                <i className='iconfont'>&#xe7fd;</i>
                <span>重要行业分布情况</span>
              </ModuleTitle>
              <div className='industry-box'>
                <IndustryDistribution
                  industryData={industryData}
                />
              </div>
            </div>
          </BorderBox13>
        </RightCenterBox>

        <RightBottomBox>
          <BorderBox13 className='right-bottom-borderBox13'>
            <div className='right-bottom'>
              <ModuleTitle>
                <i className='iconfont'>&#xe790;</i>
                <span>传播态势</span>
              </ModuleTitle>
              <div className='diffusion-trend-box'>
                <DiffusionTrend />
              </div>
            </div>
          </BorderBox13>
        </RightBottomBox>
      </RightPageStyle>
    );
  }
}

const mapStateToProps = state => ({
  industryData: state.rightPage.industryData,
});

export default connect(mapStateToProps)(RightPage);

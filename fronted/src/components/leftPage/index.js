import React, { PureComponent } from 'react';
import { LeftPage, LeftTopBox, LeftBottomBox } from './style';
import { ModuleTitle } from '../../style/globalStyledSet';
import { BorderBox13 } from '@jiaminghi/data-view-react';
import WorldMap from './charts/WorldMap';
import Map from '../centerPage/charts/Map';
import AffectedSituation from './charts/AffectedSituation';
import { connect } from 'dva';

class index extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {};
  }
  
  render() {
    const { 
      worldMapData, 
      mapData,
      isSwapped,
      onSwitchMap,
      affectedData,
      selectedNetwork,
      currentMap
    } = this.props;

    const MapComponent = isSwapped ? Map : WorldMap;
    const mapDataToUse = isSwapped ? mapData : worldMapData;
    
    return (
      <LeftPage>
        <LeftTopBox>
          <BorderBox13 className='left-top-borderBox12'>
            <div className='left-top'>
              <ModuleTitle className='module-title'>
                <i className='iconfont'>&#xe78f;</i>
                <span>
                  {isSwapped 
                    ? '各国家受影响情况--僵尸节点数量/个'
                    : currentMap === 'china'
                      ? '各省(市)受影响情况--僵尸节点数量/个'
                      : `${currentMap}各城市受影响情况--僵尸节点数量/个`
                  }
                </span>
              </ModuleTitle>
              
              <div className='affected-situation-container'>
                <AffectedSituation affectedData={affectedData} />
              </div>
            </div>
          </BorderBox13>
        </LeftTopBox>

        <LeftBottomBox>
          <BorderBox13 className='left-bottom-borderBox13'>
            <div className='left-bottom'>
              <ModuleTitle className='module-title'>
                <i className='iconfont'>&#xe7fd;</i>
                <span>{isSwapped ? '中国分布' : '全球分布'}</span>
              </ModuleTitle>
              <MapComponent 
                mapData={mapDataToUse} 
                onSwitchMap={onSwitchMap}
                isLeftPage={true}
                selectedNetwork={selectedNetwork}
              />
            </div>
          </BorderBox13>
        </LeftBottomBox>
      </LeftPage>
    );
  }
}

const mapStateToProps = state => ({
  trafficSitua: state.leftPage.trafficSitua,
  accessFrequency: state.leftPage.accessFrequency,
  peakFlow: state.leftPage.peakFlow,
  worldMapData: state.leftPage.worldMapData,
  mapData: state.centerPage.mapData,
  isSwapped: state.mapPosition.isSwapped,
  affectedData: state.leftPage.affectedData,
  selectedNetwork: state.mapState.selectedNetwork,
  currentMap: state.mapState.currentMap
});

export default connect(mapStateToProps)(index);

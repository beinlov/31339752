import React from 'react';
import { connect } from '../utils/ModernConnect';
import { IndexPageStyle, IndexPageContent, TopPageStyle, GlobalStyle } from '../style/style';
import TopPage from './topPage';
import LeftPage from './leftPage';
import CenterPage from './centerPage';
import RightPage from './rightPage';

const IndexPage = ({ dispatch, isSwapped }) => {
  const handleSwitchMap = () => {
    dispatch({
      type: 'mapPosition/toggleMapPosition',
    });
  };

  return (
    <>
      <GlobalStyle />
      <IndexPageStyle>
        <TopPageStyle>
          <TopPage />
        </TopPageStyle>
        <IndexPageContent>
          {/* 左侧内容 */}
          <LeftPage onSwitchMap={handleSwitchMap} isSwapped={isSwapped} />
          {/* 中间内容 */}
          <CenterPage onSwitchMap={handleSwitchMap} isSwapped={isSwapped} />
          {/* 右侧内容 */}
          <RightPage />
        </IndexPageContent>
      </IndexPageStyle>
    </>
  );
};

const mapStateToProps = (state) => ({
  isSwapped: state.mapPosition.isSwapped,
});

export default connect(mapStateToProps)(IndexPage);

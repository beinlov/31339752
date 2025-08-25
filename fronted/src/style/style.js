import styled, { createGlobalStyle } from 'styled-components';
import pageBg from '../assets/pageBg.png';

// 添加全局样式
export const GlobalStyle = createGlobalStyle`
  html, body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }
  
  * {
    box-sizing: border-box;
  }
`;

export const IndexPageStyle = styled.div`
  position: relative;
  overflow: hidden;
  background: url(${pageBg}) center center no-repeat;
  background-size: cover;
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
`;

export const TopPageStyle = styled.div`
  width: 100%;
  height: 2vh;
  flex-shrink: 0;
`;

export const IndexPageContent = styled.div`
  display: flex;
  justify-content: space-between;
  flex-wrap: nowrap;
  height: 98vh;
  width: 100%;
  overflow: hidden;
  .center-page {
    flex: 1;
  }
`;

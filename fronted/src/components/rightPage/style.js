import styled from 'styled-components';

export const RightPageStyle = styled.div`
  width: 25%;
  height:100%;
`;

export const RightTopBox = styled.div`
  position: relative;
  height: 37%;
  width: 100%;
  margin-bottom: 1%;
  top:0%;

  .right-top {

    &-content {
    width: 100%;  
    display: flex;
      align-items: center;
      margin-top: 4%;
    }
    
    .earth-gif {
      width: 100%;
      height: auto;
      border-radius: 50%;
      overflow: hidden;
    }
  }
`;

export const RightCenterBox = styled.div`
  position: relative;
  height: 30%;
  width: 100%;
  margin-bottom: 1%;

  .right-center-borderBox13 {
    padding: 0.25rem 0.1875rem 0.1875rem;
    
    
    .right-center {
      width: 100%;
      height: 100%;
      border-radius: 10px;
      background-color: rgba(19, 25, 47, 0.6);
      
      .industry-box {
        margin-top: -1%;
        width: 100%;
        height: 90%;
        
      }
    }
  }
`;

export const RightBottomBox = styled.div`
  position: relative;
  height: 55%;
  width: 100%;
  margin-top: 0.06rem;
  // top: 0.1%;
  .right-bottom-borderBox13 {
    padding: 0.25rem 0.1875rem 0.1875rem;
    height: 100%;
    
    .right-bottom {
      width: 100%;
      height: 100%;
      border-radius: 10px;
      background-color: rgba(19, 25, 47, 0.6);
      
      .diffusion-trend-box {
        width: 100%;
        height: calc(100% - 1.2rem);
        margin-top: 0.1rem;
      }
    }
  }
`;

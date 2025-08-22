import styled from 'styled-components';

export const LeftPage = styled.div`
  margin-top: 0.2rem;  // 减小顶部边距
  align-items: center;
  height: 100%;
  width: 24.5%;
  display: flex;
  flex-direction: column;
  gap: 0.25rem; // 添加间距
`;

export const LeftTopBox = styled.div`
  width: 100%;
  height: 55%;  // 改为百分比
  padding-bottom: 0.25rem;
  display: flex;
  flex-direction: column;
  
  .left-top-borderBox12 {
    width: 100%;
    height: 100%;
    padding: 0.1rem;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(5px);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
    }
    
    .left-top {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      margin-top: 0.2rem; 
      //margin-bottom: -1rem;
      
      .module-title {
        height: 0.35rem;
        display: flex;
        align-items: center;
        padding: 0 0.2rem;
        
        i {
          margin-right: 0.15rem;
          font-size: 0.2rem;
          background: linear-gradient(to right, #0072ff, #00eaff);
          -webkit-background-clip: text;
          color: transparent;
        }
        
        span {
          font-size: 0.18rem;
          font-weight: 600;
          background: linear-gradient(to right, #ffffff, #8cdfff);
          -webkit-background-clip: text;
          color: transparent;
          text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }
      }
      
      .affected-situation-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 0.1rem 0;
      }
    }
  }
`;

export const LeftBottomBox = styled.div`
  width: 100%;
  height: 40%;  // 改为百分比
  display: flex;
  flex-direction: column;
  
  .left-bottom-borderBox13 {
    width: 100%;
    height: 100%;
    padding: 0.2rem;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(5px);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
    }
    
    .left-bottom {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      
      .module-title {
        height: 0.35rem;
        display: flex;
        align-items: center;
        padding: 0 0.2rem;
        
        i {
          margin-right: 0.15rem;
          font-size: 0.2rem;
          background: linear-gradient(to right, #0072ff, #00eaff);
          -webkit-background-clip: text;
          color: transparent;
        }
        
        span {
          font-size: 0.18rem;
          font-weight: 600;
          background: linear-gradient(to right, #ffffff, #8cdfff);
          -webkit-background-clip: text;
          color: transparent;
          text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }
      }
      
      & > div:last-child {
        flex: 1;
        display: flex;
      }
    }
  }
`;

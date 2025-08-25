import styled, { keyframes } from 'styled-components';
import { TitleColor } from '../../style/color';

const pulse = keyframes`
  0% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.02); }
  100% { opacity: 0.8; transform: scale(1); }
`;

const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
  100% { transform: translateY(0px); }
`;

const rotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const shimmer = keyframes`
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
`;

export const CenterPage = styled.div`
  margin-top: 0.2rem;  // 减小顶部边距
  align-items: center;
  height: 100%;
  width: 50%;
  display: flex;
  flex-direction: column;
  margin-right: -0.2rem;
  margin-left: -0.2rem;
  position: relative;
`;

export const MapContainer = styled.div`
  width: 98%;
  height: 75%;

  margin-bottom: 0.1rem;
  margin-top: -0.2rem;  // 添加负边距使地图上移
  position: relative;
  box-shadow: 0 0 20px rgba(91, 192, 222, 0.15);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 0 25px rgba(91, 192, 222, 0.25);
  }
`;

export const TakeoverContainer = styled.div`
  width: 1.425rem;
  height: auto;
  line-height: normal;
  position: absolute;
  //top: 20%;
  left: 50%;
  animation: ${float} 3s ease-in-out infinite;
`;

export const CenterBottom = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 25%;
  gap: 0rem;
  margin-top: -3%;
  position: relative;
  
  .detail-list {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-around;
    gap: 0.2rem;
    
    &-item {
      display: flex;
      align-items: center;
      position: relative;
      height: 1.1rem;
      padding: 0 0.125rem;
      width: 32%;
      border-radius: 8px;
      border: 1px solid rgba(52, 63, 75, 0.8);
      background-color: rgba(19, 25, 47, 0.8);
      backdrop-filter: blur(5px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2), inset 0 1px rgba(255, 255, 255, 0.1);
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3), inset 0 1px rgba(255, 255, 255, 0.15);
        border-color: rgba(91, 192, 222, 0.5);
        background-color: rgba(19, 25, 47, 0.9);
      }
      
      img {
        width: 0.9rem;
        height: 0.9rem;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        transition: all 0.3s ease;
        
        &:hover {
          transform: scale(1.05);
          filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.4));
        }
      }
      
      .detail-item-text {
        margin-left: 0.125rem;
        h3 {
          color: ${TitleColor};
          font-size: 12px;
          margin-bottom: 0.2rem;
          font-weight: 500;
          letter-spacing: 1px;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }
        span {
          font-size: 0.2rem;
          font-weight: bolder;
          background: linear-gradient(45deg, #fff, #4db6e5);
          color: transparent;
          -webkit-background-clip: text;
          background-clip: text;
          text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
          animation: ${pulse} 2s infinite ease-in-out;
        }
        .unit {
          font-size: 0.16rem;
          margin-left: 0.125rem;
          opacity: 0.8;
        }
      }
    }
  }

  .user-situation {
    width: 100%;
    height: 3.2rem;
    background-color: rgba(19, 25, 47, 0.8);
    padding: 0rem;
    margin-top: 0.2rem;
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(52, 63, 75, 0.6);
    backdrop-filter: blur(5px);
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
      border-color: rgba(91, 192, 222, 0.4);
    }
    
    .user-situation-container {
      height: 100%;
      width: 95%;
      display: flex;
      flex-direction: column;
      padding-top: 0.15rem;
      margin: 0 auto;
      
      .user-situation-title {
        font-size: 0.25rem;
        color: #fff;
        text-align: center;
        margin-bottom: 0.22rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        
        i {
          margin-right: 8px;
          color: #4db6e5;
        }
        
        &:after {
          content: '';
          position: absolute;
          bottom: -8px;
          left: 50%;
          transform: translateX(-50%);
          width: 30%;
          height: 2px;
          background: linear-gradient(90deg, transparent, rgba(91, 192, 222, 0.8), transparent);
        }
      }
      
      .user-situation-content {
        flex: 1;
        font-size: 5px;
        overflow: hidden;
        padding-top: 0rem;
        
        .loading-spinner {
          width: 20px;
          height: 20px;
          margin-right: 10px;
          border: 2px solid rgba(91, 192, 222, 0.3);
          border-top-color: #4db6e5;
          border-radius: 50%;
          animation: ${rotate} 1s linear infinite;
        }
      }
    }

    :global {
      .dv-scroll-board {
        width: 100% !important;
        height: calc(100% - 40px) !important;
        
        .header {
          display: flex !important;
          font-size: 14px !important;
          font-weight: bold;
          background: rgba(15, 19, 37, 0.9) !important;
          color: #BCDCFF;
          width: 100% !important;
          height: 35px !important;
          line-height: 35px !important;
          border-bottom: 1px solid rgba(91, 192, 222, 0.3);
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
          backdrop-filter: blur(5px);
        }
        
        .rows {
          font-size: 14px !important;
          color: #E6EFF8;
          width: 100% !important;

          .row-item {
            height: 45px !important;
            line-height: 45px !important;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            
            &:hover {
              background-color: rgba(91, 192, 222, 0.1) !important;
              
              &:before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(
                  90deg,
                  transparent,
                  rgba(91, 192, 222, 0.2),
                  transparent
                );
                animation: ${shimmer} 1.5s ease-in-out;
              }
            }
          }
        }

        .row-item {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 1;
          padding: 0 10px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          min-width: 0;
          height: 45px !important;
          line-height: 45px !important;
        }

        .header-item {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 1;
          padding: 0 10px;
          height: 35px !important;
          line-height: 35px !important;
          letter-spacing: 1px;
          font-weight: 600;
        }
      }
    }
  }
`;

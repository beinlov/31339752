import styled, { keyframes } from 'styled-components';
import { TitleColor } from '../../style/color'

const pulse = keyframes`
  0% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.8;
  }
`;

const gradientAnimation = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

export const TopBox = styled.div`
  .top_box {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
    position: relative;
    
    .top_decoration10 {
      position: relative;
      width: 33.3%;
      height: 3px;
      filter: drop-shadow(0 0 2px rgba(91, 192, 222, 0.8));
    }

    .top_decoration10_reverse {
      transform: rotateY(180deg);
    }

    .title-box {
      display: flex;
      justify-content: center;
      width: 33.4%;

      .top_decoration8 {
        width: 20%;
        height: 22px;
        top: 10%;
        filter: drop-shadow(0 0 3px #568aea);
      }

      .title {
        position: relative;
        width: 60%;
        text-align: center;
        background-size: cover;
        background-repeat: no-repeat;
        padding: 10px 0;

        .title-text {
          font-size: 1.4vw;
          font-weight: 600;
          position: absolute;
          top: 10%;
          bottom: 0;
          left: 50%;
          color: #fff;
          transform: translate(-50%);
          white-space: nowrap;
          text-shadow: 0 0 10px rgba(91, 192, 222, 0.8), 0 0 20px rgba(91, 192, 222, 0.5);
          letter-spacing: 2px;
          animation: ${pulse} 2s infinite ease-in-out;
        }

        .top_decoration6 {
          width: 60%;
          height: 5px;
          filter: drop-shadow(0 0 2px rgba(91, 192, 222, 0.8));
        }

        .title-bototm {
          position: absolute;
          bottom: -20px;
          left: 50%;
          transform: translate(-50%);
        }
      } // end title
    } // end title-box
  } // end top_box
`;

export const TimeBox = styled.div`
  position: absolute;
  right: 2%;
  top: 3%;
  text-align: right;
  padding: 8px 15px;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(32, 41, 64, 0.7) 0%, rgba(32, 41, 64, 0.3) 100%);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(91, 192, 222, 0.3);
  box-shadow: 0 0 15px rgba(91, 192, 222, 0.2);
  
  h3 {
    font-size: 1vw;
    color: ${TitleColor};
    font-weight: 400;
    letter-spacing: 1px;
    margin: 0;
    text-shadow: 0 0 5px rgba(188, 220, 255, 0.5);
    line-height: 1.6;
    
    &:first-child {
      border-bottom: 1px solid rgba(188, 220, 255, 0.3);
      padding-bottom: 4px;
      margin-bottom: 4px;
    }
  }
`;

import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import axios from 'axios';

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const shimmer = keyframes`
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
`;

const TitleWrapper = styled.div`
  position: absolute;
  top: 6%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  text-align: center;
`;

const TitleText = styled.div`
  position: relative;
  display: inline-block;
  cursor: help;
  color: #FFFFFF;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 2px;
  padding: 10px 20px;
  text-shadow: 0 0 10px rgba(91, 192, 222, 0.8), 0 0 20px rgba(91, 192, 222, 0.5);

  &:after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #FFFFFF, transparent);
    background-size: 200% 100%;
    animation: ${shimmer} 2s infinite;
  }
`;

const Tooltip = styled.div`
  position: absolute;
  top: calc(100% + 20px);
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 14px;
  font-weight: normal;
  line-height: 1.6;
  color: #FFFFFF;
  z-index: 1001;
  text-align: left;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  animation: ${fadeIn} 0.3s ease-out;

  &:before {
    content: '';
    position: absolute;
    top: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 8px solid transparent;
    border-right: 8px solid transparent;
    border-bottom: 8px solid rgba(0, 0, 0, 0.85);
  }
`;

const NetworkTitle = ({ selectedNetwork }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [animateTitle, setAnimateTitle] = useState(false);
  const [networkInfo, setNetworkInfo] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNetworkInfo = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/botnet-info');
        if (response.data.status === 'success') {
          setNetworkInfo(response.data.data);
        }
      } catch (error) {
        console.error('Error fetching botnet info:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchNetworkInfo();
  }, []);

  useEffect(() => {
    setAnimateTitle(true);
    const timer = setTimeout(() => setAnimateTitle(false), 1000);
    return () => clearTimeout(timer);
  }, [selectedNetwork]);

  if (loading) {
    return (
      <TitleWrapper>
        <TitleText>加载中...</TitleText>
      </TitleWrapper>
    );
  }

  const currentNetwork = networkInfo[selectedNetwork] || { title: '未知网络', description: '暂无相关信息' };

  return (
    <TitleWrapper>
      <TitleText
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        style={{
          transform: animateTitle ? 'scale(1.05)' : 'scale(1)',
          transition: 'transform 0.3s ease-out'
        }}
      >
        {currentNetwork.title}
        {showTooltip && (
          <Tooltip>
            {currentNetwork.description}
          </Tooltip>
        )}
      </TitleText>
    </TitleWrapper>
  );
};

export default NetworkTitle;

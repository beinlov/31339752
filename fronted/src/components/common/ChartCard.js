import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';
import * as echarts from 'echarts';

const Card = styled.div`
  width: 100%;
  background: linear-gradient(135deg, rgba(10, 25, 41, 0.95) 0%, rgba(13, 31, 45, 0.95) 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(30, 70, 120, 0.3);
  border: 1px solid rgba(30, 70, 120, 0.3);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(30, 70, 120, 0.6), transparent);
  }
  
  &:hover {
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(30, 70, 120, 0.5);
    border-color: rgba(30, 70, 120, 0.5);
    transform: translateY(-2px);
  }
`;

const ChartContainer = styled.div`
  width: 100%;
  height: ${props => props.height || '300px'};
`;

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(10, 25, 41, 0.9);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  opacity: ${props => props.isLoading ? 1 : 0};
  visibility: ${props => props.isLoading ? 'visible' : 'hidden'};
  transition: opacity 0.3s ease, visibility 0.3s ease;
`;

const Spinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid rgba(30, 70, 120, 0.3);
  border-top-color: #5a8fc4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 0 15px rgba(90, 143, 196, 0.4);
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const NoDataOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(10, 25, 41, 0.9);
  backdrop-filter: blur(5px);
  z-index: 5;
  opacity: ${props => props.show ? 1 : 0};
  visibility: ${props => props.show ? 'visible' : 'hidden'};
  transition: opacity 0.3s ease, visibility 0.3s ease;
`;

const NoDataMessage = styled.div`
  font-size: 16px;
  color: #7a9cc6;
  text-align: center;
  padding: 20px;
  
  div:first-child {
    font-size: 18px;
    font-weight: 500;
    color: #5a8fc4;
    margin-bottom: 8px;
  }
  
  div:last-child {
    color: #6a8db8;
    opacity: 0.8;
  }
`;

const ChartCard = ({ option, height, accentColor, loading = false }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  
  // 检查数据是否为空
  const hasNoData = !option.series || option.series.every(series => 
    !series.data || series.data.length === 0 || 
    (Array.isArray(series.data) && series.data.every(item => item === 0 || item.value === 0))
  );

  useEffect(() => {
    // 初始化图表实例（只执行一次）
    if (chartRef.current && !chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      // 处理窗口大小变化
      const handleResize = () => {
        if (chartInstance.current) {
          chartInstance.current.resize();
        }
      };
      window.addEventListener('resize', handleResize);
      
      // 清理函数（仅在组件卸载时执行）
      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartInstance.current) {
          chartInstance.current.dispose();
          chartInstance.current = null;
        }
      };
    }
  }, []); // 空依赖数组，只在挂载时执行一次

  useEffect(() => {
    // 更新图表配置（当 option 改变时）
    if (chartInstance.current && option) {
      console.log('ChartCard 更新图表配置:', option);
      chartInstance.current.setOption(option, true); // true 表示不合并，完全替换
    }
  }, [option]);

  return (
    <Card>
      <LoadingOverlay isLoading={loading === true}>
        <Spinner />
      </LoadingOverlay>
      <NoDataOverlay show={hasNoData && !loading}>
        <NoDataMessage>
          <div>暂无数据</div>
          <div style={{ fontSize: '14px', marginTop: '5px' }}>请稍后再试</div>
        </NoDataMessage>
      </NoDataOverlay>
      <ChartContainer ref={chartRef} height={height} />
    </Card>
  );
};

export default ChartCard; 
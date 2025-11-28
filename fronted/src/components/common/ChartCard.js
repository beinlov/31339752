import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';
import * as echarts from 'echarts';

const Card = styled.div`
  background: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  background: rgba(255, 255, 255, 0.8);
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
  border: 3px solid rgba(26, 35, 126, 0.2);
  border-top-color: #1a237e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
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
  background: rgba(255, 255, 255, 0.8);
  z-index: 5;
  opacity: ${props => props.show ? 1 : 0};
  visibility: ${props => props.show ? 'visible' : 'hidden'};
  transition: opacity 0.3s ease, visibility 0.3s ease;
`;

const NoDataMessage = styled.div`
  font-size: 16px;
  color: #757575;
  text-align: center;
  padding: 20px;
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
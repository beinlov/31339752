import React, { PureComponent } from 'react';
import * as echarts from 'echarts';
import { registerMap } from 'echarts/core';
import worldJson from "../world.zh.json";
import chinaJson from "../china.json";
import request from '../utils/request';

// 确保在使用地图之前完成注册
try {
  // 检查地图是否已经注册
  const maps = echarts.getMap('world');
  if (!maps) {
    registerMap('world', worldJson);
  }
  const chinaMaps = echarts.getMap('china');
  if (!chinaMaps) {
    registerMap('china', chinaJson);
  }
} catch (error) {
  console.error('地图注册失败:', error);
}

class NodeDistribution extends PureComponent {
  state = {
    nodeData: null,
    loading: true,
    error: null,
    mapType: 'world', // 默认显示世界地图
    totalNodes: 0,
    activeNodes: 0,
    countryDistribution: {},
    statsByCountry: {},
    zoomLevel: 1,
    displayMode: 'all', // 'all', 'active', 'inactive'
    pointSize: 'medium', // 'small', 'medium', 'large'
    mapLoaded: false, // 添加地图加载状态
    renderedActiveNodes: 0,    // 新增：跟踪渲染的活跃节点数
    renderedInactiveNodes: 0   // 新增：跟踪渲染的非活跃节点数
  };

  constructor(props) {
    super(props);
    this.chartRef = React.createRef();
    this.chart = null;
    this.debounceTimer = null;
    this.allNodesData = {
      active: [],
      inactive: []
    };
    
    // 确保zoomLevel有初始值
    this.state = {
      ...this.state,
      zoomLevel: 1
    };
  }

  async componentDidMount() {
    try {
      // 确保地图数据已加载
      if (!echarts.getMap('world') || !echarts.getMap('china')) {
        // 重新注册地图
        registerMap('world', worldJson);
        registerMap('china', chinaJson);
      }
      
      // 初始化图表
      await this.initChart();
      this.setState({ mapLoaded: true });
      
      // 获取节点数据
      await this.fetchNodeData();
    } catch (error) {
      console.error('初始化失败:', error);
      this.setState({ error: '地图初始化失败' });
    }
  }

  componentDidUpdate(prevProps) {
    if (prevProps.networkType !== this.props.networkType) {
      this.fetchNodeData();
    }
  }

  componentWillUnmount() {
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
    window.removeEventListener('resize', this.handleResize);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  initChart = async () => {
    if (this.chartRef.current) {
      // 确保销毁之前的实例
      if (this.chart) {
        this.chart.dispose();
      }
      
      // 创建新实例，使用 WebGL 渲染器并优化大数据渲染
      this.chart = echarts.init(this.chartRef.current, null, { 
        renderer: 'webgl',
        useDirtyRect: false,
        progressive: 500,  // 减少每帧渲染数量
        progressiveThreshold: 1000, // 降低渐进式渲染阈值
        largeThreshold: 1000, // 降低大数据模式阈值
        devicePixelRatio: 1 // 固定像素比
      });
      
      // 添加事件监听
      window.addEventListener('resize', this.handleResize);
      this.chart.on('georoam', this.handleMapZoom);
      
      // 设置基础配置，关闭不必要的动画
      const baseOption = {
        backgroundColor: '#061633',
        animation: false, // 关闭全局动画
        progressive: 1000,
        progressiveThreshold: 5000,
        geo: {
          map: this.state.mapType,
          roam: true,
          zoom: 1.2,
          silent: false,
          animation: false // 关闭地图动画
        }
      };
      
      // 应用基础配置
      await this.chart.setOption(baseOption);
    }
  };

  handleResize = () => {
    if (this.chart) {
      this.chart.resize();
    }
  };

  handleMapZoom = (params) => {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    
    // 获取当前缩放级别
    const zoom = this.chart.getOption().geo[0].zoom;
    
    // 增加缩放变化阈值，减少更新频率
    if (Math.abs(zoom - this.state.zoomLevel) < 0.3) {
      return;
    }
    
    // 使用requestAnimationFrame来优化性能
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    
    this.animationFrame = requestAnimationFrame(() => {
      this.setState({
        zoomLevel: zoom
      }, () => {
        // 延长防抖时间
        if (this.debounceTimer) {
          clearTimeout(this.debounceTimer);
        }
        
        this.debounceTimer = setTimeout(() => {
          this.updateNodeDisplay();
        }, 200); // 增加延迟时间
      });
    });
  };

  updateNodeDisplay = () => {
    if (!this.chart) return;
    
    // 仅更新节点大小和位置
    const option = this.chart.getOption();
    const { zoomLevel } = this.state;
    
    // 简化点大小计算
    const activeSymbolSize = Math.min(3 * zoomLevel, 8);
    const inactiveSymbolSize = Math.min(2 * zoomLevel, 6);
    
    if (option.series[1]) {
      option.series[1].symbolSize = activeSymbolSize;
    }
    if (option.series[2]) {
      option.series[2].symbolSize = inactiveSymbolSize;
    }
    
    this.chart.setOption({
      series: option.series
    }, {
      notMerge: false,
      lazyUpdate: true,
      silent: true,
      animation: false
    });
  };

  fetchNodeData = async () => {
    try {
      this.setState({ loading: true });
      
      // 首先获取统计数据
      const statsResponse = await request(`/api/node-stats/${this.props.networkType}`);
      if (!statsResponse || !statsResponse.data) {
        throw new Error('获取统计数据失败');
      }
      
      // 然后获取节点详细数据（使用较大的page_size以获取足够的数据点）
      const params = new URLSearchParams({
        botnet_type: this.props.networkType,
        page: 1,
        page_size: 100000 // 使用较大的页面大小以获取足够的数据点
      });
      
      const response = await request(`/api/node-details?${params.toString()}`);
      if (!response || !response.data || !response.data.nodes) {
        throw new Error('获取节点数据失败');
      }
      
      // 处理统计数据
      const stats = statsResponse.data;
      const totalNodes = stats.total_nodes;
      const activeNodes = stats.active_nodes;
      const countryDistribution = {};
      const statsByCountry = {};
      
      // 处理国家分布数据
      Object.entries(stats.country_distribution).forEach(([country, data]) => {
        countryDistribution[country] = data.total;
        statsByCountry[country] = {
          active: data.active,
          inactive: data.total - data.active
        };
      });
      
      // 处理节点数据
      const processedData = response.data.nodes.map(node => ({
        ...node,
        longitude: parseFloat(node.longitude) || 0,
        latitude: parseFloat(node.latitude) || 0
      }));
      
      console.log(`NodeDistribution: 获取到 ${totalNodes} 条节点数据，活跃节点: ${activeNodes}`);
      
      this.setState({ 
        nodeData: processedData,
        totalNodes,
        activeNodes,
        countryDistribution,
        statsByCountry
      }, () => {
        this.prepareNodeData();
        this.updateChart();
      });
      
    } catch (error) {
      console.error('获取节点数据失败:', error);
      this.setState({ error: '获取节点数据失败' });
    } finally {
      this.setState({ loading: false });
    }
  };

  // 准备节点数据
  prepareNodeData = () => {
    const { nodeData, mapType } = this.state;
    if (!nodeData) return;

    // 根据地图类型筛选数据
    let filteredData = nodeData;
    if (mapType === 'china') {
      filteredData = nodeData.filter(node => node.country === '中国');
    }

    // 过滤掉无效的经纬度数据
    const validActiveNodes = filteredData
      .filter(node => node.status === 'active' && 
              typeof node.longitude === 'number' && 
              typeof node.latitude === 'number' &&
              !isNaN(node.longitude) && 
              !isNaN(node.latitude) &&
              Math.abs(node.longitude) <= 180 &&
              Math.abs(node.latitude) <= 90);
              
    const validInactiveNodes = filteredData
      .filter(node => node.status !== 'active' && 
              typeof node.longitude === 'number' && 
              typeof node.latitude === 'number' &&
              !isNaN(node.longitude) && 
              !isNaN(node.latitude) &&
              Math.abs(node.longitude) <= 180 &&
              Math.abs(node.latitude) <= 90);

    // 保存所有有效节点数据
    this.allNodesData = {
      active: validActiveNodes.map(node => ({
        name: node.ip,
        value: [node.longitude, node.latitude],
        ip: node.ip,
        status: node.status,
        last_active: node.last_active,
        country: node.country,
        province: node.province,
        city: node.city,
        id: `node-${node.ip.replace(/\./g, '-')}`
      })),
      inactive: validInactiveNodes.map(node => ({
        name: node.ip,
        value: [node.longitude, node.latitude],
        ip: node.ip,
        status: node.status,
        last_active: node.last_active,
        country: node.country,
        province: node.province,
        city: node.city,
        id: `node-${node.ip.replace(/\./g, '-')}`
      }))
    };
  };

  toggleMapType = async () => {
    const newMapType = this.state.mapType === 'world' ? 'china' : 'world';
    
    try {
      // 验证新地图类型是否已注册
      if (!echarts.getMap(newMapType)) {
        // 重新注册地图
        if (newMapType === 'world') {
          registerMap('world', worldJson);
        } else {
          registerMap('china', chinaJson);
        }
      }
      
      // 更新状态
      await new Promise(resolve => {
        this.setState({ 
          mapType: newMapType,
          zoomLevel: 1,
          mapLoaded: false // 临时设置为false，等待新地图加载
        }, resolve);
      });
      
      // 重新初始化图表
      await this.initChart();
      
      // 标记地图已加载
      this.setState({ mapLoaded: true }, () => {
        // 重新准备节点数据并更新图表
        this.prepareNodeData();
        this.updateChart();
      });
      
    } catch (error) {
      console.error('切换地图失败:', error);
      this.setState({ 
        error: '切换地图失败',
        mapType: this.state.mapType // 恢复原来的地图类型
      });
    }
  };

  toggleDisplayMode = (mode) => {
    this.setState({ 
      displayMode: mode
    }, () => {
      this.updateNodeDisplay();
    });
  };

  setPointSize = (size) => {
    this.setState({ 
      pointSize: size
    }, () => {
      this.updateNodeDisplay();
    });
  };

  updateChart = () => {
    if (!this.chart || !this.state.nodeData || !this.state.mapLoaded) {
      console.warn('Chart or data not ready');
      return;
    }

    const { mapType, displayMode, zoomLevel } = this.state;
    
    // 验证地图是否已注册
    if (!echarts.getMap(mapType)) {
      console.error(`地图 ${mapType} 未注册`);
      try {
        // 尝试重新注册地图
        if (mapType === 'world') {
          registerMap('world', worldJson);
        } else if (mapType === 'china') {
          registerMap('china', chinaJson);
        }
      } catch (error) {
        console.error('地图注册失败:', error);
        return;
      }
    }
    
    // 准备地图数据
    let mapData = [];
    try {
      if (mapType === 'world') {
        mapData = Object.keys(this.state.countryDistribution).map(country => ({
          name: country,
          value: this.state.countryDistribution[country]
        }));
      } else if (mapType === 'china') {
        const provinceDistribution = {};
        this.state.nodeData.filter(node => node.country === '中国').forEach(node => {
          if (node.province) {
            if (!provinceDistribution[node.province]) {
              provinceDistribution[node.province] = 0;
            }
            provinceDistribution[node.province]++;
          }
        });
        mapData = Object.keys(provinceDistribution).map(province => ({
          name: province,
          value: provinceDistribution[province]
        }));
      }
    } catch (error) {
      console.error('处理地图数据失败:', error);
      return;
    }

    // 根据显示模式过滤数据
    let activeNodesData = [];
    let inactiveNodesData = [];
    
    const maxPointsPerType = 5000; // 每种类型最多显示5000个点

    if (displayMode === 'all' || displayMode === 'active') {
      activeNodesData = this.sampleData(this.allNodesData.active, maxPointsPerType);
    }
    
    if (displayMode === 'all' || displayMode === 'inactive') {
      inactiveNodesData = this.sampleData(this.allNodesData.inactive, maxPointsPerType);
    }

    // 更新渲染节点计数
    this.setState({
      renderedActiveNodes: activeNodesData.length,
      renderedInactiveNodes: inactiveNodesData.length
    });

    // 简化点大小计算
    const activeSymbolSize = Math.min(3 * zoomLevel, 8);
    const inactiveSymbolSize = Math.min(2 * zoomLevel, 6);

    const option = {
      backgroundColor: '#061633',
      animation: false,
      progressive: 500,
      progressiveThreshold: 1000,
      title: {
        text: `${this.props.networkType.toUpperCase()} 僵尸网络节点分布`,
        subtext: `总节点数: ${this.state.totalNodes} | 活跃节点: ${this.state.activeNodes} | 当前视图: ${mapType === 'world' ? '全球' : '中国'}`,
        left: 'center',
        top: 10,
        textStyle: {
          color: '#eee',
          fontSize: 18
        },
        subtextStyle: {
          color: '#aaa',
          fontSize: 12
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          if (params.seriesType === 'effectScatter' || params.seriesType === 'scatter') {
            return `<div style="font-weight:bold;margin-bottom:5px;">${params.data.country || ''} ${params.data.province || ''} ${params.data.city || ''}</div>` +
                  `<div>IP: ${params.data.ip}</div>` +
                  `<div>状态: ${params.data.status === 'active' ? '活跃' : '非活跃'}</div>` +
                  `<div>最后活动: ${params.data.last_active}</div>`;
          } else if (params.seriesType === 'map') {
            return `${params.name}: ${params.value || 0} 个节点`;
          }
          return '';
        },
        backgroundColor: 'rgba(0,0,0,0.85)',
        borderColor: '#00c8ff',
        borderWidth: 2,
        padding: 10,
        textStyle: {
          color: '#fff'
        }
      },
      visualMap: {
        min: 0,
        max: mapType === 'world' 
          ? Math.max(...Object.values(this.state.countryDistribution)) || 100
          : Math.max(...mapData.map(item => item.value)) || 100,
        text: ['高', '低'],
        realtime: false, // 关闭实时更新
        calculable: true,
        inRange: {
          color: ['#0a3d62', '#1e5799', '#3498db', '#2ecc71', '#27ae60', '#f1c40f', '#f39c12', '#e67e22', '#d35400', '#c0392b']
        },
        textStyle: {
          color: '#fff'
        },
        seriesIndex: [0],
        show: true,
        dimension: 'value',
        pieces: [],
        zlevel: 2,
        hoverLink: true,
        itemWidth: 10,
        itemHeight: 80,
        left: 'left',
        bottom: '10%',
        orient: 'vertical'
      },
      geo: {
        map: mapType,
        roam: true,
        zoom: mapType === 'world' ? 1.2 : 1,
        center: mapType === 'world' ? [0, 30] : [104, 38],
        label: {
          emphasis: {
            show: false
          }
        },
        itemStyle: {
          normal: {
            areaColor: '#0c2c5a',
            borderColor: '#516a8c'
          },
          emphasis: {
            areaColor: '#1854a3'
          }
        },
        silent: false,
        scaleLimit: {
          min: 1,
          max: 10
        },
        select: {
          itemStyle: {
            areaColor: '#1854a3'
          }
        },
        z: 0,
        animation: false, // 关闭地图动画
        animationDurationUpdate: 0
      },
      series: [
        {
          name: mapType === 'world' ? '国家分布' : '省份分布',
          type: 'map',
          geoIndex: 0,
          data: mapData,
          itemStyle: {
            normal: {
              areaColor: '#1D1E4C',
              borderColor: 'rgba(147, 235, 248, 0.3)',
              borderWidth: 1
            },
            emphasis: {
              areaColor: 'rgba(147, 235, 248, 0.5)',
              borderWidth: 1
            }
          },
          z: 1,
          roam: true,
          label: {
            show: false // 关闭标签显示
          },
          animation: false,
          large: true,
          silent: true // 禁用交互以提高性能
        },
        {
          name: '活跃节点',
          type: 'scatter',
          coordinateSystem: 'geo',
          data: activeNodesData,
          symbolSize: activeSymbolSize,
          symbol: 'circle',
          itemStyle: {
            color: '#ffeb3b'
          },
          large: true,
          largeThreshold: 1000,
          progressive: 500,
          progressiveThreshold: 1000,
          animation: false,
          blendMode: 'source-over',
          silent: true, // 禁用交互
          z: 10,
          zlevel: 1
        },
        {
          name: '非活跃节点',
          type: 'scatter',
          coordinateSystem: 'geo',
          data: inactiveNodesData,
          symbolSize: inactiveSymbolSize,
          symbol: 'circle',
          itemStyle: {
            color: '#ff5252'
          },
          large: true,
          largeThreshold: 1000,
          progressive: 500,
          progressiveThreshold: 1000,
          animation: false,
          blendMode: 'source-over',
          silent: true, // 禁用交互
          z: 9,
          zlevel: 1
        }
      ]
    };

    // 优化更新策略
    this.chart.setOption(option, {
      notMerge: true, // 完全替换配置
      lazyUpdate: true,
      silent: true,
      animation: false
    });
  };

  // 添加数据采样方法
  sampleData = (data, maxPoints) => {
    if (data.length <= maxPoints) return data;
    
    const step = Math.ceil(data.length / maxPoints);
    return data.filter((_, index) => index % step === 0);
  };

  renderStats = () => {
    const { countryDistribution, renderedActiveNodes, renderedInactiveNodes, totalNodes, activeNodes } = this.state;
    // 按节点数量排序
    const sortedCountries = Object.keys(countryDistribution).sort(
      (a, b) => countryDistribution[b] - countryDistribution[a]
    ).slice(0, 10);

    return (
      <div style={{
        position: 'absolute',
        top: '60px',
        right: '20px',
        background: 'rgba(15, 28, 60, 0.8)',
        padding: '10px',
        borderRadius: '5px',
        color: '#fff',
        maxWidth: '300px',
        boxShadow: '0 0 10px rgba(0,0,0,0.5)',
        zIndex: 100
      }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', borderBottom: '1px solid #3a5998' }}>
          节点统计
        </h3>
        <div style={{ marginBottom: '10px', fontSize: '14px', color: '#aaa' }}>
          <div>总节点数: {totalNodes}</div>
          <div>活跃节点总数: {activeNodes}</div>
          <div style={{ color: '#ffeb3b' }}>当前渲染活跃节点: {renderedActiveNodes}</div>
          <div style={{ color: '#ff5252' }}>当前渲染非活跃节点: {renderedInactiveNodes}</div>
          <div style={{ color: '#00a8ff' }}>当前总渲染节点: {renderedActiveNodes + renderedInactiveNodes}</div>
        </div>
        <h3 style={{ margin: '10px 0', fontSize: '16px', borderBottom: '1px solid #3a5998' }}>
          国家/地区分布 (Top 10)
        </h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {sortedCountries.map(country => (
            <div key={country} style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              padding: '5px 0',
              borderBottom: '1px solid rgba(255,255,255,0.1)'
            }}>
              <span>{country}</span>
              <span>{countryDistribution[country]} 个节点</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  renderProvinceStats = () => {
    const { nodeData, renderedActiveNodes, renderedInactiveNodes, totalNodes, activeNodes } = this.state;
    
    // 只筛选中国节点
    const chinaNodes = nodeData.filter(node => node.country === '中国');
    
    // 统计省份分布
    const provinceDistribution = {};
    chinaNodes.forEach(node => {
      if (node.province) {
        if (!provinceDistribution[node.province]) {
          provinceDistribution[node.province] = 0;
        }
        provinceDistribution[node.province]++;
      }
    });
    
    // 按节点数量排序
    const sortedProvinces = Object.keys(provinceDistribution).sort(
      (a, b) => provinceDistribution[b] - provinceDistribution[a]
    ).slice(0, 10);
    
    return (
      <div style={{
        position: 'absolute',
        top: '60px',
        right: '20px',
        background: 'rgba(15, 28, 60, 0.8)',
        padding: '10px',
        borderRadius: '5px',
        color: '#fff',
        maxWidth: '300px',
        boxShadow: '0 0 10px rgba(0,0,0,0.5)',
        zIndex: 100
      }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', borderBottom: '1px solid #3a5998' }}>
          节点统计
        </h3>
        <div style={{ marginBottom: '10px', fontSize: '14px', color: '#aaa' }}>
          <div>总节点数: {totalNodes}</div>
          <div>活跃节点总数: {activeNodes}</div>
          <div style={{ color: '#ffeb3b' }}>当前渲染活跃节点: {renderedActiveNodes}</div>
          <div style={{ color: '#ff5252' }}>当前渲染非活跃节点: {renderedInactiveNodes}</div>
          <div style={{ color: '#00a8ff' }}>当前总渲染节点: {renderedActiveNodes + renderedInactiveNodes}</div>
        </div>
        <h3 style={{ margin: '10px 0', fontSize: '16px', borderBottom: '1px solid #3a5998' }}>
          中国省份分布 (Top 10)
        </h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {sortedProvinces.map(province => (
            <div key={province} style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              padding: '5px 0',
              borderBottom: '1px solid rgba(255,255,255,0.1)'
            }}>
              <span>{province}</span>
              <span>{provinceDistribution[province]} 个节点</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  renderControls = () => {
    const { displayMode, pointSize } = this.state;
    
    return (
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        background: 'rgba(10, 30, 70, 0.9)', // 更深的背景色
        padding: '15px',
        borderRadius: '8px',
        color: '#fff',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)' // 添加阴影
      }}>
        <div style={{ fontSize: '14px', marginBottom: '5px', fontWeight: 'bold' }}>节点显示:</div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => this.toggleDisplayMode('all')}
            style={{
              padding: '8px 12px',
              background: displayMode === 'all' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: displayMode === 'all' ? 'bold' : 'normal',
              boxShadow: displayMode === 'all' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            全部节点
          </button>
          <button 
            onClick={() => this.toggleDisplayMode('active')}
            style={{
              padding: '8px 12px',
              background: displayMode === 'active' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: displayMode === 'active' ? 'bold' : 'normal',
              boxShadow: displayMode === 'active' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            仅活跃节点
          </button>
          <button 
            onClick={() => this.toggleDisplayMode('inactive')}
            style={{
              padding: '8px 12px',
              background: displayMode === 'inactive' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: displayMode === 'inactive' ? 'bold' : 'normal',
              boxShadow: displayMode === 'inactive' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            仅非活跃节点
          </button>
        </div>
        
        <div style={{ fontSize: '14px', marginBottom: '5px', marginTop: '5px', fontWeight: 'bold' }}>节点大小:</div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => this.setPointSize('small')}
            style={{
              padding: '8px 12px',
              background: pointSize === 'small' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: pointSize === 'small' ? 'bold' : 'normal',
              boxShadow: pointSize === 'small' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            小
          </button>
          <button 
            onClick={() => this.setPointSize('medium')}
            style={{
              padding: '8px 12px',
              background: pointSize === 'medium' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: pointSize === 'medium' ? 'bold' : 'normal',
              boxShadow: pointSize === 'medium' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            中
          </button>
          <button 
            onClick={() => this.setPointSize('large')}
            style={{
              padding: '8px 12px',
              background: pointSize === 'large' ? '#00a8ff' : 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: pointSize === 'large' ? 'bold' : 'normal',
              boxShadow: pointSize === 'large' ? '0 0 8px #00a8ff' : 'none' // 添加发光效果
            }}
          >
            大
          </button>
        </div>
        
        <div style={{ fontSize: '12px', color: '#a3d8ff', marginTop: '5px' }}>
          提示: 放大地图可查看更多节点细节
        </div>
      </div>
    );
  };

  render() {
    const { loading, error, nodeData, mapType } = this.state;

    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        {loading && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#fff',
            background: 'rgba(0,0,0,0.8)',
            padding: '20px 40px',
            borderRadius: '8px',
            zIndex: 1000,
            boxShadow: '0 0 20px rgba(0,150,255,0.3)' // 添加蓝色发光效果
          }}>
            <div style={{ fontSize: '18px', marginBottom: '15px', textAlign: 'center' }}>加载中...</div>
            <div style={{ width: '60px', height: '60px', border: '5px solid rgba(255,255,255,0.2)', 
                         borderTop: '5px solid #00a8ff', borderRadius: '50%',
                         margin: '0 auto', animation: 'spin 1.5s linear infinite' }}></div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}
        {error && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#ff4757',
            background: 'rgba(0,0,0,0.8)',
            padding: '20px',
            borderRadius: '8px',
            zIndex: 1,
            boxShadow: '0 0 20px rgba(255,0,0,0.3)' // 添加红色发光效果
          }}>
            {error}
          </div>
        )}
        <button 
          onClick={this.toggleMapType}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            zIndex: 100,
            padding: '10px 18px',
            background: 'linear-gradient(to right, #00a8ff, #0097e6)', // 渐变背景
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
            fontWeight: 'bold',
            transition: 'all 0.2s ease'
          }}
        >
          切换到{this.state.mapType === 'world' ? '中国' : '全球'}视图
        </button>
        {nodeData && mapType === 'world' && this.renderStats()}
        {nodeData && mapType === 'china' && this.renderProvinceStats()}
        {nodeData && this.renderControls()}
        <div
          ref={this.chartRef}
          style={{
            width: '100%',
            height: '100%',
            minHeight: '600px'
          }}
        />
      </div>
    );
  }
}

export default NodeDistribution; 
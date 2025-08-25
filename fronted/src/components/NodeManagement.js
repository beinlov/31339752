import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import StatCard from './common/StatCard';
import ChartCard from './common/ChartCard';
import { getUserLocation } from '../utils/index';

// 样式定义
const Container = styled.div`
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 0px;
  box-sizing: border-box;
  margin-top: -1.5%;
  position: relative;
`;

const TopBar = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 0px;
  padding: 20px;
  flex-shrink: 0;
`;

const Select = styled.select`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 180px;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="6"><path d="M0 0l6 6 6-6z" fill="%23333"/></svg>');
  background-repeat: no-repeat;
  background-position: right 15px center;
  background-size: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  cursor: pointer;

  &:focus {
    border-color: #1a237e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
  }

  &:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
    opacity: 0.7;
  }

  option {
    padding: 10px;
    font-size: 14px;
  }
`;

const SearchInput = styled.input`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 250px;
  margin-left: -1.5%;
  transition: all 0.3s ease;
  font-size: 14px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%23999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>');
  background-repeat: no-repeat;
  background-position: 12px center;
  padding-left: 40px;

  &:focus {
    border-color: #1a237e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
    width: 280px;
  }

  &::placeholder {
    color: #aaa;
  }
`;

const Button = styled.button`
  padding: 12px 18px;
  border-radius: 8px;
  border: none;
  background: ${props => props.active ? '#1a237e' : '#f5f5f5'};
  color: ${props => props.active ? 'white' : '#333'};
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: ${props => props.active ? '0 4px 10px rgba(26, 35, 126, 0.2)' : 'none'};

  &:hover {
    background: ${props => props.active ? '#0d1642' : '#e0e0e0'};
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  &:active {
    transform: translateY(0);
    box-shadow: none;
  }

  &:disabled {
    background: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const TableContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 0;
  position: relative;
  display: flex;
  flex-direction: column;
`;

const Table = styled.div`
  width: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
`;

const TableHeader = styled.div`
  display: grid;
  grid-template-columns: 60px 180px 160px 1fr 120px;
  padding: 16px;
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
  z-index: 1;

  > div {
    padding: 0 10px;
    display: flex;
    align-items: center;

    &:hover {
      cursor: pointer;
      background: rgba(0, 0, 0, 0.05);
      border-radius: 4px;
    }
  }
`;

const TableRow = styled.div`
  display: grid;
  grid-template-columns: 60px 180px 160px 1fr 120px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  transition: all 0.2s ease;
  opacity: ${props => props.disabled ? 0.5 : 1};
  background: ${props => props.disabled ? '#f9f9f9' : 'white'};

  &:hover {
    background: ${props => !props.disabled && '#f0f4ff'};
    transform: ${props => !props.disabled && 'translateY(-1px)'};
    box-shadow: ${props => !props.disabled && '0 2px 5px rgba(0, 0, 0, 0.05)'};
  }

  > div {
    padding: 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
`;

const LocationInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;

  .location-primary {
    font-weight: 500;
    color: #333;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .location-secondary {
    font-size: 0.85em;
    color: #666;
    margin-left: 22px;
  }

  .coordinates {
    font-size: 0.75em;
    color: #888;
    margin-left: 22px;
    font-family: monospace;
  }
`;

const TimeInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;

  .time-absolute {
    font-size: 0.9em;
    color: #333;
  }

  .time-relative {
    font-size: 0.8em;
    color: #666;
  }
`;

const IpContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;

  .ip-address {
    font-family: monospace;
    font-weight: 500;
  }

  .ip-copy {
    font-size: 0.75em;
    color: #1a237e;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  &:hover .ip-copy {
    opacity: 1;
  }
`;

const Pagination = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 20px;
  flex-shrink: 0;
  background: white;
  border-top: 1px solid #eee;
`;

const PageButton = styled.button`
  padding: 8px 14px;
  border: 1px solid #ddd;
  background: ${props => props.active ? '#1a237e' : 'white'};
  color: ${props => props.active ? 'white' : '#333'};
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 6px;
  font-weight: ${props => props.active ? '600' : '400'};

  &:hover {
    background: ${props => props.active ? '#1a237e' : '#f5f5f5'};
    transform: translateY(-2px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }

  &:disabled {
    background: ${props => props.active ? '#1a237e' : '#f5f5f5'};
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
    box-shadow: none;
  }
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
  flex-shrink: 0;
`;

const ChartsContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  flex-shrink: 0;
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 500;
  background-color: ${props => props.status === '在线' ? '#e8f5e9' : '#ffebee'};
  color: ${props => props.status === '在线' ? '#2e7d32' : '#c62828'};
  border: 1px solid ${props => props.status === '在线' ? '#a5d6a7' : '#ef9a9a'};

  &::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: ${props => props.status === '在线' ? '#2e7d32' : '#c62828'};
    margin-right: 6px;
    animation: ${props => props.status === '在线' ? 'pulse 2s infinite' : 'none'};
  }

  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7);
    }
    70% {
      box-shadow: 0 0 0 6px rgba(46, 125, 50, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(46, 125, 50, 0);
    }
  }
`;

const CountryFlag = styled.span`
  display: inline-block;
  margin-right: 8px;
  font-size: 1.2em;
`;

// 国家/地区对应的旗帜emoji
const countryFlags = {
  '中国': '🇨🇳',
  '美国': '🇺🇸',
  '日本': '🇯🇵',
  '韩国': '🇰🇷',
  '俄罗斯': '🇷🇺',
  '德国': '🇩🇪',
  '法国': '🇫🇷',
  '加拿大': '🇨🇦',
  '英国': '🇬🇧',
  '澳大利亚': '🇦🇺',
  '印度': '🇮🇳',
  '巴西': '🇧🇷',
  '新加坡': '🇸🇬',
  '马来西亚': '🇲🇾'
};

// 操作系统对应的图标
const getOsIcon = (os) => {
  if (os.includes('Windows')) return '🪟';
  if (os.includes('Ubuntu') || os.includes('Linux')) return '🐧';
  if (os.includes('macOS')) return '🍎';
  return '💻';
};

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  backdrop-filter: blur(2px);
`;

const Spinner = styled.div`
  border: 4px solid rgba(26, 35, 126, 0.1);
  border-radius: 50%;
  border-top: 4px solid #1a237e;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// 保留 Checkbox 样式组件
const Checkbox = styled.input.attrs({ type: 'checkbox' })`
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  width: 20px;
  height: 20px;
  accent-color: #1a237e;
  transition: all 0.2s ease;

  &:hover {
    transform: ${props => !props.disabled && 'scale(1.1)'};
  }
`;

// 辅助函数：获取相对时间
const getRelativeTime = (date) => {
  const now = new Date();
  const diff = now - date;

  // 处理无效日期
  if (isNaN(diff)) {
    return '未知时间';
  }

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 30) {
    return `${Math.floor(days / 30)} 个月前`;
  }
  if (days > 0) {
    return `${days} 天前`;
  }
  if (hours > 0) {
    return `${hours} 小时前`;
  }
  if (minutes > 0) {
    return `${minutes} 分钟前`;
  }
  return '刚刚';
};

const NodeManagement = ({ networkType: propNetworkType }) => {
  const [nodes, setNodes] = useState([]);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [operation, setOperation] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [filter, setFilter] = useState('all'); // 'all', 'online', 'offline'
  const [isOnlineActive, setIsOnlineActive] = useState(false);
  const [isOfflineActive, setIsOfflineActive] = useState(false);
  const [isSelectAllActive, setIsSelectAllActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [networkType, setNetworkType] = useState(propNetworkType || 'asruex');
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(100); // 符合API要求的最小页面大小
  const [displayLimit] = useState(20); // 实际在UI中显示的条数
  const [nodeStats, setNodeStats] = useState({
    totalNodes: 0,
    onlineNodes: 0,
    offlineNodes: 0,
    countryDistribution: {},
    selectedCount: 0
  });

  // 当从 props 接收到新的 networkType 时更新本地状态
  useEffect(() => {
    if (propNetworkType && propNetworkType !== networkType) {
      setNetworkType(propNetworkType);
    }
  }, [propNetworkType]);

  // 统一的数据获取 effect
  useEffect(() => {
    if (networkType) {
      console.log(`获取节点数据: networkType=${networkType}, page=${currentPage}, pageSize=${pageSize}, filter=${filter}`);
      fetchNodesData();
    }
  }, [networkType, currentPage, pageSize, filter]); // 依赖项包含所有会触发重新获取的状态

  // 根据不同网络类型获取节点数据
  const fetchNodesData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 构建查询参数
      const params = new URLSearchParams({
        botnet_type: networkType,
        page: currentPage,
        page_size: pageSize,
      });

      // 添加过滤条件
      if (filter === 'online') {
        params.append('status', 'active');
      } else if (filter === 'offline') {
        params.append('status', 'inactive');
      }

      // 如果有搜索词且看起来是国家名，添加country过滤
      if (searchTerm && !searchTerm.match(/^[0-9.]+$/)) {
        params.append('country', searchTerm);
      }

      const endpoint = `/api/node-details?${params.toString()}`;
      console.log(`请求接口: ${endpoint}`);

      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`获取节点数据失败: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.data || !result.data.nodes) {
        throw new Error('返回的节点数据格式不正确');
      }

      // 转换数据格式
      const formattedNodes = result.data.nodes.map(node => ({
        id: node.id,
        ip: node.ip,
        country: node.country || '未知',
        province: node.province || '',
        city: node.city || '',
        status: node.status === 'active' ? '在线' : '下线',
        longitude: node.longitude,
        latitude: node.latitude,
        lastSeen: node.last_active
      }));

      setNodes(formattedNodes);
      setTotalPages(result.data.pagination.total_pages);
      setTotalCount(result.data.pagination.total_count);

      // 更新统计信息
      const statistics = result.data.statistics;
      setNodeStats({
        totalNodes: statistics.active_nodes + statistics.inactive_nodes,
        onlineNodes: statistics.active_nodes,
        offlineNodes: statistics.inactive_nodes,
        countryDistribution: statistics.country_distribution,
        selectedCount: selectedNodes.length
      });

    } catch (error) {
      console.error('Error fetching nodes:', error);
      setError(error.message);
      setNodes([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 更新选中节点数量
  useEffect(() => {
    setNodeStats(prev => ({
      ...prev,
      selectedCount: selectedNodes.length
    }));
  }, [selectedNodes]);

  // 过滤和分页逻辑
  const filteredNodes = (nodes || []).filter(node => {
    const matchesSearch =
      node.country?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.ip?.includes(searchTerm);
    const matchesFilter =
      filter === 'all' ? true :
      filter === 'online' ? node.status === '在线' :
      filter === 'offline' ? node.status === '下线' : true;
    return matchesSearch && matchesFilter;
  });

  // 本地分页，只显示前displayLimit条
  const displayedNodes = filteredNodes.slice(0, displayLimit);

  // 处理节点选择
  const handleNodeSelect = (nodeId) => {
    if (selectedNodes.includes(nodeId)) {
      setSelectedNodes(selectedNodes.filter(id => id !== nodeId));
    } else {
      setSelectedNodes([...selectedNodes, nodeId]);
    }
  };

  // 处理全选
  const handleSelectAll = () => {
    const availableNodes = nodes.filter(node => node.status === '在线').map(node => node.id);
    if (selectedNodes.length === availableNodes.length) {
      setSelectedNodes([]);
      setIsSelectAllActive(false);
    } else {
      setSelectedNodes(availableNodes);
      setIsSelectAllActive(true);
    }
  };

  // 处理在线/下线过滤
  const handleFilterChange = (newFilter) => {
    if (newFilter === 'online') {
      if (isOnlineActive) {
        setFilter('all');
        setIsOnlineActive(false);
      } else {
        setFilter('online');
        setIsOnlineActive(true);
        setIsOfflineActive(false);
      }
    } else if (newFilter === 'offline') {
      if (isOfflineActive) {
        setFilter('all');
        setIsOfflineActive(false);
      } else {
        setFilter('offline');
        setIsOfflineActive(true);
        setIsOnlineActive(false);
      }
    }
    setCurrentPage(1);
  };

  // 根据国家生成模拟操作系统数据
  const getOSFromCountry = (country) => {
    // 生成随机操作系统，但保持一定的分布规律
    const rand = Math.random();
    if (country === '中国') {
      if (rand < 0.6) return 'Windows 10';
      if (rand < 0.8) return 'Windows 7';
      if (rand < 0.9) return 'Ubuntu 20.04';
      return 'macOS';
    } else if (country === '美国') {
      if (rand < 0.4) return 'Windows 10';
      if (rand < 0.6) return 'Windows 11';
      if (rand < 0.8) return 'macOS';
      return 'Ubuntu 22.04';
    } else if (country === '日本' || country === '韩国') {
      if (rand < 0.7) return 'Windows 10';
      if (rand < 0.9) return 'macOS';
      return 'Ubuntu 20.04';
    } else if (country === '德国' || country === '法国' || country === '英国') {
      if (rand < 0.5) return 'Windows 10';
      if (rand < 0.7) return 'Windows 11';
      if (rand < 0.9) return 'Ubuntu 22.04';
      return 'macOS';
    }

    // 默认分布
    if (rand < 0.5) return 'Windows 10';
    if (rand < 0.7) return 'Windows 11';
    if (rand < 0.9) return 'Ubuntu 20.04';
    return 'macOS';
  };

  // 处理节点清除/抑制操作
  const handleOperation = async () => {
    if (!operation || selectedNodes.length === 0) return;

    setIsLoading(true);
    try {
      const endpoint = '/api/clean-botnet';

      // 获取选中节点的IP地址
      const selectedIPs = selectedNodes.map(nodeId =>
        nodes.find(node => node.id === nodeId)?.ip
      ).filter(ip => ip);

      // 获取操作者的IP地理位置
      const locationInfo = await getUserLocation();
      console.log('操作者IP地理位置:', locationInfo);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          botnet_type: networkType,
          target_machines: selectedIPs,
          clean_method: operation,
          username: localStorage.getItem('username') || 'admin',
          location: locationInfo.location,
          operator_ip: locationInfo.ip  // 添加操作者IP
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Operation failed');
      }

      const result = await response.json();

      // 显示操作已开始的提示
      alert(`操作已开始: ${result.message}\n影响节点数: ${result.affected_machines}\n\n清理过程将在后台继续，您可以继续使用系统。`);

      // 重置选择状态
      setSelectedNodes([]);
      setOperation('');

      // 延迟一段时间后刷新数据，让后台有时间处理一部分
      setTimeout(async () => {
        await fetchNodesData();
      }, 5000);

      // 设置定时刷新，以便看到后台处理的进度
      const refreshInterval = setInterval(async () => {
        await fetchNodesData();
      }, 10000); // 每10秒刷新一次

      // 60秒后停止自动刷新
      setTimeout(() => {
        clearInterval(refreshInterval);
      }, 60000);

    } catch (error) {
      console.error('Error during operation:', error);
      alert(`操作失败: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 准备图表数据
  const getLocationChartOption = () => ({
    title: {
      text: '节点地理分布',
      left: 'center',
      textStyle: {
        fontWeight: 'normal',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20,
      data: Array.from(new Set(nodes.map(node => node.country)))
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '18',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: Array.from(
        nodes.reduce((acc, node) => {
          acc.set(node.country, (acc.get(node.country) || 0) + 1);
          return acc;
        }, new Map())
      ).map(([name, value]) => ({
        name,
        value,
        label: {
          formatter: '{b}: {c} ({d}%)'
        }
      }))
    }]
  });

  const getStatusChartOption = () => ({
    title: {
      text: '节点状态分布',
      left: 'center',
      textStyle: {
        fontWeight: 'normal',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: ['在线', '下线'],
      axisLabel: {
        formatter: function(value) {
          return value === '在线' ? '🟢 在线' : '🔴 下线';
        }
      }
    },
    series: [{
      name: '节点数量',
      type: 'bar',
      data: [
        {
          value: nodes.filter(node => node.status === '在线').length,
          itemStyle: { color: '#2e7d32' }
        },
        {
          value: nodes.filter(node => node.status === '下线').length,
          itemStyle: { color: '#c62828' }
        }
      ],
      showBackground: true,
      backgroundStyle: {
        color: 'rgba(180, 180, 180, 0.1)'
      }
    }]
  });

  useEffect(() => {
    // 如果执行了操作，更新选择状态
    if (operation && selectedNodes.length > 0) {
      handleOperation();
    }
  }, [operation]);

  return (
    <Container>
      <StatsContainer>
        <StatCard
          title="总节点数"
          value={nodeStats.totalNodes}
          trend="全部节点"
          background="linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)"
          titleIcon="📊"
        />
        <StatCard
          title="在线节点"
          value={nodeStats.onlineNodes}
          trend={`${((nodeStats.onlineNodes / nodeStats.totalNodes) * 100).toFixed(1)}% 在线率`}
          background="linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)"
          titleIcon="🟢"
        />
        <StatCard
          title="下线节点"
          value={nodeStats.offlineNodes}
          trend={`${((nodeStats.offlineNodes / nodeStats.totalNodes) * 100).toFixed(1)}% 下线率`}
          background="linear-gradient(135deg, #c62828 0%, #b71c1c 100%)"
          titleIcon="🔴"
        />
        <StatCard
          title="已选节点"
          value={nodeStats.selectedCount}
          trend={`${nodeStats.onlineNodes > 0 ? ((nodeStats.selectedCount / nodeStats.onlineNodes) * 100).toFixed(1) : 0}% 选中率`}
          background="linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)"
          titleIcon="✓"
        />
      </StatsContainer>

      <ChartsContainer>
        <ChartCard
          option={getLocationChartOption()}
          height="300px"
          accentColor="linear-gradient(90deg, #1a237e, #0d47a1)"
          loading={isLoading ? true : undefined}
        />
        <ChartCard
          option={getStatusChartOption()}
          height="300px"
          accentColor="linear-gradient(90deg, #2e7d32, #1b5e20)"
          loading={isLoading ? true : undefined}
        />
      </ChartsContainer>

      <TopBar>
        <SearchInput
          placeholder="搜索IP/国家/操作系统"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Button
          active={isOnlineActive}
          onClick={() => handleFilterChange('online')}
        >
          <span>🟢</span> 在线节点
        </Button>
        <Button
          active={isOfflineActive}
          onClick={() => handleFilterChange('offline')}
        >
          <span>🔴</span> 下线节点
        </Button>
        <Button
          active={isSelectAllActive}
          onClick={handleSelectAll}
        >
          <span>✓</span> 一键勾选
        </Button>
        <Select
          value={operation}
          onChange={(e) => setOperation(e.target.value)}
          disabled={isLoading || selectedNodes.length === 0}
        >
          <option value="">操作节点</option>
          <option value="clear">清除</option>
          <option value="reuse">再利用</option>
          <option value="ddos">DDos攻击</option>
        </Select>
      </TopBar>

      <TableContainer>
        <Table>
          <TableHeader>
            <div>选择</div>
            <div>IP地址</div>
            <div>状态</div>
            <div>地理位置</div>
            <div>最后活动</div>
          </TableHeader>
          {displayedNodes.map(node => (
            <TableRow key={node.id} disabled={node.status === '下线'}>
              <div>
                <Checkbox
                  checked={selectedNodes.includes(node.id)}
                  onChange={() => handleNodeSelect(node.id)}
                  disabled={node.status === '下线'}
                />
              </div>
              <div>
                <IpContainer>
                  <span className="ip-address">{node.ip}</span>
                  <span
                    className="ip-copy"
                    onClick={() => {
                      navigator.clipboard.writeText(node.ip);
                      alert('IP已复制到剪贴板');
                    }}
                  >
                    复制IP
                  </span>
                </IpContainer>
              </div>
              <div>
                <StatusBadge status={node.status}>
                  {node.status}
                </StatusBadge>
              </div>
              <LocationInfo>
                <div className="location-primary">
                  <CountryFlag>{countryFlags[node.country] || '🌐'}</CountryFlag>
                  {node.country}
                </div>
                {(node.province || node.city) && (
                  <div className="location-secondary">
                    {[node.province, node.city].filter(Boolean).join(' - ')}
                  </div>
                )}
                {(node.longitude && node.latitude) && (
                  <div className="coordinates">
                    {node.longitude.toFixed(4)}° E, {node.latitude.toFixed(4)}° N
                  </div>
                )}
              </LocationInfo>
              <TimeInfo>
                <div className="time-absolute">
                  {new Date(node.lastSeen).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
                <div className="time-relative">
                  {getRelativeTime(new Date(node.lastSeen))}
                </div>
              </TimeInfo>
            </TableRow>
          ))}
        </Table>

        {isLoading && (
          <LoadingOverlay>
            <Spinner />
            <div style={{ fontWeight: 500, color: '#1a237e' }}>正在处理...</div>
          </LoadingOverlay>
        )}
      </TableContainer>

      <Pagination>
        <PageButton
          onClick={() => setCurrentPage(1)}
          disabled={currentPage === 1 || isLoading}
        >
          首页
        </PageButton>
        <PageButton
          onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          disabled={currentPage === 1 || isLoading}
        >
          上一页
        </PageButton>
        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
          let pageToShow;
          if (totalPages <= 5) {
            pageToShow = i + 1;
          } else if (currentPage <= 3) {
            pageToShow = i + 1;
          } else if (currentPage >= totalPages - 2) {
            pageToShow = totalPages - 4 + i;
          } else {
            pageToShow = currentPage - 2 + i;
          }
          return (
            <PageButton
              key={pageToShow}
              active={currentPage === pageToShow}
              onClick={() => setCurrentPage(pageToShow)}
              disabled={isLoading}
            >
              {pageToShow}
            </PageButton>
          );
        })}
        <PageButton
          onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          disabled={currentPage === totalPages || isLoading}
        >
          下一页
        </PageButton>
        <PageButton
          onClick={() => setCurrentPage(totalPages)}
          disabled={currentPage === totalPages || isLoading}
        >
          末页
        </PageButton>
        <span style={{ marginLeft: '10px', color: '#666' }}>
          共 {totalCount} 条记录，{totalPages} 页，每页 {displayLimit} 条显示（API加载 {pageSize} 条）
        </span>
      </Pagination>

      {error && (
        <div style={{
          color: 'red',
          textAlign: 'center',
          padding: '20px',
          backgroundColor: '#ffebee',
          borderRadius: '8px',
          margin: '10px 0',
          border: '1px solid #ef9a9a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '20px' }}>⚠️</span>
          {error}
        </div>
      )}
    </Container>
  );
};

export default NodeManagement;

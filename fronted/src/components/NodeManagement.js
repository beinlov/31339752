import React, { useState, useEffect, useMemo } from 'react';
import styled from 'styled-components';
import StatCard from './common/StatCard';
import ChartCard from './common/ChartCard';

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
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  color: #e0e0e0;
  width: 180px;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="6"><path d="M0 0l6 6 6-6z" fill="%2364b5f6"/></svg>');
  background-repeat: no-repeat;
  background-position: right 15px center;
  background-size: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(26, 115, 232, 0.2);

  &:focus {
    border-color: #1a73e8;
    outline: none;
    box-shadow: 0 0 15px rgba(26, 115, 232, 0.4);
  }

  &:disabled {
    background-color: rgba(100, 100, 100, 0.3);
    cursor: not-allowed;
    opacity: 0.7;
  }

  option {
    padding: 10px;
    font-size: 14px;
    background: #0d47a1;
    color: white;
  }
`;

const SearchInput = styled.input`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  color: #e0e0e0;
  width: 250px;
  margin-left: -1.5%;
  transition: all 0.3s ease;
  font-size: 14px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%2364b5f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>');
  background-repeat: no-repeat;
  background-position: 12px center;
  padding-left: 40px;
  box-shadow: 0 0 10px rgba(26, 115, 232, 0.2);

  &:focus {
    border-color: #1a73e8;
    outline: none;
    box-shadow: 0 0 15px rgba(26, 115, 232, 0.4);
    width: 280px;
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const Button = styled.button`
  padding: 12px 18px;
  border-radius: 8px;
  border: 1px solid ${props => props.active ? 'rgba(100, 181, 246, 0.5)' : 'rgba(100, 181, 246, 0.2)'};
  background: ${props => props.active ? 'linear-gradient(90deg, #1565c0, #1a73e8)' : 'rgba(26, 115, 232, 0.1)'};
  color: ${props => props.active ? 'white' : '#8db4d8'};
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: ${props => props.active ? '0 0 15px rgba(26, 115, 232, 0.4)' : '0 0 10px rgba(26, 115, 232, 0.1)'};

  &:hover {
    background: ${props => props.active ? 'linear-gradient(90deg, #0d47a1, #1565c0)' : 'rgba(26, 115, 232, 0.2)'};
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(26, 115, 232, 0.5);
    border-color: rgba(100, 181, 246, 0.6);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: rgba(100, 100, 100, 0.3);
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
  max-height: calc(100vh - 650px);
`;

const Table = styled.div`
  width: 100%;
  background: linear-gradient(135deg, rgba(15, 25, 35, 0.95) 0%, rgba(26, 35, 50, 0.95) 100%);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(26, 115, 232, 0.2);
  border: 1px solid rgba(100, 181, 246, 0.2);
`;

const TableHeader = styled.div`
  display: grid;
  grid-template-columns: 60px 220px 1fr 200px;
  padding: 16px;
  background: linear-gradient(90deg, rgba(13, 71, 161, 0.3), rgba(21, 101, 192, 0.3));
  border-bottom: 2px solid rgba(100, 181, 246, 0.3);
  font-weight: 600;
  color: #64b5f6;
  position: sticky;
  top: 0;
  z-index: 1;
  box-shadow: 0 2px 10px rgba(26, 115, 232, 0.2);

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
  grid-template-columns: 60px 220px 1fr 200px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(100, 181, 246, 0.1);
  transition: all 0.2s ease;
  opacity: ${props => props.disabled ? 0.5 : 1};
  background: ${props => props.disabled ? 'rgba(26, 115, 232, 0.05)' : 'transparent'};
  color: #e0e0e0;

  &:hover {
    background: ${props => !props.disabled && 'rgba(26, 115, 232, 0.15)'};
    transform: ${props => !props.disabled && 'translateY(-1px)'};
    box-shadow: ${props => !props.disabled && '0 2px 8px rgba(26, 115, 232, 0.2)'};
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
    color: #f5f9ff;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .location-secondary {
    font-size: 0.85em;
    color: rgba(255, 255, 255, 0.8);
    margin-left: 22px;
  }

  .coordinates {
    font-size: 0.75em;
    color: rgba(255, 255, 255, 0.7);
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
    color: #f5f9ff;
    font-weight: 500;
  }

  .time-relative {
    font-size: 0.8em;
    color: rgba(255, 255, 255, 0.75);
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
  grid-template-columns: repeat(2, 1fr);
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

const formatDateTime = (value) => {
  if (!value) return '未知';
  const date = new Date(value);
  if (isNaN(date.getTime())) return '未知';

  const pad = (num) => String(num).padStart(2, '0');
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());

  return `${year}/${month}/${day} ${hours}:${minutes}`;
};

const NodeManagement = ({ networkType: propNetworkType }) => {
  const [nodes, setNodes] = useState([]);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState(''); // 筛选方式: 'ip', 'country', 'last_active'
  const [isSelectAllActive, setIsSelectAllActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [networkType, setNetworkType] = useState(propNetworkType || 'asruex');
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(100); // 符合API要求的最小页面大小
  const [nodeStats, setNodeStats] = useState({
    totalNodes: 0,
    onlineNodes: 0,
    offlineNodes: 0,
    countryDistribution: {},
    selectedCount: 0
  });

  // 独立的图表统计数据（完整数据，不受分页影响）
  const [chartStats, setChartStats] = useState({
    totalNodes: 0,
    activeNodes: 0,
    inactiveNodes: 0,
    countryDistribution: {},
    statusDistribution: {}
  });

  // 当从 props 接收到新的 networkType 时更新本地状态
  useEffect(() => {
    if (propNetworkType && propNetworkType !== networkType) {
      setNetworkType(propNetworkType);
    }
  }, [propNetworkType]);

  // 获取图表统计数据（只在网络类型改变时获取，不受分页和勾选影响）
  useEffect(() => {
    if (networkType) {
      fetchChartStats();
    }
  }, [networkType]); // 只依赖 networkType

  // 统一的数据获取 effect（节点列表数据）
  useEffect(() => {
    if (networkType) {
      console.log(`获取节点数据: networkType=${networkType}, page=${currentPage}, pageSize=${pageSize}`);
      fetchNodesData();
    }
  }, [networkType, currentPage, pageSize]); // 依赖项包含所有会触发重新获取的状态

  // 获取完整的图表统计数据
  const fetchChartStats = async () => {
    try {
      const endpoint = `http://localhost:8000/api/node-stats/${networkType}`;
      console.log(`获取图表统计数据: ${endpoint}`);

      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`获取统计数据失败: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.data) {
        throw new Error('返回的统计数据格式不正确');
      }

      // 更新图表数据
      const newChartStats = {
        totalNodes: result.data.total_nodes || 0,
        activeNodes: result.data.active_nodes || 0,
        inactiveNodes: result.data.inactive_nodes || 0,
        countryDistribution: result.data.country_distribution || {},
        statusDistribution: result.data.status_distribution || {}
      };
      
      console.log('图表统计数据更新完成:', result.data);
      console.log('country_distribution 内容:', result.data.country_distribution);
      console.log('country_distribution 类型:', typeof result.data.country_distribution);
      console.log('country_distribution 条目数:', Object.keys(result.data.country_distribution || {}).length);
      
      setChartStats(newChartStats);

    } catch (error) {
      console.error('获取图表统计数据失败:', error);
      // 不影响主数据，只记录错误
    }
  };

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

      // 如果有搜索词且看起来是国家名，添加country过滤
      if (searchTerm && !searchTerm.match(/^[0-9.]+$/)) {
        params.append('country', searchTerm);
      }

      const endpoint = `http://localhost:8000/api/node-details?${params.toString()}`;
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
      // 去重：按 IP 保留最新记录
      const mapByIp = new Map();
      for (const node of result.data.nodes) {
        const key = node.ip || '';
        const current = mapByIp.get(key);
        if (!current) {
          mapByIp.set(key, node);
        } else {
          // 选择最近的 last_active
          const curTime = new Date(current.last_active || 0).getTime();
          const newTime = new Date(node.last_active || 0).getTime();
          if (newTime >= curTime) {
            mapByIp.set(key, node);
          }
        }
      }

      const formattedNodes = Array.from(mapByIp.values()).map(node => {
        const lastSeenRaw = node.last_active;
        return {
          id: node.id,
          ip: node.ip,
          country: node.country || '未知',
          province: node.province || '',
          city: node.city || '',
          status: node.status === 'active' ? '在线' : '下线',
          longitude: node.longitude,
          latitude: node.latitude,
          lastSeen: lastSeenRaw,
          lastSeenFormatted: formatDateTime(lastSeenRaw)
        };
      });

      setNodes(formattedNodes);
      setTotalPages(result.data.pagination.total_pages);
      setTotalCount(result.data.pagination.total_count);

      // 更新统计信息
      // 注意：这里使用chartStats中的总数（来自聚合表），而不是分页数据的total_count
      // 因为分页数据可能不完整，聚合表的数据与节点分布界面一致
      const statistics = result.data.statistics;
      setNodeStats({
        // 使用chartStats的数据（来自聚合表），与节点分布界面保持一致
        totalNodes: chartStats.totalNodes || result.data.pagination.total_count,
        onlineNodes: chartStats.activeNodes || statistics.active_nodes,
        offlineNodes: chartStats.inactiveNodes || statistics.inactive_nodes,
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
    const rawTerm = searchTerm.trim();
    const term = rawTerm.toLowerCase();

    if (!rawTerm) {
      return true;
    }

    if (sortBy === 'ip') {
      return (node.ip || '').toLowerCase().includes(term);
    }

    if (sortBy === 'country') {
      return [node.country, node.province, node.city]
        .filter(Boolean)
        .some(value => value.toLowerCase().includes(term));
    }

    if (sortBy === 'last_active') {
      return (node.lastSeenFormatted || '').includes(rawTerm);
    }

    return (node.ip || '').toLowerCase().includes(term) ||
      (node.country || '').toLowerCase().includes(term);
  });

  // 根据筛选方式调整排序
  const displayedNodes = useMemo(() => {
    const list = [...filteredNodes];
    if (sortBy === 'last_active') {
      list.sort((a, b) => {
        const timeA = new Date(a.lastSeen || 0).getTime();
        const timeB = new Date(b.lastSeen || 0).getTime();
        return timeB - timeA;
      });
    }
    return list;
  }, [filteredNodes, sortBy]);

  const searchPlaceholder = useMemo(() => {
    switch (sortBy) {
      case 'ip':
        return '按IP搜索，例如：192.168';
      case 'country':
        return '按国家/省份/城市搜索，例如：中国';
      case 'last_active':
        return '按最后活跃日期搜索，例如：2025/12/11';
      default:
        return '搜索IP/国家/操作系统';
    }
  }, [sortBy]);

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

  // 准备图表数据 - 使用 useMemo 缓存，避免不必要的重新渲染
  const getLocationChartOption = useMemo(() => {
    // 使用完整的统计数据，而不是分页数据
    const distribution = chartStats.countryDistribution || {};
    
    // 调试日志
    console.log('饼状图数据源 chartStats.countryDistribution:', distribution);
    console.log('数据条目数:', Object.keys(distribution).length);
    
    const countryData = Object.entries(distribution)
      .map(([name, value]) => ({
        name,
        value,
        label: {
          formatter: '{b}: {c} ({d}%)'
        }
      }))
      .sort((a, b) => b.value - a.value); // 按数量排序

    console.log('处理后的饼图数据:', countryData);

    // 如果没有数据，返回空状态配置
    if (countryData.length === 0) {
      return {
        title: {
          text: '节点地理分布',
          left: 'center',
          textStyle: {
            fontWeight: 'normal',
            fontSize: 16
          }
        },
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无数据',
            fontSize: 16,
            fill: '#999'
          }
        }
      };
    }

    return {
      title: {
        text: '节点地理分布',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16,
          color: '#ffffff'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `${params.name}: ${params.value} (${params.percent}%)`;
        }
      },
      legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 10,
        top: 20,
        bottom: 20,
        data: countryData.map(item => item.name),
        textStyle: {
          color: '#ffffff'
        }
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
        data: countryData
      }]
    };
  }, [chartStats.countryDistribution]); // 只依赖图表数据，不依赖节点列表或勾选状态

  const getStatusChartOption = useMemo(() => {
    // 使用完整的统计数据
    const activeCount = chartStats.activeNodes || 0;
    const inactiveCount = chartStats.inactiveNodes || 0;

    return {
      title: {
        text: '节点状态分布',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16,
          color: '#ffffff'
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
        type: 'value',
        axisLabel: {
          color: '#ffffff'
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.3)'
          }
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      yAxis: {
        type: 'category',
        data: ['在线', '下线'],
        axisLabel: {
          color: '#ffffff',
          formatter: function(value) {
            return value === '在线' ? '🟢 在线' : '🔴 下线';
          }
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.3)'
          }
        }
      },
      series: [{
        name: '节点数量',
        type: 'bar',
        data: [
          {
            value: activeCount,
            itemStyle: { color: '#2e7d32' }
          },
          {
            value: inactiveCount,
            itemStyle: { color: '#c62828' }
          }
        ],
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.1)'
        }
      }]
    };
  }, [chartStats.activeNodes, chartStats.inactiveNodes]); // 只依赖图表统计数据

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
          title="已选节点"
          value={nodeStats.selectedCount}
          trend={`${nodeStats.onlineNodes > 0 ? ((nodeStats.selectedCount / nodeStats.onlineNodes) * 100).toFixed(1) : 0}% 选中率`}
          background="linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)"
          titleIcon="✓"
        />
      </StatsContainer>

      <ChartsContainer>
        <ChartCard
          option={getLocationChartOption}
          height="300px"
          accentColor="linear-gradient(90deg, #1a237e, #0d47a1)"
        />
        <ChartCard
          option={getStatusChartOption}
          height="300px"
          accentColor="linear-gradient(90deg, #2e7d32, #1b5e20)"
        />
      </ChartsContainer>

      <TopBar>
        <SearchInput
          placeholder={searchPlaceholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Button
          active={isSelectAllActive}
          onClick={handleSelectAll}
        >
          <span>✓</span> 一键勾选
        </Button>
        <Select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          disabled={isLoading}
        >
          <option value="">筛选节点</option>
          <option value="ip">IP</option>
          <option value="country">国家</option>
          <option value="last_active">最后活跃时间</option>
        </Select>
      </TopBar>

      <TableContainer>
        <Table>
          <TableHeader>
            <div>选择</div>
            <div>IP地址</div>
            <div>地理位置</div>
            <div>最近活跃时间</div>
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
              </div>
              <div>
                <TimeInfo>
                  <div className="time-absolute">
                    {node.lastSeenFormatted}
                  </div>
                  <div className="time-relative">
                    {getRelativeTime(new Date(node.lastSeen))}
                  </div>
                </TimeInfo>
              </div>
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
          共 {totalCount} 条记录，{totalPages} 页，当前页最多显示 {pageSize} 条
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

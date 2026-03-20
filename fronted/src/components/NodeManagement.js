import React, { useState, useEffect, useMemo } from 'react';
import styled from 'styled-components';
import { getApiUrl } from '../config/api';
import StatCard from './common/StatCard';
import ChartCard from './common/ChartCard';
import CommunicationModal from './CommunicationModal';

// 样式定义
const Container = styled.div`
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: row;
  padding: 0px;
  box-sizing: border-box;
  gap: 20px;
  position: relative;
`;

// 左侧面板 - 统计信息和图表
const LeftPanel = styled.div`
  width: 38%;
  min-width: 540px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 10px;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(10, 25, 41, 0.3);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(100, 181, 246, 0.3);
    border-radius: 3px;
  }
`;

// 右侧面板 - 搜索和表格
const RightPanel = styled.div`
  flex: 1;
  padding-left: 10px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
`;

const TopBar = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
`;

const Select = styled.select`
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  color: #e0e0e0;
  width: 140px;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="6"><path d="M0 0l6 6 6-6z" fill="%2364b5f6"/></svg>');
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 12px;
  font-size: 13px;
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
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  color: #e0e0e0;
  width: 220px;
  transition: all 0.3s ease;
  font-size: 13px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%2364b5f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>');
  background-repeat: no-repeat;
  background-position: 10px center;
  padding-left: 36px;
  box-shadow: 0 0 10px rgba(26, 115, 232, 0.2);

  &:focus {
    border-color: #1a73e8;
    outline: none;
    box-shadow: 0 0 15px rgba(26, 115, 232, 0.4);
    width: 260px;
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const Button = styled.button`
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid ${props => props.active ? 'rgba(100, 181, 246, 0.5)' : 'rgba(100, 181, 246, 0.2)'};
  background: ${props => props.active ? 'linear-gradient(90deg, #1565c0, #1a73e8)' : 'rgba(26, 115, 232, 0.1)'};
  color: ${props => props.active ? 'white' : '#8db4d8'};
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
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
  grid-template-columns: 115px 160px 125px 125px;
  padding: 10px 8px;
  background: linear-gradient(90deg, rgba(13, 71, 161, 0.3), rgba(21, 101, 192, 0.3));
  border-bottom: 2px solid rgba(100, 181, 246, 0.3);
  font-weight: 600;
  color: #64b5f6;
  position: sticky;
  top: 0;
  z-index: 1;
  box-shadow: 0 2px 10px rgba(26, 115, 232, 0.2);
  font-size: 11px;

  > div {
    padding: 0 4px;
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
  grid-template-columns: 115px 160px 125px 125px;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(100, 181, 246, 0.1);
  transition: all 0.2s ease;
  opacity: ${props => props.disabled ? 0.5 : 1};
  background: ${props => props.disabled ? 'rgba(26, 115, 232, 0.05)' : 'transparent'};
  color: #e0e0e0;
  font-size: 11px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};

  &:hover {
    background: ${props => !props.disabled && 'rgba(26, 115, 232, 0.15)'};
    transform: ${props => !props.disabled && 'translateY(-1px)'};
    box-shadow: ${props => !props.disabled && '0 2px 8px rgba(26, 115, 232, 0.2)'};
  }

  > div {
    padding: 0 4px;
    display: flex;
    align-items: center;
    gap: 3px;
  }
`;

const LocationInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1px;

  .location-primary {
    font-weight: 500;
    color: #f5f9ff;
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 12px;
  }

  .location-secondary {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
    margin-left: 18px;
  }

  .coordinates {
    font-size: 9px;
    color: rgba(255, 255, 255, 0.5);
    margin-left: 18px;
    font-family: monospace;
  }
`;

const TimeInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0px;

  .time-absolute {
    font-size: 11px;
    color: #f5f9ff;
    font-weight: 500;
  }

  .time-relative {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.6);
  }
`;

const IpContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1px;

  .ip-address {
    font-family: monospace;
    font-weight: 500;
    font-size: 11px;
  }

  .ip-copy {
    font-size: 9px;
    color: #64b5f6;
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
  gap: 8px;
  padding: 16px;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(15, 25, 35, 0.95) 0%, rgba(26, 35, 50, 0.95) 100%);
  border-top: 1px solid rgba(100, 181, 246, 0.2);
  border-radius: 0 0 8px 8px;
`;

const PageButton = styled.button`
  padding: 6px 12px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: ${props => props.active ? 'linear-gradient(90deg, #1565c0, #1a73e8)' : 'rgba(26, 115, 232, 0.1)'};
  color: ${props => props.active ? 'white' : '#8db4d8'};
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 6px;
  font-weight: ${props => props.active ? '600' : '400'};
  font-size: 12px;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(90deg, #0d47a1, #1565c0)' : 'rgba(26, 115, 232, 0.2)'};
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(26, 115, 232, 0.3);
  }

  &:disabled {
    background: rgba(100, 100, 100, 0.2);
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
    box-shadow: none;
  }
`;

const ExportButton = styled.button`
  padding: 6px 16px;
  margin-right: 12px;
  border: 1px solid rgba(46, 125, 50, 0.4);
  background: linear-gradient(135deg, rgba(46, 125, 50, 0.15) 0%, rgba(27, 94, 32, 0.15) 100%);
  color: #66bb6a;
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;

  &:hover {
    background: linear-gradient(135deg, rgba(46, 125, 50, 0.25) 0%, rgba(27, 94, 32, 0.25) 100%);
    border-color: rgba(46, 125, 50, 0.6);
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(46, 125, 50, 0.3);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: rgba(100, 100, 100, 0.2);
    border-color: rgba(100, 100, 100, 0.2);
    color: rgba(255, 255, 255, 0.3);
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
    box-shadow: none;
  }
`;

const StatsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 0 0 35%;

  > * {
    flex: 1;
  }
`;

const ChartSection = styled.div`
  flex: 1;
  display: flex;
`;

const CountryFlag = styled.span`
  display: inline-block;
  margin-right: 3px;
  font-size: 1em;
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

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 25, 35, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  backdrop-filter: blur(2px);
`;

const Spinner = styled.div`
  border: 4px solid rgba(100, 181, 246, 0.1);
  border-radius: 50%;
  border-top: 4px solid #64b5f6;
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
  width: 16px;
  height: 16px;
  accent-color: #1a73e8;
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
  const [sortBy, setSortBy] = useState('country'); // 固定为国家搜索
  const [ipRangeStart, setIpRangeStart] = useState(''); // IP段起始
  const [ipRangeEnd, setIpRangeEnd] = useState(''); // IP段结束
  const [timeRangeStart, setTimeRangeStart] = useState(''); // 时间范围开始
  const [timeRangeEnd, setTimeRangeEnd] = useState(''); // 时间范围结束
  const [isSelectAllActive, setIsSelectAllActive] = useState(false);
  const [isSelectAllLoading, setIsSelectAllLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [networkType, setNetworkType] = useState(propNetworkType || 'utg_q_008');
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

  // 通信记录弹窗相关状态
  const [showCommunicationModal, setShowCommunicationModal] = useState(false);
  const [selectedIp, setSelectedIp] = useState(null);

  // 导出状态
  const [isExporting, setIsExporting] = useState(false);

  // 导出数据库函数
  const handleExportDatabase = async () => {
    if (!networkType) {
      alert('请先选择僵尸网络类型');
      return;
    }

    setIsExporting(true);
    try {
      // 调用后端API导出数据
      const response = await fetch(getApiUrl(`/api/export-database?botnet_type=${networkType}`), {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error('导出失败');
      }

      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${networkType}_database_export.zip`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // 下载文件
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('数据导出成功！');
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败: ' + error.message);
    } finally {
      setIsExporting(false);
    }
  };

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
      console.log(`获取节点数据: networkType=${networkType}, page=${currentPage}, pageSize=${pageSize}, searchTerm=${searchTerm}`);
      
      // 使用防抖延迟搜索请求
      const debounceTimer = setTimeout(() => {
        fetchNodesData();
      }, 500); // 500ms 防抖延迟
      
      return () => clearTimeout(debounceTimer);
    }
  }, [networkType, currentPage, pageSize, searchTerm, ipRangeStart, ipRangeEnd, timeRangeStart, timeRangeEnd]); // 添加 searchTerm 到依赖项

  // 获取完整的图表统计数据
  const fetchChartStats = async () => {
    try {
      const endpoint = getApiUrl(`/api/node-stats/${networkType}`);
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
      
      setChartStats(newChartStats);

    } catch (error) {
      console.error('获取图表统计数据失败:', error);
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

      // 添加搜索关键词（后端会在country/province/city中进行LIKE搜索）
      if (searchTerm && searchTerm.trim()) {
        params.append('keyword', searchTerm.trim());
      }

      // 添加IP段筛选
      if (ipRangeStart) {
        params.append('ip_start', ipRangeStart);
      }
      if (ipRangeEnd) {
        params.append('ip_end', ipRangeEnd);
      }

      // 添加时间范围筛选
      if (timeRangeStart) {
        params.append('time_start', timeRangeStart);
      }
      if (timeRangeEnd) {
        params.append('time_end', timeRangeEnd);
      }

      const endpoint = getApiUrl(`/api/node-details?${params.toString()}`);
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
        const activeTimeRaw = node.active_time;
        
        // 根据status字段设置显示文本
        let statusText;
        if (node.status === 'active') {
          statusText = '在线';
        } else if (node.status === 'cleaned') {
          statusText = '已清除';
        } else {
          statusText = '离线';
        }
        
        return {
          id: node.id,
          ip: node.ip,
          country: node.country || '未知',
          province: node.province || '',
          city: node.city || '',
          status: statusText,
          rawStatus: node.status, // 保存原始状态用于判断
          longitude: node.longitude,
          latitude: node.latitude,
          lastSeen: lastSeenRaw,
          lastSeenFormatted: formatDateTime(lastSeenRaw),
          activeTime: activeTimeRaw,
          activeTimeFormatted: formatDateTime(activeTimeRaw)
        };
      });

      setNodes(formattedNodes);
      setTotalPages(result.data.pagination.total_pages);
      setTotalCount(result.data.pagination.total_count);

      // 更新统计信息
      const statistics = result.data.statistics;
      setNodeStats({
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

  // 后端已处理搜索过滤，直接使用返回的节点数据
  const displayedNodes = useMemo(() => {
    return nodes || [];
  }, [nodes]);

  const searchPlaceholder = '按国家/省份搜索';

  // 处理节点选择
  const handleNodeSelect = (nodeId) => {
    setSelectedNodes(prev => {
      if (prev.includes(nodeId)) {
        return prev.filter(id => id !== nodeId);
      }
      return [...prev, nodeId];
    });
    setIsSelectAllActive(false);
  };

  // 处理全选
  const handleSelectAll = async () => {
    if (isSelectAllActive) {
      setSelectedNodes([]);
      setIsSelectAllActive(false);
      return;
    }

    if (!networkType) return;

    setIsSelectAllLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        botnet_type: networkType,
        ids_only: 'true',
        status: 'active'
      });

      if (searchTerm && !searchTerm.match(/^[0-9.]+$/)) {
        params.append('country', searchTerm);
      }
      if (ipRangeStart) {
        params.append('ip_start', ipRangeStart);
      }
      if (ipRangeEnd) {
        params.append('ip_end', ipRangeEnd);
      }
      if (timeRangeStart) {
        params.append('time_start', timeRangeStart);
      }
      if (timeRangeEnd) {
        params.append('time_end', timeRangeEnd);
      }

      const endpoint = getApiUrl(`/api/node-details?${params.toString()}`);
      const response = await fetch(endpoint);

      if (!response.ok) {
        throw new Error(`批量选择失败: ${response.statusText}`);
      }

      const result = await response.json();
      const ids = result.data?.node_ids || [];
      setSelectedNodes(ids);
      setIsSelectAllActive(true);
      setNodeStats(prev => ({
        ...prev,
        selectedCount: ids.length
      }));
    } catch (err) {
      console.error('批量勾选失败:', err);
      setError(err.message || '批量勾选失败，请稍后重试');
    } finally {
      setIsSelectAllLoading(false);
    }
  };

  // 准备图表数据 - 使用 useMemo 缓存，避免不必要的重新渲染
  const getLocationChartOption = useMemo(() => {
    // 使用完整的统计数据，而不是分页数据
    const distribution = chartStats.countryDistribution || {};
    
    const countryData = Object.entries(distribution)
      .map(([name, value]) => ({
        name,
        value,
        label: {
          formatter: '{b}: {c} ({d}%)'
        }
      }))
      .sort((a, b) => b.value - a.value); // 按数量排序

    // 如果没有数据，返回空状态配置
    const buildEmptyState = () => ({
      title: {
        text: '节点地理分布',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16,
          color: '#ffffff'
        }
      },
      legend: {
        show: false
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
    });

    if (countryData.length === 0) {
      return buildEmptyState();
    }

    return {
      title: {
        text: '节点地理分布',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 14,
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
        orient: 'horizontal',
        bottom: 0,
        left: 'center',
        data: countryData.map(item => item.name),
        textStyle: {
          color: '#ffffff',
          fontSize: 12
        },
        itemWidth: 14,
        itemHeight: 14,
        itemGap: 10,
        icon: 'circle'
      },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
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
            fontSize: '16',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: countryData
      }]
    };
  }, [chartStats.countryDistribution]);

  return (
    <Container>
      {/* 左侧面板 - 统计信息和图表 */}
      <LeftPanel>
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

        <ChartCard
          option={getLocationChartOption}
          height="400px"
          accentColor="linear-gradient(90deg, #1a237e, #0d47a1)"
        />
      </LeftPanel>

      {/* 右侧面板 - 搜索和表格 */}
      <RightPanel>
        <TopBar>
          <SearchInput
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </TopBar>
        
        <TopBar>
          <SearchInput
            placeholder="起始IP，例如：192.168.1.1"
            value={ipRangeStart}
            onChange={(e) => setIpRangeStart(e.target.value)}
            style={{ width: '160px' }}
          />
          <span style={{ color: '#7a9cc6' }}>~</span>
          <SearchInput
            placeholder="结束IP，例如：192.168.1.254"
            value={ipRangeEnd}
            onChange={(e) => setIpRangeEnd(e.target.value)}
            style={{ width: '160px' }}
          />
          <SearchInput
            type="date"
            placeholder="开始日期"
            value={timeRangeStart}
            onChange={(e) => setTimeRangeStart(e.target.value)}
            style={{ width: '160px' }}
          />
          <span style={{ color: '#7a9cc6' }}>至</span>
          <SearchInput
            type="date"
            placeholder="结束日期"
            value={timeRangeEnd}
            onChange={(e) => setTimeRangeEnd(e.target.value)}
            style={{ width: '160px' }}
          />
          <Button
            onClick={() => {
              setSearchTerm('');
              setIpRangeStart('');
              setIpRangeEnd('');
              setTimeRangeStart('');
              setTimeRangeEnd('');
              setCurrentPage(1);
            }}
            style={{ background: 'linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)' }}
          >
            清除筛选
          </Button>
        </TopBar>

        <TableContainer>
          <Table>
            <TableHeader>
              <div>IP地址</div>
              <div>地理位置</div>
              <div>最初记录时间</div>
              <div>最近活跃时间</div>
            </TableHeader>
            {displayedNodes.map(node => (
              <TableRow 
                key={node.id} 
                disabled={node.status === '离线' || node.status === '已清除'}
                onClick={(e) => {
                  // 避免点击复选框时触发
                  if (!e.target.closest('input[type="checkbox"]') && !e.target.closest('.ip-copy')) {
                    setSelectedIp(node.ip);
                    setShowCommunicationModal(true);
                  }
                }}
              >
                <div>
                  <IpContainer>
                    <span className="ip-address">{node.ip}</span>
                    <span
                      className="ip-copy"
                      onClick={(e) => {
                        e.stopPropagation();
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
                      {node.activeTimeFormatted}
                    </div>
                    <div className="time-relative">
                      {getRelativeTime(new Date(node.activeTime))}
                    </div>
                  </TimeInfo>
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
              <div style={{ fontWeight: 500, color: '#64b5f6' }}>正在处理...</div>
            </LoadingOverlay>
          )}
        </TableContainer>

        <Pagination>
          <ExportButton onClick={handleExportDatabase} disabled={isExporting || !networkType}>
            <span style={{ fontSize: '14px' }}>📥</span>
            {isExporting ? '导出中...' : '导出数据库'}
          </ExportButton>
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
          <span style={{ marginLeft: '10px', color: '#7a9cc6', fontSize: '12px' }}>
            共 {totalCount} 条记录，{totalPages} 页，当前页最多显示 {pageSize} 条
          </span>
        </Pagination>
      </RightPanel>

      {error && (
        <div style={{
          position: 'absolute',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          color: '#f44336',
          textAlign: 'center',
          padding: '12px 24px',
          backgroundColor: 'rgba(244, 67, 54, 0.1)',
          borderRadius: '8px',
          border: '1px solid rgba(244, 67, 54, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          zIndex: 100
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          {error}
        </div>
      )}

      {/* 通信记录弹窗 */}
      {showCommunicationModal && selectedIp && (
        <CommunicationModal
          ip={selectedIp}
          botnetType={networkType}
          onClose={() => {
            setShowCommunicationModal(false);
            setSelectedIp(null);
          }}
        />
      )}
    </Container>
  );
};

export default NodeManagement;

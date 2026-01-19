import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const Container = styled.div`
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(135deg, #0f1923 0%, #1a2838 100%);
`;

const TabsContainer = styled.div`
  display: flex;
  background: rgba(26, 35, 50, 0.8);
  border-radius: 8px 8px 0 0;
  border-bottom: 2px solid rgba(30, 70, 120, 0.4);
  overflow-x: auto;
  margin-bottom: 20px;
`;

const Tab = styled.button`
  padding: 15px 25px;
  cursor: pointer;
  border: none;
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent'};
  font-size: 15px;
  font-weight: 600;
  color: ${props => props.active ? '#fff' : '#7a9cc6'};
  transition: all 0.3s;
  white-space: nowrap;
  border-radius: 8px 8px 0 0;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(102, 126, 234, 0.1)'};
    color: ${props => props.active ? '#fff' : '#5a8fc4'};
  }
`;

const Section = styled.div`
  background: rgba(15, 48, 87, 0.3);
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 10px;
  border-left: 4px solid #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
`;

const SectionTitle = styled.h3`
  color: #9fd3ff;
  margin-bottom: 15px;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
`;

// 2个输入框的表单组 (等宽)
const FormGroup2 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
  width: 100%;
  overflow: visible;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

// 3个输入框的表单组 (等宽，一行显示)
const FormGroup3 = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 15px;
  width: 100%;
  overflow: visible;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
`;

// 5个输入框的表单组 (两行布局: 第一行3个，第二行2个)
const FormGroup5 = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 15px;
  width: 100%;
  overflow: visible;

  & > *:nth-child(4),
  & > *:nth-child(5) {
    grid-column: span 1;
  }

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
`;

const Input = styled.input`
  width: 100%;
  min-width: 150px;
  padding: 12px 15px;
  border: 2px solid rgba(100, 181, 246, 0.3);
  border-radius: 8px;
  font-size: 14px;
  background: rgba(26, 115, 232, 0.1);
  color: #fff;
  transition: all 0.3s;
  box-sizing: border-box;

  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  &:focus {
    outline: none;
    border-color: #667eea;
    background: rgba(26, 115, 232, 0.2);
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
  }
`;

const Button = styled.button`
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 10px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const PrimaryButton = styled(Button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
`;

const SuccessButton = styled(Button)`
  background: #28a745;
  color: white;

  &:hover {
    background: #218838;
  }
`;

const DangerButton = styled(Button)`
  background: #dc3545;
  color: white;

  &:hover {
    background: #c82333;
  }
`;

const InfoButton = styled(Button)`
  background: #17a2b8;
  color: white;

  &:hover {
    background: #138496;
  }
`;

const WarningButton = styled(Button)`
  background: #ffc107;
  color: #333;

  &:hover {
    background: #e0a800;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  background: rgba(26, 35, 50, 0.6);
  border-radius: 8px;
  overflow: hidden;
`;

const Th = styled.th`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px;
  text-align: left;
  font-weight: 600;
`;

const Td = styled.td`
  padding: 12px;
  border-bottom: 1px solid rgba(30, 70, 120, 0.3);
  color: #b8d4f1;
`;

const Tr = styled.tr`
  transition: background 0.2s;

  &:hover {
    background: rgba(102, 126, 234, 0.1);
  }
`;

const Badge = styled.span`
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background: ${props => {
    switch (props.type) {
      case 'success': return 'rgba(40, 167, 69, 0.3)';
      case 'danger': return 'rgba(220, 53, 69, 0.3)';
      case 'warning': return 'rgba(255, 193, 7, 0.3)';
      case 'info': return 'rgba(23, 162, 184, 0.3)';
      default: return 'rgba(108, 117, 125, 0.3)';
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'success': return '#4caf50';
      case 'danger': return '#f44336';
      case 'warning': return '#ff9800';
      case 'info': return '#2196f3';
      default: return '#9e9e9e';
    }
  }};
  border: 1px solid ${props => {
    switch (props.type) {
      case 'success': return 'rgba(76, 175, 80, 0.5)';
      case 'danger': return 'rgba(244, 67, 54, 0.5)';
      case 'warning': return 'rgba(255, 152, 0, 0.5)';
      case 'info': return 'rgba(33, 150, 243, 0.5)';
      default: return 'rgba(158, 158, 158, 0.5)';
    }
  }};
`;

const SliderContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
`;

const Slider = styled.input`
  flex: 1;
  height: 6px;
  border-radius: 5px;
  background: rgba(102, 126, 234, 0.2);
  outline: none;
  
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
  }
  
  &::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
  }
`;

const SliderValue = styled.span`
  font-weight: bold;
  min-width: 60px;
  color: #667eea;
  font-size: 16px;
`;

const LogContainer = styled.div`
  background: rgba(45, 45, 45, 0.8);
  color: #f0f0f0;
  padding: 15px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  max-height: 400px;
  overflow-y: auto;
  margin-top: 15px;
  border: 1px solid rgba(30, 70, 120, 0.3);
`;

const LogEntry = styled.div`
  margin-bottom: 5px;
  padding: 5px;
  border-left: 3px solid ${props => {
    switch (props.level) {
      case 'INFO': return '#17a2b8';
      case 'WARNING': return '#ffc107';
      case 'ERROR': return '#dc3545';
      default: return 'transparent';
    }
  }};
  background: ${props => {
    switch (props.level) {
      case 'WARNING': return 'rgba(255, 193, 7, 0.1)';
      case 'ERROR': return 'rgba(220, 53, 69, 0.1)';
      default: return 'transparent';
    }
  }};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #7a9cc6;
  font-size: 16px;
`;

const AutoRefreshIndicator = styled.span`
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #28a745;
  margin-left: 10px;
  animation: pulse 2s infinite;

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
`;

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 15px 0;
`;

const PageButton = styled.button`
  padding: 8px 12px;
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(102, 126, 234, 0.2)'};
  color: ${props => props.active ? '#fff' : '#7a9cc6'};
  border: 1px solid ${props => props.active ? '#667eea' : 'rgba(102, 126, 234, 0.3)'};
  border-radius: 5px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.5 : 1};
  transition: all 0.3s;
  font-weight: 500;
  min-width: 40px;

  &:hover:not(:disabled) {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(102, 126, 234, 0.4)'};
    transform: translateY(-2px);
  }
`;

const PageInfo = styled.span`
  color: #7a9cc6;
  font-size: 14px;
  margin: 0 10px;
`;

const API_URL = 'http://localhost:8000';

const SuppressionStrategy = () => {
  const [activeTab, setActiveTab] = useState('port-consume');
  const [tasks, setTasks] = useState([]);
  const [ipBlacklist, setIpBlacklist] = useState([]);
  const [domainBlacklist, setDomainBlacklist] = useState([]);
  const [packetLossPolicies, setPacketLossPolicies] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [portForm, setPortForm] = useState({ ip: '', port: '', threads: '' });
  const [synForm, setSynForm] = useState({ ip: '', port: '', threads: '', duration: '', rate: '' });
  const [ipForm, setIpForm] = useState({ ip: '', description: '' });
  const [domainForm, setDomainForm] = useState({ domain: '', description: '' });
  const [packetLossForm, setPacketLossForm] = useState({ ip: '', description: '', lossRate: 0 });
  
  // 分页状态
  const [portTaskPage, setPortTaskPage] = useState(1);
  const [synTaskPage, setSynTaskPage] = useState(1);
  const tasksPerPage = 6;
  
  // 黑名单和策略的分页状态
  const [ipBlacklistPage, setIpBlacklistPage] = useState(1);
  const [domainBlacklistPage, setDomainBlacklistPage] = useState(1);
  const [packetLossPolicyPage, setPacketLossPolicyPage] = useState(1);
  const itemsPerPage = 5;

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadData = async () => {
    try {
      if (activeTab === 'port-consume' || activeTab === 'syn-flood') {
        await Promise.all([loadTasks(), loadLogs()]);
      } else if (activeTab === 'ip-blacklist') {
        await loadIPBlacklist();
      } else if (activeTab === 'domain-blacklist') {
        await loadDomainBlacklist();
      } else if (activeTab === 'packet-loss') {
        await loadPacketLossPolicies();
      }
    } catch (error) {
      console.error('加载数据失败:', error);
    }
  };

  const loadTasks = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/tasks`);
      if (response.data.status === 'success') {
        setTasks(response.data.data || []);
      }
    } catch (error) {
      console.error('加载任务失败:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/logs?limit=100`);
      if (response.data.status === 'success') {
        setLogs(response.data.data || []);
      }
    } catch (error) {
      console.error('加载日志失败:', error);
    }
  };

  const loadIPBlacklist = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/blacklist/ip`);
      if (response.data.status === 'success') {
        setIpBlacklist(response.data.data || []);
      }
    } catch (error) {
      console.error('加载IP黑名单失败:', error);
    }
  };

  const loadDomainBlacklist = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/blacklist/domain`);
      if (response.data.status === 'success') {
        setDomainBlacklist(response.data.data || []);
      }
    } catch (error) {
      console.error('加载域名黑名单失败:', error);
    }
  };

  const loadPacketLossPolicies = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/packet-loss`);
      if (response.data.status === 'success') {
        setPacketLossPolicies(response.data.data || []);
      }
    } catch (error) {
      console.error('加载丢包策略失败:', error);
    }
  };

  const startPortConsume = async () => {
    if (!portForm.ip || !portForm.port) {
      alert('请填写目标IP和端口');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/port-consume/start`, portForm);
      if (response.data.status === 'success') {
        alert('端口资源消耗任务启动成功');
        setPortForm({ ip: '', port: '', threads: '' });
        await loadTasks();
      } else {
        alert(response.data.message || '启动失败');
      }
    } catch (error) {
      // 处理验证错误（422状态码）
      if (error.response && error.response.status === 422) {
        const errors = error.response.data.detail;
        if (Array.isArray(errors) && errors.length > 0) {
          // 提取所有错误信息，只显示错误消息本身，去除 "Value error, " 前缀
          const errorMessages = errors.map(err => {
            let msg = err.msg;
            // 去除 Pydantic 自动添加的 "Value error, " 前缀
            if (msg.startsWith('Value error, ')) {
              msg = msg.substring(13);
            }
            return msg;
          }).join('\n');
          alert(errorMessages);
        } else {
          alert('输入验证失败，请检查输入格式');
        }
      } else {
        alert('启动失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const startSynFlood = async () => {
    if (!synForm.ip || !synForm.port) {
      alert('请填写目标IP和端口');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/syn-flood/start`, synForm);
      if (response.data.status === 'success') {
        alert('SYN洪水攻击任务启动成功');
        setSynForm({ ip: '', port: '', threads: '', duration: '', rate: '' });
        await loadTasks();
      } else {
        alert(response.data.message || '启动失败');
      }
    } catch (error) {
      // 处理验证错误（422状态码）
      if (error.response && error.response.status === 422) {
        const errors = error.response.data.detail;
        if (Array.isArray(errors) && errors.length > 0) {
          // 提取所有错误信息，只显示错误消息本身，去除 "Value error, " 前缀
          const errorMessages = errors.map(err => {
            let msg = err.msg;
            if (msg.startsWith('Value error, ')) {
              msg = msg.substring(13);
            }
            return msg;
          }).join('\n');
          alert(errorMessages);
        } else {
          alert('输入验证失败，请检查输入格式');
        }
      } else {
        alert('启动失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const stopTask = async (taskId) => {
    if (!window.confirm('确定要停止这个任务吗？')) return;
    try {
      const response = await axios.post(`${API_URL}/api/suppression/task/${taskId}/stop`);
      if (response.data.status === 'success') {
        alert('任务已停止');
        await loadTasks();
      } else {
        alert(response.data.message || '停止失败');
      }
    } catch (error) {
      alert('停止失败: ' + error.message);
    }
  };

  const addIPBlacklist = async () => {
    if (!ipForm.ip) {
      alert('请填写IP地址');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/blacklist/ip`, ipForm);
      if (response.data.status === 'success') {
        alert('IP已添加到黑名单');
        setIpForm({ ip: '', description: '' });
        await loadIPBlacklist();
      } else {
        alert(response.data.message || '添加失败');
      }
    } catch (error) {
      // 处理验证错误（422状态码）
      if (error.response && error.response.status === 422) {
        const errors = error.response.data.detail;
        if (Array.isArray(errors) && errors.length > 0) {
          // 提取所有错误信息，只显示错误消息本身，去除 "Value error, " 前缀
          const errorMessages = errors.map(err => {
            let msg = err.msg;
            if (msg.startsWith('Value error, ')) {
              msg = msg.substring(13);
            }
            return msg;
          }).join('\n');
          alert(errorMessages);
        } else {
          alert('输入验证失败，请检查输入格式');
        }
      } else {
        alert('添加失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteIPBlacklist = async (id) => {
    if (!window.confirm('确定要删除这个IP吗？')) return;
    try {
      const response = await axios.delete(`${API_URL}/api/suppression/blacklist/ip/${id}`);
      if (response.data.status === 'success') {
        alert('IP已删除');
        await loadIPBlacklist();
      } else {
        alert(response.data.message || '删除失败');
      }
    } catch (error) {
      alert('删除失败: ' + error.message);
    }
  };

  const addDomainBlacklist = async () => {
    if (!domainForm.domain) {
      alert('请填写域名');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/blacklist/domain`, domainForm);
      if (response.data.status === 'success') {
        alert('域名已添加到黑名单');
        setDomainForm({ domain: '', description: '' });
        await loadDomainBlacklist();
      } else {
        alert(response.data.message || '添加失败');
      }
    } catch (error) {
      // 处理验证错误（422状态码）
      if (error.response && error.response.status === 422) {
        const errors = error.response.data.detail;
        if (Array.isArray(errors) && errors.length > 0) {
          // 提取所有错误信息，只显示错误消息本身，去除 "Value error, " 前缀
          const errorMessages = errors.map(err => {
            let msg = err.msg;
            if (msg.startsWith('Value error, ')) {
              msg = msg.substring(13);
            }
            return msg;
          }).join('\n');
          alert(errorMessages);
        } else {
          alert('输入验证失败，请检查输入格式');
        }
      } else {
        alert('添加失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteDomainBlacklist = async (id) => {
    if (!window.confirm('确定要删除这个域名吗？')) return;
    try {
      const response = await axios.delete(`${API_URL}/api/suppression/blacklist/domain/${id}`);
      if (response.data.status === 'success') {
        alert('域名已删除');
        await loadDomainBlacklist();
      } else {
        alert(response.data.message || '删除失败');
      }
    } catch (error) {
      alert('删除失败: ' + error.message);
    }
  };

  const addPacketLossPolicy = async () => {
    if (!packetLossForm.ip) {
      alert('请填写IP地址');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/packet-loss`, {
        ip: packetLossForm.ip,
        description: packetLossForm.description,
        loss_rate: packetLossForm.lossRate / 100
      });
      if (response.data.status === 'success') {
        alert('丢包策略已添加');
        setPacketLossForm({ ip: '', description: '', lossRate: 0 });
        await loadPacketLossPolicies();
      } else {
        alert(response.data.message || '添加失败');
      }
    } catch (error) {
      // 处理验证错误（422状态码）
      if (error.response && error.response.status === 422) {
        const errors = error.response.data.detail;
        if (Array.isArray(errors) && errors.length > 0) {
          // 提取所有错误信息，只显示错误消息本身，去除 "Value error, " 前缀
          const errorMessages = errors.map(err => {
            let msg = err.msg;
            if (msg.startsWith('Value error, ')) {
              msg = msg.substring(13);
            }
            return msg;
          }).join('\n');
          alert(errorMessages);
        } else {
          alert('输入验证失败，请检查输入格式');
        }
      } else {
        alert('添加失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const deletePacketLossPolicy = async (id) => {
    if (!window.confirm('确定要删除这条丢包策略吗？')) return;
    try {
      const response = await axios.delete(`${API_URL}/api/suppression/packet-loss/${id}`);
      if (response.data.status === 'success') {
        alert('策略已删除');
        await loadPacketLossPolicies();
      } else {
        alert(response.data.message || '删除失败');
      }
    } catch (error) {
      alert('删除失败: ' + error.message);
    }
  };

  const togglePacketLossPolicy = async (id, enabled) => {
    try {
      const response = await axios.put(`${API_URL}/api/suppression/packet-loss/${id}`, { enabled });
      if (response.data.status === 'success') {
        alert(`策略已${enabled ? '启用' : '禁用'}`);
        await loadPacketLossPolicies();
      } else {
        alert(response.data.message || '操作失败');
      }
    } catch (error) {
      alert('操作失败: ' + error.message);
    }
  };

  // 分页辅助函数
  const getPaginatedData = (data, page, perPage) => {
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    return data.slice(startIndex, endIndex);
  };

  const getTotalPages = (dataLength, perPage) => {
    return Math.ceil(dataLength / perPage);
  };

  // 分页组件
  const Pagination = ({ currentPage, totalPages, onPageChange }) => {
    if (totalPages <= 1) return null;

    const pages = [];
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }

    return (
      <PaginationContainer>
        <PageButton 
          onClick={() => onPageChange(currentPage - 1)} 
          disabled={currentPage === 1}
        >
          上一页
        </PageButton>
        
        {pages.map(page => (
          <PageButton
            key={page}
            active={page === currentPage}
            onClick={() => onPageChange(page)}
          >
            {page}
          </PageButton>
        ))}
        
        <PageButton 
          onClick={() => onPageChange(currentPage + 1)} 
          disabled={currentPage === totalPages}
        >
          下一页
        </PageButton>
        
        <PageInfo>
          第 {currentPage} / {totalPages} 页
        </PageInfo>
      </PaginationContainer>
    );
  };

  const renderPortConsumeTab = () => (
    <>
      <Section>
        <SectionTitle>启动端口资源消耗攻击</SectionTitle>
        <FormGroup3>
          <Input
            type="text"
            placeholder="目标IP地址"
            value={portForm.ip}
            onChange={(e) => setPortForm({ ...portForm, ip: e.target.value })}
          />
          <Input
            type="number"
            placeholder="目标端口"
            value={portForm.port}
            onChange={(e) => setPortForm({ ...portForm, port: e.target.value })}
          />
          <Input
            type="number"
            placeholder="线程数"
            value={portForm.threads}
            onChange={(e) => setPortForm({ ...portForm, threads: e.target.value })}
          />
        </FormGroup3>
        <PrimaryButton onClick={startPortConsume} disabled={loading}>
          启动端口资源消耗
        </PrimaryButton>
      </Section>

      <Section>
        <SectionTitle>
          运行中的任务 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadTasks}>刷新任务列表</InfoButton>
        {(() => {
          const portTasks = tasks.filter(t => t.task_type === 'port-consume');
          const totalPages = getTotalPages(portTasks.length, tasksPerPage);
          const paginatedTasks = getPaginatedData(portTasks, portTaskPage, tasksPerPage);
          
          return portTasks.length > 0 ? (
            <>
              <Table>
                <thead>
                  <tr>
                    <Th>目标</Th>
                    <Th>线程数</Th>
                    <Th>状态</Th>
                    <Th>启动时间</Th>
                    <Th>操作</Th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTasks.map(task => (
                    <Tr key={task.task_id}>
                      <Td>{task.ip}:{task.port}</Td>
                      <Td>{task.threads}</Td>
                      <Td>
                        <Badge type={task.status === 'running' ? 'success' : 'danger'}>
                          {task.status === 'running' ? '运行中' : '已停止'}
                        </Badge>
                      </Td>
                      <Td>{task.start_time}</Td>
                      <Td>
                        {task.status === 'running' ? (
                          <DangerButton onClick={() => stopTask(task.task_id)}>停止</DangerButton>
                        ) : (
                          <span style={{ color: '#7a9cc6' }}>已停止</span>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              <Pagination 
                currentPage={portTaskPage}
                totalPages={totalPages}
                onPageChange={setPortTaskPage}
              />
            </>
          ) : (
            <EmptyState>暂无端口资源消耗任务</EmptyState>
          );
        })()}
      </Section>

      <Section>
        <SectionTitle>
          任务执行日志 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadLogs}>刷新日志</InfoButton>
        <LogContainer>
          {logs.filter(log => log.task_id && log.task_id.includes('port-consume')).length > 0 ? (
            logs.filter(log => log.task_id && log.task_id.includes('port-consume')).map((log, idx) => (
              <LogEntry key={idx} level={log.level}>
                <span style={{ color: '#888', marginRight: '10px' }}>[{log.timestamp}]</span>
                <span style={{ fontWeight: 'bold', marginRight: '10px' }}>{log.level}</span>
                <span>{log.message}</span>
              </LogEntry>
            ))
          ) : (
            <div style={{ textAlign: 'center', color: '#888' }}>等待日志...</div>
          )}
        </LogContainer>
      </Section>
    </>
  );

  const renderSynFloodTab = () => (
    <>
      <Section>
        <SectionTitle>启动SYN洪水攻击</SectionTitle>
        <FormGroup5>
          <Input
            type="text"
            placeholder="目标IP地址"
            value={synForm.ip}
            onChange={(e) => setSynForm({ ...synForm, ip: e.target.value })}
          />
          <Input
            type="number"
            placeholder="目标端口"
            value={synForm.port}
            onChange={(e) => setSynForm({ ...synForm, port: e.target.value })}
          />
          <Input
            type="number"
            placeholder="线程数"
            value={synForm.threads}
            onChange={(e) => setSynForm({ ...synForm, threads: e.target.value })}
          />
          <Input
            type="number"
            placeholder="持续时间(秒)"
            value={synForm.duration}
            onChange={(e) => setSynForm({ ...synForm, duration: e.target.value })}
          />
          <Input
            type="number"
            placeholder="速率(包/秒)"
            value={synForm.rate}
            onChange={(e) => setSynForm({ ...synForm, rate: e.target.value })}
          />
        </FormGroup5>
        <PrimaryButton onClick={startSynFlood} disabled={loading}>
          启动SYN洪水攻击
        </PrimaryButton>
      </Section>

      <Section>
        <SectionTitle>
          运行中的任务 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadTasks}>刷新任务列表</InfoButton>
        {(() => {
          const synTasks = tasks.filter(t => t.task_type === 'syn-flood');
          const totalPages = getTotalPages(synTasks.length, tasksPerPage);
          const paginatedTasks = getPaginatedData(synTasks, synTaskPage, tasksPerPage);
          
          return synTasks.length > 0 ? (
            <>
              <Table>
                <thead>
                  <tr>
                    <Th>目标</Th>
                    <Th>线程数</Th>
                    <Th>状态</Th>
                    <Th>启动时间</Th>
                    <Th>操作</Th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTasks.map(task => (
                    <Tr key={task.task_id}>
                      <Td>{task.ip}:{task.port}</Td>
                      <Td>{task.threads}</Td>
                      <Td>
                        <Badge type={task.status === 'running' ? 'success' : 'danger'}>
                          {task.status === 'running' ? '运行中' : '已停止'}
                        </Badge>
                      </Td>
                      <Td>{task.start_time}</Td>
                      <Td>
                        {task.status === 'running' ? (
                          <DangerButton onClick={() => stopTask(task.task_id)}>停止</DangerButton>
                        ) : (
                          <span style={{ color: '#7a9cc6' }}>已停止</span>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              <Pagination 
                currentPage={synTaskPage}
                totalPages={totalPages}
                onPageChange={setSynTaskPage}
              />
            </>
          ) : (
            <EmptyState>暂无SYN洪水攻击任务</EmptyState>
          );
        })()}
      </Section>

      <Section>
        <SectionTitle>
          任务执行日志 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadLogs}>刷新日志</InfoButton>
        <LogContainer>
          {logs.filter(log => log.task_id && log.task_id.includes('syn-flood')).length > 0 ? (
            logs.filter(log => log.task_id && log.task_id.includes('syn-flood')).map((log, idx) => (
              <LogEntry key={idx} level={log.level}>
                <span style={{ color: '#888', marginRight: '10px' }}>[{log.timestamp}]</span>
                <span style={{ fontWeight: 'bold', marginRight: '10px' }}>{log.level}</span>
                <span>{log.message}</span>
              </LogEntry>
            ))
          ) : (
            <div style={{ textAlign: 'center', color: '#888' }}>等待日志...</div>
          )}
        </LogContainer>
      </Section>
    </>
  );

  const renderIPBlacklistTab = () => (
    <>
      <Section>
        <SectionTitle>添加IP到黑名单</SectionTitle>
        <FormGroup2>
          <Input
            type="text"
            placeholder="IP地址"
            value={ipForm.ip}
            onChange={(e) => setIpForm({ ...ipForm, ip: e.target.value })}
          />
          <Input
            type="text"
            placeholder="描述(僵尸网络种类)"
            value={ipForm.description}
            onChange={(e) => setIpForm({ ...ipForm, description: e.target.value })}
          />
        </FormGroup2>
        <SuccessButton onClick={addIPBlacklist} disabled={loading}>添加IP</SuccessButton>
        <InfoButton onClick={loadIPBlacklist}>刷新列表</InfoButton>
      </Section>

      <Section>
        <SectionTitle>IP黑名单列表</SectionTitle>
        {(() => {
          const totalPages = getTotalPages(ipBlacklist.length, itemsPerPage);
          const paginatedItems = getPaginatedData(ipBlacklist, ipBlacklistPage, itemsPerPage);
          
          return ipBlacklist.length > 0 ? (
            <>
              <Table>
                <thead>
                  <tr>
                    <Th>ID</Th>
                    <Th>IP地址</Th>
                    <Th>描述</Th>
                    <Th>添加时间</Th>
                    <Th>操作</Th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.map(item => (
                    <Tr key={item.id}>
                      <Td>{item.id}</Td>
                      <Td>{item.ip_address}</Td>
                      <Td>{item.description || '-'}</Td>
                      <Td>{item.created_at}</Td>
                      <Td>
                        <DangerButton onClick={() => deleteIPBlacklist(item.id)}>删除</DangerButton>
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              <Pagination 
                currentPage={ipBlacklistPage}
                totalPages={totalPages}
                onPageChange={setIpBlacklistPage}
              />
            </>
          ) : (
            <EmptyState>暂无IP黑名单</EmptyState>
          );
        })()}
      </Section>
    </>
  );

  const renderDomainBlacklistTab = () => (
    <>
      <Section>
        <SectionTitle>添加域名到黑名单</SectionTitle>
        <FormGroup2>
          <Input
            type="text"
            placeholder="域名"
            value={domainForm.domain}
            onChange={(e) => setDomainForm({ ...domainForm, domain: e.target.value })}
          />
          <Input
            type="text"
            placeholder="描述(僵尸网络种类)"
            value={domainForm.description}
            onChange={(e) => setDomainForm({ ...domainForm, description: e.target.value })}
          />
        </FormGroup2>
        <SuccessButton onClick={addDomainBlacklist} disabled={loading}>添加域名</SuccessButton>
        <InfoButton onClick={loadDomainBlacklist}>刷新列表</InfoButton>
      </Section>

      <Section>
        <SectionTitle>域名黑名单列表</SectionTitle>
        {(() => {
          const totalPages = getTotalPages(domainBlacklist.length, itemsPerPage);
          const paginatedItems = getPaginatedData(domainBlacklist, domainBlacklistPage, itemsPerPage);
          
          return domainBlacklist.length > 0 ? (
            <>
              <Table>
                <thead>
                  <tr>
                    <Th>ID</Th>
                    <Th>域名</Th>
                    <Th>描述</Th>
                    <Th>添加时间</Th>
                    <Th>操作</Th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.map(item => (
                    <Tr key={item.id}>
                      <Td>{item.id}</Td>
                      <Td>{item.domain}</Td>
                      <Td>{item.description || '-'}</Td>
                      <Td>{item.created_at}</Td>
                      <Td>
                        <DangerButton onClick={() => deleteDomainBlacklist(item.id)}>删除</DangerButton>
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              <Pagination 
                currentPage={domainBlacklistPage}
                totalPages={totalPages}
                onPageChange={setDomainBlacklistPage}
              />
            </>
          ) : (
            <EmptyState>暂无域名黑名单</EmptyState>
          );
        })()}
      </Section>
    </>
  );

  const renderPacketLossTab = () => (
    <>
      <Section>
        <SectionTitle>添加丢包策略</SectionTitle>
        <FormGroup2>
          <Input
            type="text"
            placeholder="目标IP地址"
            value={packetLossForm.ip}
            onChange={(e) => setPacketLossForm({ ...packetLossForm, ip: e.target.value })}
          />
          <Input
            type="text"
            placeholder="描述(僵尸网络种类)"
            value={packetLossForm.description}
            onChange={(e) => setPacketLossForm({ ...packetLossForm, description: e.target.value })}
          />
        </FormGroup2>
        <SliderContainer>
          <label style={{ color: '#9fd3ff', fontWeight: 'bold' }}>丢包率:</label>
          <Slider
            type="range"
            min="0"
            max="100"
            value={packetLossForm.lossRate}
            onChange={(e) => setPacketLossForm({ ...packetLossForm, lossRate: parseInt(e.target.value) })}
          />
          <SliderValue>{packetLossForm.lossRate}%</SliderValue>
        </SliderContainer>
        <SuccessButton onClick={addPacketLossPolicy} disabled={loading}>添加策略</SuccessButton>
        <InfoButton onClick={loadPacketLossPolicies}>刷新列表</InfoButton>
      </Section>

      <Section>
        <SectionTitle>丢包策略列表</SectionTitle>
        {(() => {
          const totalPages = getTotalPages(packetLossPolicies.length, itemsPerPage);
          const paginatedItems = getPaginatedData(packetLossPolicies, packetLossPolicyPage, itemsPerPage);
          
          return packetLossPolicies.length > 0 ? (
            <>
              <Table>
                <thead>
                  <tr>
                    <Th>ID</Th>
                    <Th>IP地址</Th>
                    <Th>丢包率</Th>
                    <Th>描述</Th>
                    <Th>状态</Th>
                    <Th>更新时间</Th>
                    <Th>操作</Th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.map(item => (
                    <Tr key={item.id}>
                      <Td>{item.id}</Td>
                      <Td>{item.ip_address}</Td>
                      <Td>{(item.loss_rate * 100).toFixed(1)}%</Td>
                      <Td>{item.description || '-'}</Td>
                      <Td>
                        <Badge type={item.enabled ? 'success' : 'warning'}>
                          {item.enabled ? '启用' : '禁用'}
                        </Badge>
                      </Td>
                      <Td>{item.updated_at}</Td>
                      <Td>
                        <WarningButton onClick={() => togglePacketLossPolicy(item.id, !item.enabled)}>
                          {item.enabled ? '禁用' : '启用'}
                        </WarningButton>
                        <DangerButton onClick={() => deletePacketLossPolicy(item.id)}>删除</DangerButton>
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              <Pagination 
                currentPage={packetLossPolicyPage}
                totalPages={totalPages}
                onPageChange={setPacketLossPolicyPage}
              />
            </>
          ) : (
            <EmptyState>暂无丢包策略</EmptyState>
          );
        })()}
      </Section>
    </>
  );

  return (
    <Container>
      <TabsContainer>
        <Tab active={activeTab === 'port-consume'} onClick={() => setActiveTab('port-consume')}>
          端口资源消耗
        </Tab>
        <Tab active={activeTab === 'syn-flood'} onClick={() => setActiveTab('syn-flood')}>
          SYN洪水攻击
        </Tab>
        <Tab active={activeTab === 'ip-blacklist'} onClick={() => setActiveTab('ip-blacklist')}>
          IP黑名单
        </Tab>
        <Tab active={activeTab === 'domain-blacklist'} onClick={() => setActiveTab('domain-blacklist')}>
          域名黑名单
        </Tab>
        <Tab active={activeTab === 'packet-loss'} onClick={() => setActiveTab('packet-loss')}>
          丢包策略
        </Tab>
      </TabsContainer>

      {activeTab === 'port-consume' && renderPortConsumeTab()}
      {activeTab === 'syn-flood' && renderSynFloodTab()}
      {activeTab === 'ip-blacklist' && renderIPBlacklistTab()}
      {activeTab === 'domain-blacklist' && renderDomainBlacklistTab()}
      {activeTab === 'packet-loss' && renderPacketLossTab()}
    </Container>
  );
};

export default SuppressionStrategy;
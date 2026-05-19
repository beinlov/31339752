import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import { currentUserHasPermission, isCurrentUserReadOnly, USER_ROLES } from '../utils/permissions';

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

const Select = styled.select`
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
  cursor: pointer;

  option {
    background: #1a2838;
    color: #fff;
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

const FormGroup4 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 15px;
  margin-bottom: 20px;
`;

const FormGroup6 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
`;

const FormGroup7 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
`;

// 模态框样式
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  padding: 20px;
`;

const ModalContent = styled.div`
  background: linear-gradient(135deg, #1a2838 0%, #0f1923 100%);
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(102, 126, 234, 0.3);
`;

const ModalHeader = styled.div`
  padding: 20px 25px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 12px 0 0;
`;

const ModalTitle = styled.h2`
  margin: 0;
  color: #fff;
  font-size: 22px;
  font-weight: 600;
`;

const ModalCloseButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: rotate(90deg);
  }
`;

const ModalBody = styled.div`
  padding: 25px;
  overflow-y: auto;
  flex: 1;
  color: #b8d4f1;
`;

const ResultSection = styled.div`
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(15, 48, 87, 0.3);
  border-radius: 8px;
  border-left: 4px solid ${props => props.success ? '#4caf50' : '#f44336'};
`;

const ResultLabel = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #9fd3ff;
  margin-bottom: 10px;
`;

const ResultValue = styled.div`
  font-size: 18px;
  font-weight: 700;
  color: ${props => props.success ? '#4caf50' : '#f44336'};
  margin-bottom: 15px;
`;

const OutputBox = styled.pre`
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  padding: 15px;
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.5);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(102, 126, 234, 0.7);
  }
`;

const API_URL = API_BASE_URL;

const SuppressionStrategy = () => {
  // 权限控制
  const isReadOnly = isCurrentUserReadOnly();
  const hasAdminPermission = currentUserHasPermission(USER_ROLES.ADMIN);
  
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
  
  // 新增策略的状态变量
  const [computeForm, setComputeForm] = useState({ url: '', rate: '50', concurrency: '100', duration: '60' });
  const [tcpSynForm, setTcpSynForm] = useState({ target: '', port: '', captureInterface: '', injectInterface: '' });
  const [tcpSynConnections, setTcpSynConnections] = useState([]);
  const [currentAttackId, setCurrentAttackId] = useState(null);
  const [attackStatus, setAttackStatus] = useState(null);
  const [witchForm, setWitchForm] = useState({ 
    target_node: 'node-1', 
    attack_nodes_per_bucket: 8, 
    test_type: 'docker',
    description: '' 
  });
  const [sybilTestTasks, setSybilTestTasks] = useState([]);
  const [dockerStatus, setDockerStatus] = useState({ containers: [], running: 0 });
  const [selectedTestTask, setSelectedTestTask] = useState(null);
  
  // 真实网络环境VPS管理状态 - 已删除
  // const [vpsServers, setVpsServers] = useState([]);
  // const [vpsForm, setVpsForm] = useState({...});
  // const [distributedTasks, setDistributedTasks] = useState([]);
  // const [distributedForm, setDistributedForm] = useState({...});
  // const [showVpsForm, setShowVpsForm] = useState(false);
  // const [showDistributedForm, setShowDistributedForm] = useState(false);
  const [showResultModal, setShowResultModal] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [deployLogs, setDeployLogs] = useState([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [relayStatus, setRelayStatus] = useState(null);
  const [ipBlacklistStatus, setIpBlacklistStatus] = useState(null);
  const [domainBlacklistStatus, setDomainBlacklistStatus] = useState(null);
  const [packetLossStatus, setPacketLossStatus] = useState(null);
  const [deployType, setDeployType] = useState('');
  
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
    
    // 轮询中继节点状态（仅当有活动攻击时）
    const statusInterval = setInterval(() => {
      if (currentAttackId) {
        loadAttackStatus(currentAttackId);
      }
    }, 2000); // 每2秒轮询一次
    
    return () => {
      clearInterval(interval);
      clearInterval(statusInterval);
    };
  }, [activeTab, currentAttackId]);

  const loadData = async () => {
    try {
      if (activeTab === 'port-consume' || activeTab === 'syn-flood' || 
          activeTab === 'compute-consume') {
        await Promise.all([loadTasks(), loadLogs()]);
      } else if (activeTab === 'tcp-syn-flood') {
        await Promise.all([loadTasks(), loadLogs(), loadRelayStatus()]);
      } else if (activeTab === 'witch-attack') {
        await Promise.all([loadSybilTestTasks(), loadDockerStatus(), loadLogs()]);
      } else if (activeTab === 'ip-blacklist') {
        await Promise.all([loadIPBlacklist(), loadConfigServiceStatus('ip-blacklist', setIpBlacklistStatus)]);
      } else if (activeTab === 'domain-blacklist') {
        await Promise.all([loadDomainBlacklist(), loadConfigServiceStatus('domain-blacklist', setDomainBlacklistStatus)]);
      } else if (activeTab === 'packet-loss') {
        await Promise.all([loadPacketLossPolicies(), loadConfigServiceStatus('packet-loss', setPacketLossStatus)]);
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

  // 新增策略的启动函数
  const startComputeConsume = async () => {
    if (!computeForm.url) {
      alert('请填写目标URL');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/compute-consume/start`, computeForm);
      if (response.data.status === 'success') {
        alert('计算资源消耗任务启动成功');
        setComputeForm({ url: '', rate: '50', concurrency: '100', duration: '60' });
        await loadTasks();
      } else {
        alert(response.data.message || '启动失败');
      }
    } catch (error) {
      alert('启动失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const startTcpSynFlood = async () => {
    if (!tcpSynForm.target || !tcpSynForm.port) {
      alert('请填写目标地址和端口');
      return;
    }
    setLoading(true);
    try {
      // 调用文件API下发命令
      const response = await axios.post(`${API_URL}/api/suppression/relay-file/attack/start`, {
        target_ip: tcpSynForm.target,
        target_port: parseInt(tcpSynForm.port),
        capture_interface: tcpSynForm.captureInterface || null,
        inject_interface: tcpSynForm.injectInterface || null
      });
      
      if (response.data.status === 'success') {
        const attackId = response.data.attack_id;
        setCurrentAttackId(attackId);
        alert('TCP RST攻击命令已写入中继位置，等待执行...');
        // 立即加载一次状态
        setTimeout(() => loadAttackStatus(attackId), 1000);
      } else {
        alert(response.data.message || '启动失败');
      }
    } catch (error) {
      alert('启动失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };
  
  const loadAttackStatus = async (attackId) => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/relay-file/attack/${attackId}/status`);
      if (response.data.status === 'success') {
        const data = response.data.data;
        if (data.connections) {
          setTcpSynConnections(data.connections.connections || []);
        }
        if (data.attack) {
          setAttackStatus(data.attack);
        }
      }
    } catch (error) {
      console.error('加载攻击状态失败:', error);
    }
  };
  
  const stopTcpSynFlood = async () => {
    if (!currentAttackId) {
      alert('没有正在运行的攻击');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/relay-file/attack/stop?attack_id=${currentAttackId}`);
      if (response.data.status === 'success') {
        alert('停止命令已下发');
        setCurrentAttackId(null);
        setTcpSynConnections([]);
        setAttackStatus(null);
      } else {
        alert(response.data.message || '停止失败');
      }
    } catch (error) {
      alert('停止失败: ' + (error.response?.data?.message || error.message));
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

  // ==================== 女巫攻击测试相关函数 ====================
  const startSybilDockerTest = async () => {
    if (!witchForm.target_node) {
      alert('请选择目标节点');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/sybil-attack/test/docker/start`, witchForm);
      if (response.data.status === 'success') {
        alert(`女巫攻击测试已启动\n任务ID: ${response.data.task_id}\nDocker环境正在构建中，请稍候...`);
        await loadSybilTestTasks();
        await loadDockerStatus();
      }
    } catch (error) {
      alert('启动失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const loadSybilTestTasks = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sybil-attack/test/tasks`);
      if (response.data.status === 'success') {
        setSybilTestTasks(response.data.data);
      }
    } catch (error) {
      console.error('加载女巫攻击测试任务失败:', error);
    }
  };

  const loadDockerStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sybil-attack/test/docker/status`);
      if (response.data.status === 'success') {
        setDockerStatus(response.data);
      }
    } catch (error) {
      console.error('加载Docker状态失败:', error);
    }
  };

  const stopSybilDockerTest = async (taskId) => {
    if (!window.confirm('确定要停止Docker环境吗？这将关闭所有容器')) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/sybil-attack/test/docker/stop/${taskId}`);
      if (response.data.status === 'success') {
        alert('Docker环境已停止');
        await loadSybilTestTasks();
        await loadDockerStatus();
      }
    } catch (error) {
      alert('停止失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const cleanupDockerEnvironment = async () => {
    if (!window.confirm('确定要清理Docker环境吗？\n\n这将执行以下操作：\n✓ 停止并删除所有容器\n✓ 删除Docker网络\n✓ 清理未完成的任务记录')) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/sybil-attack/test/docker/cleanup`);
      if (response.data.status === 'success') {
        const details = response.data.details;
        let message = '✅ 环境清理完成！\n\n';
        message += `🗑️ 删除容器: ${details.containers_removed} 个\n`;
        message += `🌐 删除网络: ${details.networks_removed} 个\n`;
        message += `📋 清理任务: ${details.tasks_cleaned} 个\n`;
        
        if (details.errors && details.errors.length > 0) {
          message += `\n⚠️ 警告:\n${details.errors.join('\n')}`;
        }
        
        alert(message);
        await loadSybilTestTasks();
        await loadDockerStatus();
      }
    } catch (error) {
      alert('清理失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const deleteSybilTestTask = async (taskId) => {
    if (!window.confirm('确定要删除这个测试任务吗？\n\n如果任务正在运行，Docker环境也会被停止。')) return;
    
    setLoading(true);
    try {
      const response = await axios.delete(`${API_URL}/api/sybil-attack/test/tasks/${taskId}`);
      if (response.data.status === 'success') {
        alert('✅ 任务已删除');
        await loadSybilTestTasks();
        await loadDockerStatus();
      }
    } catch (error) {
      alert('删除失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const viewTestAnalysis = async (taskId) => {
    try {
      const response = await axios.get(`${API_URL}/api/sybil-attack/test/analysis/${taskId}`);
      if (response.data.status === 'success') {
        const data = response.data.data;
        const result = data.attack_result;
        if (result) {
          setTestResult(result);
          setShowResultModal(true);
        } else {
          alert('测试还在进行中，请稍后查看');
        }
      }
    } catch (error) {
      alert('获取分析结果失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getDockerLogs = async (container) => {
    try {
      const response = await axios.get(`${API_URL}/api/sybil-attack/test/docker/logs/${container}?tail=100`);
      if (response.data.status === 'success') {
        const logs = response.data.logs.substring(0, 2000);
        alert(`容器日志: ${container}\n\n${logs}`);
      }
    } catch (error) {
      alert('获取日志失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 一键部署中继节点
  const deployRelayNode = async () => {
    if (!window.confirm('⚠️ 确定要部署中继节点吗？\n\n这将在远程服务器上执行以下操作：\n1. 创建目录结构\n2. 上传攻击脚本\n3. 安装依赖包\n4. 设置网络权限\n5. 启动服务\n\n请确保config.py中的SSH配置正确！')) return;
    
    setIsDeploying(true);
    setDeployLogs([]);
    setDeployType('TCP RST中继节点');
    setShowDeployModal(true);
    
    try {
      const response = await axios.post(`${API_URL}/api/suppression/relay-file/deploy`);
      
      if (response.data.status === 'success') {
        setDeployLogs(response.data.logs || []);
        setTimeout(() => {
          loadRelayStatus();
        }, 1000);
      } else {
        setDeployLogs(response.data.logs || [{ 
          step: '部署失败', 
          status: 'error', 
          message: response.data.message,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      setDeployLogs([{ 
        step: '请求失败', 
        status: 'error', 
        message: error.response?.data?.detail || error.message,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsDeploying(false);
    }
  };

  // 加载中继节点状态
  const loadRelayStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/relay-file/status`);
      if (response.data.status === 'success') {
        setRelayStatus(response.data.data);
      }
    } catch (error) {
      console.error('获取中继节点状态失败:', error);
    }
  };

  // 加载配置服务状态
  const loadConfigServiceStatus = async (serviceType, setStatusFunc) => {
    try {
      const response = await axios.get(`${API_URL}/api/suppression/config-push/status/${serviceType}`);
      if (response.data.status === 'success') {
        setStatusFunc(response.data.data);
      }
    } catch (error) {
      console.error(`获取${serviceType}状态失败:`, error);
    }
  };

  // 一键部署配置服务
  const deployConfigService = async (serviceType, serviceName) => {
    if (!window.confirm(`⚠️ 确定要部署${serviceName}吗？\n\n这将在远程服务器上执行以下操作：\n1. 创建配置目录\n2. 设置目录权限\n3. 创建初始配置文件\n4. 验证部署\n\n请确保config.py中的SSH配置正确！`)) return;
    
    setIsDeploying(true);
    setDeployLogs([]);
    setDeployType(serviceName);
    setShowDeployModal(true);
    
    try {
      const response = await axios.post(`${API_URL}/api/suppression/config-push/deploy/${serviceType}`);
      
      if (response.data.status === 'success') {
        setDeployLogs(response.data.logs || []);
        setTimeout(() => {
          if (serviceType === 'ip-blacklist') loadConfigServiceStatus('ip-blacklist', setIpBlacklistStatus);
          else if (serviceType === 'domain-blacklist') loadConfigServiceStatus('domain-blacklist', setDomainBlacklistStatus);
          else if (serviceType === 'packet-loss') loadConfigServiceStatus('packet-loss', setPacketLossStatus);
        }, 1000);
      } else {
        setDeployLogs(response.data.logs || [{ 
          step: '部署失败', 
          status: 'error', 
          message: response.data.message,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      setDeployLogs([{ 
        step: '请求失败', 
        status: 'error', 
        message: error.response?.data?.detail || error.message,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsDeploying(false);
    }
  };

  // ==================== 真实网络环境VPS管理函数 - 已删除 ====================
  // const loadVpsServers = async () => {...};
  // const addVpsServer = async () => {...};
  // const testVpsConnection = async (vpsId) => {...};
  // const deleteVpsServer = async (vpsId) => {...};
  // const loadDistributedTasks = async () => {...};
  // const deployDistributedAttack = async () => {...};
  // const stopDistributedAttack = async (taskId) => {...};

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

  // 配置推送相关函数
  const pushIPBlacklist = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/config-push/ip-blacklist`);
      if (response.data.status === 'success') {
        alert(`IP黑名单已推送到网关设备，共${response.data.count}条`);
      } else {
        alert(response.data.message || '推送失败');
      }
    } catch (error) {
      alert('推送失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const pushDomainBlacklist = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/config-push/domain-blacklist`);
      if (response.data.status === 'success') {
        alert(`域名黑名单已推送到DNS服务器，共${response.data.count}条`);
      } else {
        alert(response.data.message || '推送失败');
      }
    } catch (error) {
      alert('推送失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const pushPacketLossPolicy = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/config-push/packet-loss`);
      if (response.data.status === 'success') {
        alert(`丢包策略已推送到网关设备，共${response.data.count}条`);
      } else {
        alert(response.data.message || '推送失败');
      }
    } catch (error) {
      alert('推送失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const pushAllConfig = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/suppression/config-push/all`);
      if (response.data.status === 'success' || response.data.status === 'partial') {
        const details = response.data.details;
        const msg = `配置推送完成:\n` +
          `- IP黑名单: ${details.ip_blacklist.count}条 ${details.ip_blacklist.success ? '✓' : '✗'}\n` +
          `- 域名黑名单: ${details.domain_blacklist.count}条 ${details.domain_blacklist.success ? '✓' : '✗'}\n` +
          `- 丢包策略: ${details.packet_loss.count}条 ${details.packet_loss.success ? '✓' : '✗'}`;
        alert(msg);
      } else {
        alert(response.data.message || '推送失败');
      }
    } catch (error) {
      alert('推送失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
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
        <PrimaryButton 
          onClick={startPortConsume} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
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
        <PrimaryButton 
          onClick={startSynFlood} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
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

  // 新增策略的渲染函数
  const renderComputeConsumeTab = () => (
    <>
      <Section>
        <SectionTitle>启动计算资源消耗攻击</SectionTitle>
        <FormGroup4>
          <Input
            type="text"
            placeholder="目标URL (如: http://192.168.1.1:80/content/faq.php)"
            value={computeForm.url}
            onChange={(e) => setComputeForm({ ...computeForm, url: e.target.value })}
          />
          <Input
            type="number"
            placeholder="每秒序列数 (rate)"
            value={computeForm.rate}
            onChange={(e) => setComputeForm({ ...computeForm, rate: e.target.value })}
          />
          <Input
            type="number"
            placeholder="并发数 (concurrency)"
            value={computeForm.concurrency}
            onChange={(e) => setComputeForm({ ...computeForm, concurrency: e.target.value })}
          />
          <Input
            type="number"
            placeholder="持续时间(秒)"
            value={computeForm.duration}
            onChange={(e) => setComputeForm({ ...computeForm, duration: e.target.value })}
          />
        </FormGroup4>
        <PrimaryButton 
          onClick={startComputeConsume} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
          启动计算资源消耗
        </PrimaryButton>
      </Section>

      <Section>
        <SectionTitle>
          运行中的任务 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadTasks}>刷新任务列表</InfoButton>
        {(() => {
          const computeTasks = tasks.filter(task => task.task_id && task.task_id.includes('compute-consume'));
          const totalPages = getTotalPages(computeTasks.length, tasksPerPage);
          const paginatedTasks = getPaginatedData(computeTasks, 1, tasksPerPage);
          
          return computeTasks.length > 0 ? (
            <Table>
              <thead>
                <tr>
                  <Th>目标</Th>
                  <Th>核心数</Th>
                  <Th>强度</Th>
                  <Th>状态</Th>
                  <Th>启动时间</Th>
                  <Th>操作</Th>
                </tr>
              </thead>
              <tbody>
                {paginatedTasks.map(task => (
                  <Tr key={task.task_id}>
                    <Td>{task.target}</Td>
                    <Td>{task.cores}</Td>
                    <Td>{task.intensity}</Td>
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
          ) : (
            <EmptyState>暂无计算资源消耗任务</EmptyState>
          );
        })()}
      </Section>
    </>
  );

  const renderTcpSynFloodTab = () => (
    <>
      {/* 中继节点部署状态 */}
      <Section>
        <SectionTitle>🛰️ 中继节点状态</SectionTitle>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '15px',
          marginBottom: '15px'
        }}>
          <div style={{ 
            padding: '15px', 
            background: relayStatus?.is_deployed ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${relayStatus?.is_deployed ? '#4caf50' : '#f44336'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>部署状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: relayStatus?.is_deployed ? '#4caf50' : '#f44336' }}>
              {relayStatus?.is_deployed ? '✅ 已部署' : '❌ 未部署'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: relayStatus?.is_running ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 152, 0, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${relayStatus?.is_running ? '#4caf50' : '#ff9800'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>服务状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: relayStatus?.is_running ? '#4caf50' : '#ff9800' }}>
              {relayStatus?.is_running ? '🟢 运行中' : '⚪ 未运行'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '8px',
            borderLeft: '4px solid #667eea'
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>服务器地址</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#b8d4f1' }}>
              {relayStatus?.host || '未配置'}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <PrimaryButton 
            onClick={deployRelayNode} 
            disabled={isDeploying || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : ''}
          >
            {isDeploying ? '⏳ 部署中...' : '🚀 一键部署中继节点'}
          </PrimaryButton>
          
          <InfoButton onClick={loadRelayStatus} disabled={loading}>
            🔄 刷新状态
          </InfoButton>
          
          {relayStatus?.available_interfaces && relayStatus.available_interfaces.length > 0 && (
            <div style={{ 
              marginLeft: '15px',
              padding: '8px 12px',
              background: 'rgba(102, 126, 234, 0.1)',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#9fd3ff'
            }}>
              可用接口: {relayStatus.available_interfaces.join(', ')}
            </div>
          )}
        </div>
        
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderLeft: '3px solid #2196f3',
          color: '#9fd3ff',
          fontSize: '13px'
        }}>
          <strong>💡 提示：</strong>
          <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '0' }}>
            <li>首次使用请点击"一键部署中继节点"自动完成所有配置</li>
            <li>部署将读取 config.py 中的 RELAY_CONFIG 配置</li>
            <li>请确保中继服务器SSH连接信息正确且有sudo权限</li>
          </ul>
        </div>
      </Section>

      <Section>
        <SectionTitle>启动TCP RST攻击（通过中继节点）</SectionTitle>
        <FormGroup4>
          <Input
            type="text"
            placeholder="目标IP (如: 192.168.1.10)"
            value={tcpSynForm.target}
            onChange={(e) => setTcpSynForm({ ...tcpSynForm, target: e.target.value })}
          />
          <Input
            type="number"
            placeholder="目标端口 (如: 80)"
            value={tcpSynForm.port}
            onChange={(e) => setTcpSynForm({ ...tcpSynForm, port: e.target.value })}
          />
          <Input
            type="text"
            placeholder="捕获接口 (可选, 如: eth0)"
            value={tcpSynForm.captureInterface}
            onChange={(e) => setTcpSynForm({ ...tcpSynForm, captureInterface: e.target.value })}
          />
          <Input
            type="text"
            placeholder="注入接口 (可选, 如: eth0)"
            value={tcpSynForm.injectInterface}
            onChange={(e) => setTcpSynForm({ ...tcpSynForm, injectInterface: e.target.value })}
          />
        </FormGroup4>
        <div style={{ display: 'flex', gap: '10px' }}>
          <PrimaryButton 
            onClick={startTcpSynFlood} 
            disabled={loading || isReadOnly || currentAttackId}
            title={isReadOnly ? '仅管理员可使用此功能' : currentAttackId ? '已有攻击正在运行' : ''}
          >
            启动TCP RST攻击
          </PrimaryButton>
          {currentAttackId && (
            <DangerButton 
              onClick={stopTcpSynFlood} 
              disabled={loading || isReadOnly}
            >
              停止当前攻击
            </DangerButton>
          )}
        </div>
        {attackStatus && (
          <div style={{ 
            marginTop: '10px', 
            padding: '10px', 
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '5px',
            color: '#9fd3ff',
            fontSize: '13px'
          }}>
            <div>攻击ID: {attackStatus.attack_id}</div>
            <div>状态: <strong>{attackStatus.status === 'running' ? '运行中' : '已停止'}</strong></div>
            {attackStatus.pid && <div>进程ID: {attackStatus.pid}</div>}
            {attackStatus.target_ip && <div>目标: {attackStatus.target_ip}:{attackStatus.target_port}</div>}
          </div>
        )}
      </Section>

      <Section>
        <SectionTitle>
          运行中的任务 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        <InfoButton onClick={loadTasks}>刷新任务列表</InfoButton>
        {(() => {
          const tcpSynTasks = tasks.filter(task => task.task_id && task.task_id.includes('tcp-syn-flood'));
          const totalPages = getTotalPages(tcpSynTasks.length, tasksPerPage);
          const paginatedTasks = getPaginatedData(tcpSynTasks, 1, tasksPerPage);
          
          return tcpSynTasks.length > 0 ? (
            <Table>
              <thead>
                <tr>
                  <Th>目标</Th>
                  <Th>端口</Th>
                  <Th>线程数</Th>
                  <Th>速率</Th>
                  <Th>状态</Th>
                  <Th>启动时间</Th>
                  <Th>操作</Th>
                </tr>
              </thead>
              <tbody>
                {paginatedTasks.map(task => (
                  <Tr key={task.task_id}>
                    <Td>{task.target}:{task.port}</Td>
                    <Td>{task.threads}</Td>
                    <Td>{task.rate}</Td>
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
          ) : (
            <EmptyState>暂无TCP RST攻击任务</EmptyState>
          );
        })()}
      </Section>

      <Section>
        <SectionTitle>
          目标连接状态监控 <AutoRefreshIndicator title="实时更新中" />
        </SectionTitle>
        <div style={{ marginBottom: '15px', color: '#9fd3ff' }}>
          {currentAttackId ? (
            <span>当前监控攻击ID: {currentAttackId}</span>
          ) : (
            <span>暂无活动监控</span>
          )}
        </div>
        {tcpSynConnections.length > 0 ? (
          <Table>
            <thead>
              <tr>
                <Th>源地址</Th>
                <Th>源端口</Th>
                <Th>目标地址</Th>
                <Th>目标端口</Th>
                <Th>连接状态</Th>
                <Th>数据包数量</Th>
                <Th>最后更新</Th>
                <Th>TCP标志</Th>
              </tr>
            </thead>
            <tbody>
              {tcpSynConnections.map((conn, index) => (
                <Tr key={index}>
                  <Td>{conn.src_ip}</Td>
                  <Td>{conn.src_port}</Td>
                  <Td>{conn.dst_ip}</Td>
                  <Td>{conn.dst_port}</Td>
                  <Td>
                    <Badge type={
                      conn.status === 'active' ? 'success' : 
                      conn.status === 'closed' ? 'danger' : 
                      'warning'
                    }>
                      {conn.status === 'active' ? '通信中' : 
                       conn.status === 'closed' ? '已断开' : 
                       '超时'}
                    </Badge>
                  </Td>
                  <Td>{conn.packet_count}</Td>
                  <Td style={{ fontSize: '12px' }}>
                    {new Date(conn.last_seen).toLocaleTimeString()}
                  </Td>
                  <Td>
                    {conn.flags && conn.flags.length > 0 ? (
                      <span style={{ 
                        fontSize: '11px', 
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        padding: '2px 6px',
                        borderRadius: '3px'
                      }}>
                        {conn.flags.join(',')}
                      </span>
                    ) : '-'}
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState>
            {currentAttackId ? 
              '等待连接数据...' : 
              '请先启动TCP RST攻击以监控连接状态'
            }
          </EmptyState>
        )}
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: 'rgba(26, 115, 232, 0.1)',
          borderLeft: '3px solid #667eea',
          color: '#9fd3ff',
          fontSize: '13px'
        }}>
          <strong>说明：</strong>
          <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
            <li>此功能需要中继节点部署在能够监听C2和Bot通信的网络位置</li>
            <li>"通信中"表示中继节点正在监听到双向数据包传输</li>
            <li>"已断开"表示检测到FIN或RST标志，连接已关闭</li>
            <li>"超时"表示超过10秒未收到数据包</li>
            <li>数据每2秒自动更新一次</li>
          </ul>
        </div>
      </Section>
    </>
  );

  const renderWitchAttackTab = () => (
    <>
      <Section>
        <SectionTitle>🐋 Docker女巫攻击测试</SectionTitle>
        <p style={{ color: '#7a9cc6', marginBottom: '15px' }}>
          在本地Docker环境中模拟DHT网络进行女巫攻击测试
        </p>
        
        <FormGroup2>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', color: '#7a9cc6' }}>
              目标节点
            </label>
            <select
              value={witchForm.target_node}
              onChange={(e) => setWitchForm({ ...witchForm, target_node: e.target.value })}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#1e3a5f',
                color: '#fff',
                border: '1px solid #2c5282',
                borderRadius: '4px'
              }}
            >
              <option value="node-1">node-1 (种子节点)</option>
              <option value="node-2">node-2</option>
              <option value="node-3">node-3</option>
              <option value="node-4">node-4</option>
              <option value="node-5">node-5</option>
              <option value="node-6">node-6</option>
              <option value="node-7">node-7</option>
              <option value="node-8">node-8</option>
              <option value="node-9">node-9</option>
              <option value="node-10">node-10</option>
            </select>
          </div>
          
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', color: '#7a9cc6' }}>
              每个Bucket的攻击节点数
            </label>
            <Input
              type="number"
              value={witchForm.attack_nodes_per_bucket}
              onChange={(e) => setWitchForm({ ...witchForm, attack_nodes_per_bucket: parseInt(e.target.value) })}
              min="1"
              max="20"
            />
            <small style={{ color: '#7a9cc6', fontSize: '12px' }}>
              总节点数 = {witchForm.attack_nodes_per_bucket} × 32 = {witchForm.attack_nodes_per_bucket * 32}
            </small>
          </div>
        </FormGroup2>

        <div style={{ marginBottom: '15px' }}>
          <Input
            type="text"
            placeholder="测试描述（可选）"
            value={witchForm.description}
            onChange={(e) => setWitchForm({ ...witchForm, description: e.target.value })}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <PrimaryButton 
            onClick={startSybilDockerTest} 
            disabled={loading || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : ''}
          >
            🚀 启动Docker测试
          </PrimaryButton>
          <InfoButton onClick={() => { loadSybilTestTasks(); loadDockerStatus(); }}>
            🔄 刷新状态
          </InfoButton>
          <WarningButton 
            onClick={cleanupDockerEnvironment}
            disabled={loading || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : '清理所有容器、网络和未完成任务'}
          >
            🧹 清理环境
          </WarningButton>
        </div>
      </Section>

      <Section>
        <SectionTitle>Docker容器状态</SectionTitle>
        {dockerStatus.running > 0 && dockerStatus.containers && dockerStatus.containers.length > 0 ? (
          <div>
            <p style={{ color: '#10b981', marginBottom: '10px' }}>
              ✅ Docker环境运行中 ({dockerStatus.running} 个容器)
            </p>
            <Table>
              <thead>
                <tr>
                  <Th>容器名称</Th>
                  <Th>状态</Th>
                  <Th>操作</Th>
                </tr>
              </thead>
              <tbody>
                {dockerStatus.containers.map((container, idx) => (
                  <Tr key={idx}>
                    <Td>{container.name || 'Unknown'}</Td>
                    <Td>
                      <Badge type={container.status?.includes('Up') ? 'success' : 'danger'}>
                        {container.status || 'Unknown'}
                      </Badge>
                    </Td>
                    <Td>
                      <InfoButton onClick={() => getDockerLogs(container.name)}>
                        查看日志
                      </InfoButton>
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        ) : (
          <EmptyState>Docker环境未运行</EmptyState>
        )}
      </Section>

      <Section>
        <SectionTitle>
          测试任务 <AutoRefreshIndicator title="自动刷新中" />
        </SectionTitle>
        {sybilTestTasks.length > 0 ? (
          <Table>
            <thead>
              <tr>
                <Th>任务ID</Th>
                <Th>目标节点</Th>
                <Th>攻击节点数</Th>
                <Th>状态</Th>
                <Th>启动时间</Th>
                <Th>操作</Th>
              </tr>
            </thead>
            <tbody>
              {sybilTestTasks.map(task => (
                <Tr key={task.task_id}>
                  <Td style={{ fontSize: '12px' }}>{task.task_id.substring(0, 20)}...</Td>
                  <Td>{task.target_node}</Td>
                  <Td>{task.attack_nodes_count}</Td>
                  <Td>
                    <Badge type={
                      task.status === 'completed' ? 'success' :
                      task.status === 'failed' ? 'danger' :
                      task.status === 'running' || task.status === 'attacking' ? 'warning' :
                      'info'
                    }>
                      {task.status === 'preparing' ? '准备中' :
                       task.status === 'starting_docker' ? '启动Docker' :
                       task.status === 'attacking' ? '攻击中' :
                       task.status === 'verifying' ? '验证中' :
                       task.status === 'completed' ? '已完成' :
                       task.status === 'failed' ? '失败' :
                       task.status === 'stopped' ? '已停止' :
                       task.status === 'cleaned' ? '已清理' :
                       task.status}
                    </Badge>
                  </Td>
                  <Td>{task.start_time}</Td>
                  <Td>
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      {task.status === 'completed' ? (
                        <InfoButton onClick={() => viewTestAnalysis(task.task_id)}>
                          查看结果
                        </InfoButton>
                      ) : task.status !== 'stopped' && task.status !== 'failed' && task.status !== 'cleaned' ? (
                        <DangerButton onClick={() => stopSybilDockerTest(task.task_id)}>
                          停止
                        </DangerButton>
                      ) : null}
                      <DangerButton 
                        onClick={() => deleteSybilTestTask(task.task_id)}
                        disabled={loading || isReadOnly}
                        title={isReadOnly ? '仅管理员可使用此功能' : '删除此任务'}
                      >
                        删除
                      </DangerButton>
                    </div>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState>暂无测试任务</EmptyState>
        )}
      </Section>

      {/* VPS服务器管理和分布式女巫攻击部署功能已删除 */}
    </>
  );

  const renderIPBlacklistTab = () => (
    <>
      {/* 配置服务部署状态 */}
      <Section>
        <SectionTitle>🌐 网关设备配置状态</SectionTitle>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '15px',
          marginBottom: '15px'
        }}>
          <div style={{ 
            padding: '15px', 
            background: ipBlacklistStatus?.is_deployed ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${ipBlacklistStatus?.is_deployed ? '#4caf50' : '#f44336'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>部署状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: ipBlacklistStatus?.is_deployed ? '#4caf50' : '#f44336' }}>
              {ipBlacklistStatus?.is_deployed ? '✅ 已部署' : '❌ 未部署'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: ipBlacklistStatus?.is_configured ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 152, 0, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${ipBlacklistStatus?.is_configured ? '#4caf50' : '#ff9800'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>配置状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: ipBlacklistStatus?.is_configured ? '#4caf50' : '#ff9800' }}>
              {ipBlacklistStatus?.is_configured ? '🟢 已配置' : '⚪ 未配置'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '8px',
            borderLeft: '4px solid #667eea'
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>网关设备地址</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#b8d4f1' }}>
              {ipBlacklistStatus?.host || '未配置'}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <PrimaryButton 
            onClick={() => deployConfigService('ip-blacklist', 'IP黑名单服务')} 
            disabled={isDeploying || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : ''}
          >
            {isDeploying ? '⏳ 部署中...' : '🚀 一键部署配置服务'}
          </PrimaryButton>
          
          <InfoButton onClick={() => loadConfigServiceStatus('ip-blacklist', setIpBlacklistStatus)} disabled={loading}>
            🔄 刷新状态
          </InfoButton>
          
          {ipBlacklistStatus?.config_file && (
            <div style={{ 
              marginLeft: '15px',
              padding: '8px 12px',
              background: 'rgba(102, 126, 234, 0.1)',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#9fd3ff'
            }}>
              配置文件: {ipBlacklistStatus.config_file}
            </div>
          )}
        </div>
        
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderLeft: '3px solid #2196f3',
          color: '#9fd3ff',
          fontSize: '13px'
        }}>
          <strong>💡 提示：</strong>
          <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '0' }}>
            <li>首次使用请点击"一键部署配置服务"在网关设备创建配置目录</li>
            <li>部署将读取 config.py 中的 IP_BLACKLIST_CONFIG 配置</li>
            <li>部署完成后可使用"推送到网关设备"功能同步黑名单数据</li>
          </ul>
        </div>
      </Section>

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
        <SuccessButton 
          onClick={addIPBlacklist} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
          添加IP
        </SuccessButton>
        <InfoButton onClick={loadIPBlacklist}>刷新列表</InfoButton>
        <PrimaryButton 
          onClick={pushIPBlacklist} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
          style={{ marginLeft: '10px' }}
        >
          📤 推送到网关设备
        </PrimaryButton>
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
      {/* 配置服务部署状态 */}
      <Section>
        <SectionTitle>🌐 DNS服务器配置状态</SectionTitle>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '15px',
          marginBottom: '15px'
        }}>
          <div style={{ 
            padding: '15px', 
            background: domainBlacklistStatus?.is_deployed ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${domainBlacklistStatus?.is_deployed ? '#4caf50' : '#f44336'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>部署状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: domainBlacklistStatus?.is_deployed ? '#4caf50' : '#f44336' }}>
              {domainBlacklistStatus?.is_deployed ? '✅ 已部署' : '❌ 未部署'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: domainBlacklistStatus?.is_configured ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 152, 0, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${domainBlacklistStatus?.is_configured ? '#4caf50' : '#ff9800'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>配置状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: domainBlacklistStatus?.is_configured ? '#4caf50' : '#ff9800' }}>
              {domainBlacklistStatus?.is_configured ? '🟢 已配置' : '⚪ 未配置'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '8px',
            borderLeft: '4px solid #667eea'
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>DNS服务器地址</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#b8d4f1' }}>
              {domainBlacklistStatus?.host || '未配置'}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <PrimaryButton 
            onClick={() => deployConfigService('domain-blacklist', '域名黑名单服务')} 
            disabled={isDeploying || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : ''}
          >
            {isDeploying ? '⏳ 部署中...' : '🚀 一键部署配置服务'}
          </PrimaryButton>
          
          <InfoButton onClick={() => loadConfigServiceStatus('domain-blacklist', setDomainBlacklistStatus)} disabled={loading}>
            🔄 刷新状态
          </InfoButton>
          
          {domainBlacklistStatus?.config_file && (
            <div style={{ 
              marginLeft: '15px',
              padding: '8px 12px',
              background: 'rgba(102, 126, 234, 0.1)',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#9fd3ff'
            }}>
              配置文件: {domainBlacklistStatus.config_file}
            </div>
          )}
        </div>
        
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderLeft: '3px solid #2196f3',
          color: '#9fd3ff',
          fontSize: '13px'
        }}>
          <strong>💡 提示：</strong>
          <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '0' }}>
            <li>首次使用请点击"一键部署配置服务"在DNS服务器创建配置目录</li>
            <li>部署将读取 config.py 中的 DOMAIN_BLACKLIST_CONFIG 配置</li>
            <li>部署完成后可使用"推送到DNS服务器"功能同步黑名单数据</li>
          </ul>
        </div>
      </Section>

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
        <SuccessButton 
          onClick={addDomainBlacklist} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
          添加域名
        </SuccessButton>
        <InfoButton onClick={loadDomainBlacklist}>刷新列表</InfoButton>
        <PrimaryButton 
          onClick={pushDomainBlacklist} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
          style={{ marginLeft: '10px' }}
        >
          📤 推送到DNS服务器
        </PrimaryButton>
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
      {/* 配置服务部署状态 */}
      <Section>
        <SectionTitle>🌐 网关设备配置状态</SectionTitle>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '15px',
          marginBottom: '15px'
        }}>
          <div style={{ 
            padding: '15px', 
            background: packetLossStatus?.is_deployed ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${packetLossStatus?.is_deployed ? '#4caf50' : '#f44336'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>部署状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: packetLossStatus?.is_deployed ? '#4caf50' : '#f44336' }}>
              {packetLossStatus?.is_deployed ? '✅ 已部署' : '❌ 未部署'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: packetLossStatus?.is_configured ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 152, 0, 0.1)',
            borderRadius: '8px',
            borderLeft: `4px solid ${packetLossStatus?.is_configured ? '#4caf50' : '#ff9800'}`
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>配置状态</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: packetLossStatus?.is_configured ? '#4caf50' : '#ff9800' }}>
              {packetLossStatus?.is_configured ? '🟢 已配置' : '⚪ 未配置'}
            </div>
          </div>
          
          <div style={{ 
            padding: '15px', 
            background: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '8px',
            borderLeft: '4px solid #667eea'
          }}>
            <div style={{ fontSize: '13px', color: '#9fd3ff', marginBottom: '8px' }}>网关设备地址</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#b8d4f1' }}>
              {packetLossStatus?.host || '未配置'}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <PrimaryButton 
            onClick={() => deployConfigService('packet-loss', '丢包策略服务')} 
            disabled={isDeploying || isReadOnly}
            title={isReadOnly ? '仅管理员可使用此功能' : ''}
          >
            {isDeploying ? '⏳ 部署中...' : '🚀 一键部署配置服务'}
          </PrimaryButton>
          
          <InfoButton onClick={() => loadConfigServiceStatus('packet-loss', setPacketLossStatus)} disabled={loading}>
            🔄 刷新状态
          </InfoButton>
          
          {packetLossStatus?.config_file && (
            <div style={{ 
              marginLeft: '15px',
              padding: '8px 12px',
              background: 'rgba(102, 126, 234, 0.1)',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#9fd3ff'
            }}>
              配置文件: {packetLossStatus.config_file}
            </div>
          )}
        </div>
        
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderLeft: '3px solid #2196f3',
          color: '#9fd3ff',
          fontSize: '13px'
        }}>
          <strong>💡 提示：</strong>
          <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '0' }}>
            <li>首次使用请点击"一键部署配置服务"在网关设备创建配置目录</li>
            <li>部署将读取 config.py 中的 PACKET_LOSS_CONFIG 配置</li>
            <li>部署完成后可使用"推送到网关设备"功能同步丢包策略数据</li>
          </ul>
        </div>
      </Section>

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
        <SuccessButton 
          onClick={addPacketLossPolicy} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
        >
          添加策略
        </SuccessButton>
        <InfoButton onClick={loadPacketLossPolicies}>刷新列表</InfoButton>
        <PrimaryButton 
          onClick={pushPacketLossPolicy} 
          disabled={loading || isReadOnly}
          title={isReadOnly ? '仅管理员可使用此功能' : ''}
          style={{ marginLeft: '10px' }}
        >
          📤 推送到网关设备
        </PrimaryButton>
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
        <Tab active={activeTab === 'compute-consume'} onClick={() => setActiveTab('compute-consume')}>
          计算资源消耗
        </Tab>
        <Tab active={activeTab === 'tcp-syn-flood'} onClick={() => setActiveTab('tcp-syn-flood')}>
          TCP RST攻击
        </Tab>
        <Tab active={activeTab === 'witch-attack'} onClick={() => setActiveTab('witch-attack')}>
          女巫攻击
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
      {activeTab === 'compute-consume' && renderComputeConsumeTab()}
      {activeTab === 'tcp-syn-flood' && renderTcpSynFloodTab()}
      {activeTab === 'witch-attack' && renderWitchAttackTab()}
      {activeTab === 'ip-blacklist' && renderIPBlacklistTab()}
      {activeTab === 'domain-blacklist' && renderDomainBlacklistTab()}
      {activeTab === 'packet-loss' && renderPacketLossTab()}

      {/* 部署进度模态框 */}
      {showDeployModal && (
        <ModalOverlay onClick={() => !isDeploying && setShowDeployModal(false)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>🚀 {deployType || '服务'}自动部署</ModalTitle>
              {!isDeploying && (
                <ModalCloseButton onClick={() => setShowDeployModal(false)}>
                  ×
                </ModalCloseButton>
              )}
            </ModalHeader>
            <ModalBody>
              {deployLogs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#9fd3ff' }}>
                  <div style={{ fontSize: '18px', marginBottom: '10px' }}>⏳ 正在准备部署...</div>
                </div>
              ) : (
                <div>
                  {deployLogs.map((log, index) => (
                    <div 
                      key={index} 
                      style={{
                        padding: '12px',
                        marginBottom: '10px',
                        background: log.status === 'error' ? 'rgba(244, 67, 54, 0.1)' : 
                                   log.status === 'success' ? 'rgba(76, 175, 80, 0.1)' :
                                   log.status === 'warning' ? 'rgba(255, 152, 0, 0.1)' :
                                   'rgba(33, 150, 243, 0.1)',
                        borderLeft: `4px solid ${log.status === 'error' ? '#f44336' : 
                                                 log.status === 'success' ? '#4caf50' :
                                                 log.status === 'warning' ? '#ff9800' :
                                                 '#2196f3'}`,
                        borderRadius: '6px'
                      }}
                    >
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '5px'
                      }}>
                        <strong style={{ 
                          color: log.status === 'error' ? '#f44336' : 
                                log.status === 'success' ? '#4caf50' :
                                log.status === 'warning' ? '#ff9800' :
                                '#2196f3'
                        }}>
                          {log.status === 'error' ? '❌' : 
                           log.status === 'success' ? '✅' :
                           log.status === 'warning' ? '⚠️' : '⏳'} {log.step}
                        </strong>
                        <span style={{ fontSize: '11px', color: '#7a9cc6' }}>
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div style={{ fontSize: '13px', color: '#b8d4f1' }}>
                        {log.message}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {!isDeploying && deployLogs.length > 0 && (
                <div style={{ 
                  marginTop: '20px', 
                  textAlign: 'center',
                  paddingTop: '15px',
                  borderTop: '1px solid rgba(102, 126, 234, 0.3)'
                }}>
                  <PrimaryButton onClick={() => setShowDeployModal(false)}>
                    关闭
                  </PrimaryButton>
                </div>
              )}
            </ModalBody>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* 测试结果模态框 */}
      {showResultModal && testResult && (
        <ModalOverlay onClick={() => setShowResultModal(false)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>🔍 女巫攻击测试结果</ModalTitle>
              <ModalCloseButton onClick={() => setShowResultModal(false)}>
                ×
              </ModalCloseButton>
            </ModalHeader>
            <ModalBody>
              <ResultSection success={testResult.attack_success}>
                <ResultLabel>攻击成功</ResultLabel>
                <ResultValue success={testResult.attack_success}>
                  {testResult.attack_success ? '✅ 是' : '❌ 否'}
                </ResultValue>
              </ResultSection>

              <ResultSection success={testResult.attack_success}>
                <ResultLabel>验证输出</ResultLabel>
                <OutputBox>
                  {testResult.verify_output || '无验证输出'}
                </OutputBox>
              </ResultSection>

              {testResult.attack_output && (
                <ResultSection>
                  <ResultLabel>攻击输出（部分）</ResultLabel>
                  <OutputBox>
                    {testResult.attack_output}
                  </OutputBox>
                </ResultSection>
              )}
            </ModalBody>
          </ModalContent>
        </ModalOverlay>
      )}
    </Container>
  );
};

export default SuppressionStrategy;
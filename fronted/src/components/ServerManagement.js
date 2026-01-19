import React, { useState, useEffect, useRef } from 'react';
import { getServers, createServer, updateServer, deleteServer } from '../services';
import styled from 'styled-components';
import { Table, Button, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CodeOutlined, ClearOutlined, ExpandOutlined, CompressOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const Container = styled.div`
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
  
  /* 自定义滚动条 */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(10, 25, 41, 0.5);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(100, 181, 246, 0.3);
    border-radius: 4px;
    
    &:hover {
      background: rgba(100, 181, 246, 0.5);
    }
  }
`;

const ServerSection = styled.div`
  background: linear-gradient(135deg, rgba(10, 25, 41, 0.95) 0%, rgba(13, 31, 45, 0.95) 100%);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(30, 70, 120, 0.3);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  
  /* 装饰性光效 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(100, 181, 246, 0.5), transparent);
  }
  
  /* 表格样式覆盖 */
  .ant-table {
    background: transparent;
  }
  
  .ant-table-thead > tr > th {
    background: rgba(15, 48, 87, 0.6) !important;
    color: #7ec8ff !important;
    border-bottom: 1px solid rgba(30, 70, 120, 0.4) !important;
    font-weight: 600;
    padding: 10px 12px;
    font-size: 13px;
  }
  
  .ant-table-tbody > tr > td {
    border-bottom: 1px solid rgba(30, 70, 120, 0.2) !important;
    color: #d0e7ff;
    padding: 8px 12px;
    transition: all 0.2s ease;
    font-size: 13px;
  }
  
  .ant-table-tbody > tr:hover > td {
    background: rgba(15, 48, 87, 0.4) !important;
  }
  
  .ant-table-tbody > tr {
    background: transparent;
  }
  
  .ant-pagination {
    margin-top: 12px !important;
    margin-bottom: 0 !important;
    
    .ant-pagination-item {
      background: rgba(15, 48, 87, 0.4);
      border-color: rgba(30, 70, 120, 0.4);
      min-width: 28px;
      height: 28px;
      line-height: 26px;
      
      a {
        color: #7ec8ff;
      }
      
      &:hover, &-active {
        background: rgba(0, 120, 215, 0.4);
        border-color: rgba(0, 120, 215, 0.8);
      }
    }
    
    .ant-pagination-prev, .ant-pagination-next {
      min-width: 28px;
      height: 28px;
      line-height: 26px;
      
      .ant-pagination-item-link {
        background: rgba(15, 48, 87, 0.4);
        border-color: rgba(30, 70, 120, 0.4);
        color: #7ec8ff;
      }
    }
    
    .ant-pagination-options {
      display: none;
    }
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(30, 70, 120, 0.3);
`;

const Title = styled.h2`
  margin: 0;
  color: #64b5f6;
  text-shadow: 0 0 10px rgba(100, 181, 246, 0.3);
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  
  .anticon {
    font-size: 18px;
    color: #0078d4;
  }
`;

// PowerShell 终端样式
const TerminalSection = styled.div`
  background: linear-gradient(135deg, rgba(1, 36, 86, 0.98) 0%, rgba(0, 30, 60, 0.98) 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 120, 215, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: ${props => props.expanded ? '500px' : '280px'};
  transition: all 0.3s ease;
  position: relative;
  
  /* 左侧装饰条 */
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #0078d4, #106ebe, #0078d4);
  }
`;

const TerminalHeader = styled.div`
  background: linear-gradient(90deg, #012456 0%, #001e3c 100%);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 120, 215, 0.3);
  margin-left: 4px;
  flex-shrink: 0;
`;

const TerminalTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 14px;
  color: #ffffff;
  font-weight: 600;
  font-size: 15px;
  
  .ps-icon {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    color: white;
    box-shadow: 0 2px 8px rgba(0, 120, 215, 0.4);
  }
`;

const TerminalControls = styled.div`
  display: flex;
  gap: 8px;
`;

const TerminalBtn = styled.button`
  padding: 6px 12px;
  background: rgba(0, 120, 215, 0.2);
  color: #7ec8ff;
  border: 1px solid rgba(0, 120, 215, 0.4);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(0, 120, 215, 0.4);
    border-color: rgba(0, 120, 215, 0.8);
    color: #ffffff;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TerminalOutput = styled.div`
  flex: 1;
  background: #012456;
  padding: 12px 20px;
  padding-left: 24px;
  overflow-y: auto;
  font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #cccccc;
  white-space: pre-wrap;
  word-break: break-all;
  min-height: 0;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(0, 30, 60, 0.5);
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 120, 215, 0.5);
    border-radius: 4px;
    
    &:hover {
      background: rgba(0, 120, 215, 0.7);
    }
  }
`;

const OutputLine = styled.div`
  margin-bottom: 4px;
  
  &.command {
    color: #ffff00;
  }
  
  &.stdout {
    color: #cccccc;
  }
  
  &.stderr {
    color: #f14c4c;
  }
  
  &.success {
    color: #23d18b;
  }
  
  &.error {
    color: #f14c4c;
  }
  
  &.info {
    color: #3b8eea;
  }
`;

const TerminalInputRow = styled.div`
  display: flex;
  align-items: center;
  padding: 10px 20px;
  padding-left: 24px;
  background: linear-gradient(90deg, rgba(1, 36, 86, 0.95) 0%, rgba(0, 40, 80, 0.95) 100%);
  border-top: 1px solid rgba(0, 120, 215, 0.25);
  flex-shrink: 0;
`;

const PromptText = styled.span`
  color: #3b8eea;
  font-family: 'Cascadia Code', 'Consolas', monospace;
  font-size: 14px;
  margin-right: 8px;
  white-space: nowrap;
`;

const TerminalInput = styled.input`
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #ffffff;
  font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  caret-color: #ffffff;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
  }
`;

const RunButton = styled.button`
  padding: 10px 24px;
  background: linear-gradient(90deg, #0078d4 0%, #106ebe 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  margin-left: 16px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 120, 215, 0.3);
  
  &:hover:not(:disabled) {
    background: linear-gradient(90deg, #106ebe 0%, #1a7fd4 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 120, 215, 0.5);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    box-shadow: none;
  }
`;

// 页面标题区域
const PageTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
  flex-shrink: 0;
  
  h1 {
    margin: 0;
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(90deg, #64b5f6 0%, #42a5f5 50%, #2196f3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 30px rgba(100, 181, 246, 0.3);
  }
  
  .subtitle {
    color: #7a9cc6;
    font-size: 13px;
    padding-left: 12px;
    border-left: 2px solid rgba(100, 181, 246, 0.3);
  }
`;

const ServerManagement = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingServer, setEditingServer] = useState(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 3,  // 每页最多显示3条数据
    total: 0
  });
  
  // PowerShell 终端状态
  const [command, setCommand] = useState('');
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([
    { type: 'info', text: 'Windows PowerShell' },
    { type: 'info', text: '版权所有 (C) Microsoft Corporation。保留所有权利。' },
    { type: 'info', text: '' },
    { type: 'info', text: '尝试新的跨平台 PowerShell https://aka.ms/pscore6' },
    { type: 'info', text: '' },
  ]);
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [expanded, setExpanded] = useState(false);
  const outputRef = useRef(null);
  const inputRef = useRef(null);

  // 获取服务器列表
  const fetchServers = async (page = 1, pageSize = 3) => {
    setLoading(true);
    try {
      const response = await getServers(page, pageSize);
      console.log('API Response:', response); // 添加日志以便调试
      if (response && response.status === 'success') {
        // 按ID升序排序服务器数据
        const sortedServers = (response.data.servers || []).sort((a, b) => a.id - b.id);
        setServers(sortedServers);
        setPagination({
          current: page,
          pageSize: pageSize,
          total: response.data.pagination?.total_count || 0
        });
      } else {
        console.error('Invalid response format:', response);
        message.error('获取服务器列表失败: 响应格式错误');
      }
    } catch (error) {
      console.error('Error fetching servers:', error);
      message.error('获取服务器列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);
  
  // 自动滚动到终端底部
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [history]);
  
  // 执行PowerShell命令
  const runCommand = async () => {
    if (!command.trim() || busy) return;
    
    const cmd = command.trim();
    setCommand('');
    setBusy(true);
    
    // 添加命令到历史记录
    setCommandHistory(prev => [...prev, cmd]);
    setHistoryIndex(-1);
    
    // 显示命令
    setHistory(prev => [...prev, { type: 'command', text: `PS C:\\> ${cmd}` }]);
    
    try {
      const res = await axios.post('http://localhost:8000/api/terminal/exec', {
        command: cmd,
        timeout_seconds: 300
      });
      
      const data = res.data || {};
      
      // 添加stdout输出
      if (data.stdout) {
        setHistory(prev => [...prev, { type: 'stdout', text: data.stdout }]);
      }
      
      // 添加stderr输出
      if (data.stderr) {
        setHistory(prev => [...prev, { type: 'stderr', text: data.stderr }]);
      }
      
      // 显示返回码
      if (data.return_code !== 0) {
        setHistory(prev => [...prev, { type: 'error', text: `[Exit Code: ${data.return_code}]` }]);
      }
      
    } catch (e) {
      const errMsg = e?.response?.data?.detail || e.message || '执行失败';
      setHistory(prev => [...prev, { type: 'error', text: `错误: ${errMsg}` }]);
    } finally {
      setBusy(false);
      // 聚焦输入框
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 0);
    }
  };
  
  // 处理键盘事件
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      runCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex;
        setHistoryIndex(newIndex);
        setCommand(commandHistory[commandHistory.length - 1 - newIndex] || '');
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setCommand(commandHistory[commandHistory.length - 1 - newIndex] || '');
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCommand('');
      }
    }
  };
  
  // 清空终端
  const clearTerminal = () => {
    setHistory([
      { type: 'info', text: 'Windows PowerShell' },
      { type: 'info', text: '终端已清空' },
      { type: 'info', text: '' },
    ]);
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      key: 'index',
      width: 60,
      render: (_, __, index) => index + 1 + (pagination.current - 1) * pagination.pageSize,
    },
    {
      title: '地理位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
    },
    {
      title: '域名',
      dataIndex: 'domain',
      key: 'domain',
    },
    {
      title: '链路状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === '在线' ? '#52c41a' : status === '故障' ? '#f5222d' : '#faad14';
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {status}
          </span>
        );
      }
    },
    {
      title: '操作系统',
      dataIndex: 'os',
      key: 'os',
    },
    {
      title: '所属僵尸网络',
      dataIndex: 'botnet_name',
      key: 'botnet_name',
      render: (botnet_name) => botnet_name || '-',
    },
    {
      title: '节点总数统计',
      dataIndex: 'node_count',
      key: 'node_count',
      render: (count) => (count === null || count === undefined ? 'Null' : count),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <span>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个服务器吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 处理表格分页
  const handleTableChange = (pagination) => {
    fetchServers(pagination.current, pagination.pageSize);
  };

  // 打开添加服务器模态框
  const showAddModal = () => {
    setEditingServer(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑服务器模态框
  const handleEdit = (server) => {
    setEditingServer(server);
    form.setFieldsValue({
      location: server.location,
      ip: server.ip,
      domain: server.domain,
      status: server.status,
      os: server.os,
      botnet_name: server.botnet_name,
    });
    setModalVisible(true);
  };

  // 处理删除服务器
  const handleDelete = async (id) => {
    try {
      const response = await deleteServer(id);
      console.log('Delete Response:', response); // 添加日志以便调试
      if (response && response.status === 'success') {
        message.success('服务器删除成功');
        fetchServers(pagination.current, pagination.pageSize);
      } else {
        console.error('Invalid delete response:', response);
        message.error('删除服务器失败: 响应格式错误');
      }
    } catch (error) {
      console.error('Error deleting server:', error);
      message.error('删除服务器失败');
    }
  };

  // 处理模态框确认
  const handleModalOk = () => {
    form.validateFields().then(async (values) => {
      try {
        if (editingServer) {
          // 更新服务器
          const response = await updateServer(editingServer.id, values);
          console.log('Update Response:', response); // 添加日志以便调试
          if (response && response.status === 'success') {
            message.success('服务器更新成功');
            setModalVisible(false);
            fetchServers(pagination.current, pagination.pageSize);
          } else {
            console.error('Invalid update response:', response);
            message.error('更新服务器失败: 响应格式错误');
          }
        } else {
          // 添加服务器
          const response = await createServer(values);
          console.log('Create Response:', response); // 添加日志以便调试
          if (response && response.status === 'success') {
            message.success('服务器添加成功');
            setModalVisible(false);
            fetchServers(pagination.current, pagination.pageSize);
          } else {
            console.error('Invalid create response:', response);
            message.error('添加服务器失败: 响应格式错误');
          }
        }
      } catch (error) {
        console.error('Error saving server:', error);
        message.error(editingServer ? '更新服务器失败' : '添加服务器失败');
      }
    });
  };

  // 处理模态框取消
  const handleModalCancel = () => {
    setModalVisible(false);
  };

  return (
    <Container>
      {/* 页面标题 */}
      <PageTitle>
        <h1>C2 管理控制台</h1>
        <span className="subtitle">服务器管理 · 命令执行</span>
      </PageTitle>
      
      {/* C2服务器管理区域 */}
      <ServerSection>
        <Header>
          <Title><CodeOutlined /> C2 服务器列表</Title>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={showAddModal}
            style={{
              background: 'linear-gradient(90deg, #0078d4, #106ebe)',
              border: 'none',
              boxShadow: '0 2px 8px rgba(0, 120, 215, 0.4)'
            }}
          >
            添加服务器
          </Button>
        </Header>

        <Table
          columns={columns}
          dataSource={servers}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            pageSize: 3,
            showSizeChanger: false,
            showQuickJumper: false,
            simple: false,
            size: 'small'
          }}
          onChange={handleTableChange}
          size="small"
          scroll={{ x: 'max-content' }}
        />
      </ServerSection>

      {/* PowerShell 终端区域 */}
      <TerminalSection expanded={expanded}>
        <TerminalHeader>
          <TerminalTitle>
            <div className="ps-icon">PS</div>
            <span>PowerShell 终端</span>
            <span style={{ color: '#7ec8ff', fontSize: '12px', marginLeft: '8px', opacity: 0.7 }}>
              | 无限制命令执行
            </span>
          </TerminalTitle>
          <TerminalControls>
            <TerminalBtn onClick={clearTerminal} title="清空终端">
              <ClearOutlined /> 清空
            </TerminalBtn>
            <TerminalBtn onClick={() => setExpanded(!expanded)} title={expanded ? '收起' : '展开'}>
              {expanded ? <CompressOutlined /> : <ExpandOutlined />}
              {expanded ? '收起' : '展开'}
            </TerminalBtn>
          </TerminalControls>
        </TerminalHeader>
        
        <TerminalOutput ref={outputRef}>
          {history.map((item, index) => (
            <OutputLine key={index} className={item.type}>
              {item.text}
            </OutputLine>
          ))}
          {busy && <OutputLine className="info">⏳ 执行中...</OutputLine>}
        </TerminalOutput>
        
        <TerminalInputRow>
          <PromptText>PS C:\&gt;</PromptText>
          <TerminalInput
            ref={inputRef}
            placeholder={busy ? '命令执行中...' : '输入 PowerShell 命令，按 Enter 执行，↑↓ 浏览历史...'}
            value={command}
            onChange={e => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={busy}
            autoFocus
          />
          <RunButton onClick={runCommand} disabled={busy || !command.trim()}>
            {busy ? '执行中' : '▶ 运行'}
          </RunButton>
        </TerminalInputRow>
      </TerminalSection>

      <Modal
        title={editingServer ? '编辑服务器' : '添加服务器'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="location"
            label="地理位置"
            rules={[{ required: true, message: '请输入地理位置' }]}
          >
            <Input placeholder="例如：北京市朝阳区" />
          </Form.Item>

          <Form.Item
            name="ip"
            label="IP地址"
            rules={[
              { required: true, message: '请输入IP地址' },
              { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: 'IP地址格式不正确' }
            ]}
          >
            <Input placeholder="例如：192.168.1.1" />
          </Form.Item>

          <Form.Item
            name="domain"
            label="域名"
            rules={[{ required: true, message: '请输入域名' }]}
          >
            <Input placeholder="例如：example.com" />
          </Form.Item>

          <Form.Item
            name="status"
            label="链路状态"
            rules={[{ required: true, message: '请选择链路状态' }]}
          >
            <Select placeholder="请选择链路状态">
              <Option value="在线">在线</Option>
              <Option value="离线">离线</Option>
              <Option value="故障">故障</Option>
              <Option value="维护中">维护中</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="os"
            label="操作系统"
            rules={[{ required: true, message: '请输入操作系统' }]}
          >
            <Input placeholder="例如：CentOS 7.9" />
          </Form.Item>

          <Form.Item
            name="botnet_name"
            label="所控制的僵尸网络"
            rules={[{ required: false, message: '请输入僵尸网络名称' }]}
          >
            <Input placeholder="例如：mirai" />
          </Form.Item>
        </Form>
      </Modal>
    </Container>
  );
};

export default ServerManagement;

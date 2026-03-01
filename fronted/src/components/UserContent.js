import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { getApiUrl } from '../config/api';
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

const Button = styled.button`
  padding: 10px 18px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.5);
  background: linear-gradient(90deg, #1565c0, #1a73e8);
  color: white;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  box-shadow: 0 0 15px rgba(26, 115, 232, 0.3);
  font-weight: 500;
  
  &:hover {
    background: linear-gradient(90deg, #0d47a1, #1565c0);
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(26, 115, 232, 0.5);
    border-color: rgba(100, 181, 246, 0.8);
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

const ActionButton = styled(Button)`
  padding: 6px 12px;
  font-size: 13px;
  background: ${props => props.variant === 'edit' ? 'linear-gradient(90deg, #1976d2, #2196f3)' : props.variant === 'delete' ? 'linear-gradient(90deg, #d32f2f, #f44336)' : 'linear-gradient(90deg, #1565c0, #1a73e8)'};
  
  &:hover {
    background: ${props => props.variant === 'edit' ? 'linear-gradient(90deg, #115293, #1976d2)' : props.variant === 'delete' ? 'linear-gradient(90deg, #b71c1c, #d32f2f)' : 'linear-gradient(90deg, #0d47a1, #1565c0)'};
  }
`;

const TableContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  margin-bottom: 0;
  position: relative;
  display: flex;
  flex-direction: column;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: linear-gradient(135deg, rgba(15, 25, 35, 0.95) 0%, rgba(26, 35, 50, 0.95) 100%);
  border-radius: 8px;
  table-layout: fixed;
  border: 1px solid rgba(100, 181, 246, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
`;

const Th = styled.th`
  padding: 14px;
  background: linear-gradient(90deg, rgba(13, 71, 161, 0.3), rgba(21, 101, 192, 0.3));
  text-align: left;
  border-bottom: 2px solid rgba(100, 181, 246, 0.3);
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: 600;
  color: #64b5f6;
  transition: background 0.2s ease;
  box-shadow: 0 2px 10px rgba(26, 115, 232, 0.2);
  
  &:hover {
    background: #e0e0e0;
  }
`;

const Td = styled.td`
  padding: 14px;
  border-bottom: 1px solid rgba(100, 181, 246, 0.1);
  transition: all 0.2s ease;
  color: #e0e0e0;
`;

const Tr = styled.tr`
  &:hover {
    background: rgba(26, 115, 232, 0.15);
  }
  transition: all 0.2s ease;
`;

const Pagination = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 20px;
  flex-shrink: 0;
`;

const PageButton = styled.button`
  padding: 5px 10px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: ${props => props.active ? 'linear-gradient(90deg, #1565c0, #1a73e8)' : 'rgba(26, 115, 232, 0.1)'};
  color: ${props => props.active ? 'white' : '#8db4d8'};
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s ease;
  box-shadow: ${props => props.active ? '0 0 10px rgba(26, 115, 232, 0.3)' : 'none'};
  
  &:hover {
    background: ${props => props.active ? 'linear-gradient(90deg, #0d47a1, #1565c0)' : 'rgba(26, 115, 232, 0.2)'};
    border-color: rgba(100, 181, 246, 0.5);
  }
`;

// Modal styles
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background: linear-gradient(135deg, rgba(15, 25, 35, 0.98) 0%, rgba(26, 35, 50, 0.98) 100%);
  padding: 25px;
  border-radius: 12px;
  width: 450px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(26, 115, 232, 0.3);
  border: 1px solid rgba(100, 181, 246, 0.3);
  transform: translateY(0);
  animation: slideIn 0.3s ease;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const ModalHeader = styled.div`
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #64b5f6;
  border-bottom: 2px solid rgba(100, 181, 246, 0.3);
  padding-bottom: 15px;
  display: flex;
  align-items: center;
  text-shadow: 0 0 10px rgba(100, 181, 246, 0.3);
  
  &::before {
    content: ${props => props.isEdit ? '"✏️"' : '"👤"'};
    margin-right: 10px;
    font-size: 24px;
  }
`;

const FormGroup = styled.div`
  margin-bottom: 15px;
  position: relative;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  box-sizing: border-box;
  transition: all 0.3s ease;
  font-size: 15px;
  
  &:focus {
    border-color: #1a237e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
  }
  
  &::placeholder {
    color: #aaa;
  }
`;

const PasswordContainer = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const PasswordToggle = styled.button`
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  color: #666;
  font-size: 16px;
  transition: all 0.2s ease;
  
  &:hover {
    color: #1a237e;
  }
  
  &:focus {
    outline: none;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-sizing: border-box;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="6"><path d="M0 0l6 6 6-6z" fill="%23333"/></svg>');
  background-repeat: no-repeat;
  background-position: right 15px center;
  background-size: 12px;
  font-size: 15px;
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
  }
`;

const ModalFooter = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 25px;
  gap: 12px;
  border-top: 2px solid #e0e0e0;
  padding-top: 20px;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
`;

const ChartsContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
`;

const SearchInput = styled.input`
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 250px;
  margin-left: 10px;
  transition: all 0.2s ease;
  font-size: 14px;
  
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

const ActionButtonsContainer = styled.div`
  display: flex;
  gap: 5px;
`;

const Badge = styled.span`
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 500;
  background-color: ${props => 
    props.role === '管理员' ? '#e8eaf6' : 
    props.role === '操作员' ? '#e8f5e9' : '#fff3e0'};
  color: ${props => 
    props.role === '管理员' ? '#1a237e' : 
    props.role === '操作员' ? '#2e7d32' : '#f57c00'};
  border: 1px solid ${props => 
    props.role === '管理员' ? '#c5cae9' : 
    props.role === '操作员' ? '#c8e6c9' : '#ffe0b2'};
`;

const UserContent = () => {
  const [users, setUsers] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});
  const [editingUser, setEditingUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    totalUsers: 0,
    adminUsers: 0,
    operatorUsers: 0,
    viewerUsers: 0
  });
  const [activityData, setActivityData] = useState({
    dates: [],
    loginCounts: []
  });
  const [operationStats, setOperationStats] = useState({
    user_operations: [],
    operation_types: [],
    operation_trend: []
  });
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: '操作员'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 获取认证token
  const token = localStorage.getItem('token');
  const headers = {
    'Authorization': `Bearer ${token}`
  };

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/user/users'), { headers });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/user/statistics'), { headers });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  // 获取活动数据
  const fetchActivity = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/user/activity'), { headers });
      setActivityData(response.data);
    } catch (error) {
      console.error('Error fetching activity:', error);
    }
  };

  // 获取用户操作统计
  const fetchOperationStats = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/user/user-operations'), { headers });
      setOperationStats(response.data);
    } catch (error) {
      console.error('Error fetching operation statistics:', error);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchStats();
    fetchActivity();
    fetchOperationStats();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEdit = (user) => {
    setIsEditMode(true);
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',  // 不显示原密码
      role: user.role
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (userId) => {
    if (window.confirm('确定要删除此用户吗？')) {
      try {
        await axios.delete(getApiUrl(`/api/user/users/${userId}`), { headers });
        fetchUsers();  // 重新获取用户列表
      } catch (error) {
        console.error('Error deleting user:', error);
        alert('删除用户失败');
      }
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      if (isEditMode) {
        // 编辑现有用户
        await axios.put(
          getApiUrl(`/api/user/users/${editingUser.id}`),
          formData,
          { headers }
        );
      } else {
        // 创建新用户
        await axios.post(
          getApiUrl('/api/user/users'),
          formData,
          { headers }
        );
      }
      
      setIsModalOpen(false);
      setIsEditMode(false);
      setEditingUser(null);
      setFormData({
        username: '',
        password: '',
        role: '操作员'
      });
      
      fetchUsers();  // 重新获取用户列表
      
    } catch (error) {
      console.error('Error saving user:', error);
      alert(error.response?.data?.detail || '保存用户失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 过滤用户
  const filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.role.includes(searchTerm)
  );

  const itemsPerPage = 14;
  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
  const currentUsers = filteredUsers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // 准备图表数据
  const getRoleDistributionOption = () => ({
    title: {
      text: '用户角色分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['管理员', '操作员', '访客']
    },
    series: [{
      type: 'pie',
      radius: '70%',
      center: ['50%', '60%'],
      data: [
        { value: stats.adminUsers, name: '管理员', itemStyle: { color: '#1a237e' } },
        { value: stats.operatorUsers, name: '操作员', itemStyle: { color: '#2e7d32' } },
        { value: stats.viewerUsers, name: '访客', itemStyle: { color: '#f57c00' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}: {c} ({d}%)'
      }
    }]
  });

  const getActivityTrendOption = () => ({
    title: {
      text: '用户活动趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: activityData.dates || []
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '登录次数',
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#1a237e',
        width: 3
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0, color: 'rgba(26, 35, 126, 0.5)'
          }, {
            offset: 1, color: 'rgba(26, 35, 126, 0.1)'
          }]
        }
      },
      data: activityData.loginCounts || []
    }]
  });

  // 新增：操作类型分布图表
  const getOperationTypeOption = () => {
    // 确保数据存在
    if (!operationStats.operation_types || operationStats.operation_types.length === 0) {
      return {
        title: {
          text: '操作类型分布',
          left: 'center'
        },
        series: [{
          type: 'pie',
          radius: '70%',
          data: []
        }]
      };
    }

    return {
      title: {
        text: '操作类型分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: operationStats.operation_types.map(item => item.operation_type)
      },
      series: [{
        type: 'pie',
        radius: '70%',
        center: ['50%', '60%'],
        data: operationStats.operation_types.map(item => ({
          name: item.operation_type,
          value: item.count,
          itemStyle: {
            color: item.operation_type === '清除操作' ? '#2e7d32' :
                  item.operation_type === '再利用' ? '#1565c0' :
                  item.operation_type === '抑制操作' ? '#c2185b' :
                  item.operation_type === '其他操作' ? '#e65100' :
                  '#6a1b9a'
          }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {c} ({d}%)'
        }
      }]
    };
  };

  // 新增：用户操作统计表格（作为卡片样式）
  const renderUserOperationsCard = () => {
    if (!operationStats.user_operations || operationStats.user_operations.length === 0) {
      return (
        <div style={{
          background: 'linear-gradient(135deg, rgba(15, 25, 35, 0.95) 0%, rgba(26, 35, 50, 0.95) 100%)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(100, 181, 246, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}>
          <h3 style={{ marginBottom: '15px', color: '#64b5f6', fontWeight: '600', fontSize: '16px' }}>用户操作统计</h3>
          <p style={{ color: '#8db4d8' }}>暂无数据</p>
        </div>
      );
    }

    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(15, 25, 35, 0.95) 0%, rgba(26, 35, 50, 0.95) 100%)',
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid rgba(100, 181, 246, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        overflow: 'hidden'
      }}>
        <h3 style={{ marginBottom: '15px', color: '#64b5f6', fontWeight: '600', fontSize: '16px' }}>用户操作统计</h3>
        <div style={{ overflowX: 'auto' }}>
          <Table style={{ marginBottom: 0 }}>
            <thead>
              <tr>
                <Th style={{ padding: '10px 12px', fontSize: '13px' }}>用户名</Th>
                <Th style={{ padding: '10px 12px', fontSize: '13px' }}>操作次数</Th>
                <Th style={{ padding: '10px 12px', fontSize: '13px' }}>活跃天数</Th>
                <Th style={{ padding: '10px 12px', fontSize: '13px' }}>操作僵尸网络类型</Th>
                <Th style={{ padding: '10px 12px', fontSize: '13px' }}>最后操作时间</Th>
              </tr>
            </thead>
            <tbody>
              {operationStats.user_operations.map((op, index) => (
                <Tr key={index}>
                  <Td style={{ padding: '10px 12px', fontSize: '13px' }}>{op.username}</Td>
                  <Td style={{ padding: '10px 12px', fontSize: '13px' }}>{op.operation_count}</Td>
                  <Td style={{ padding: '10px 12px', fontSize: '13px' }}>{op.active_days}</Td>
                  <Td style={{ padding: '10px 12px', fontSize: '13px' }}>{op.botnet_types}</Td>
                  <Td style={{ padding: '10px 12px', fontSize: '13px' }}>{op.last_operation}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      </div>
    );
  };

  return (
    <Container>
      <StatsContainer>
        <StatCard
          title="总用户数"
          value={stats.totalUsers}
          trend="全部账户"
          background="linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)"
        />
        <StatCard
          title="管理员"
          value={stats.adminUsers}
          trend={`${((stats.adminUsers / stats.totalUsers) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #303f9f 0%, #1a237e 100%)"
        />
        <StatCard
          title="操作员"
          value={stats.operatorUsers}
          trend={`${((stats.operatorUsers / stats.totalUsers) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)"
        />
        <StatCard
          title="访客账户"
          value={stats.viewerUsers}
          trend={`${((stats.viewerUsers / stats.totalUsers) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)"
        />
      </StatsContainer>

      {/* 新增操作统计卡片 */}
      <StatsContainer>
        <StatCard
          title="总操作次数"
          value={operationStats.user_operations?.reduce((sum, user) => sum + user.operation_count, 0) || 0}
          trend="所有用户操作总数"
          background="linear-gradient(135deg, #c2185b 0%, #880e4f 100%)"
        />
        <StatCard
          title="清除操作"
          value={operationStats.operation_types?.find(op => op.operation_type === '清除操作')?.count || 0}
          trend="僵尸网络清除次数"
          background="linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)"
        />
        <StatCard
          title="抑制操作"
          value={operationStats.operation_types?.find(op => op.operation_type === '抑制操作')?.count || 0}
          trend="僵尸网络抑制次数"
          background="linear-gradient(135deg, #c62828 0%, #b71c1c 100%)"
        />
        <StatCard
          title="已操作的僵尸网络数量"
          value={operationStats.user_operations?.reduce((sum, user) => Math.max(sum, user.botnet_types || 0), 0) || 0}
          trend="不同类型僵尸网络"
          background="linear-gradient(135deg, #6a1b9a 0%, #4a148c 100%)"
        />
      </StatsContainer>

      <ChartsContainer>
        <ChartCard option={getOperationTypeOption()} height="300px" />
        {renderUserOperationsCard()}
      </ChartsContainer>

      <TopBar>
        <Button onClick={() => {
          setIsEditMode(false);
          setFormData({
            username: '',
            password: '',
            role: '操作员'
          });
          setIsModalOpen(true);
        }}>
          新建用户
        </Button>
        <SearchInput
          placeholder="搜索用户名或角色"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </TopBar>

      <TableContainer>
        <Table>
          <thead>
            <tr>
              <Th>账户ID</Th>
              <Th>账户名</Th>
              <Th>账户权限</Th>
              <Th>最后登录</Th>
              <Th>状态</Th>
              <Th>操作</Th>
            </tr>
          </thead>
          <tbody>
            {currentUsers.map(user => (
              <Tr key={user.id}>
                <Td>{user.id}</Td>
                <Td>{user.username}</Td>
                <Td>
                  <Badge role={user.role}>
                    {user.role}
                  </Badge>
                </Td>
                <Td>{user.lastLogin || '从未登录'}</Td>
                <Td>
                  <span style={{ 
                    color: user.status === '在线' ? '#2e7d32' : '#757575',
                    fontWeight: user.status === '在线' ? 'bold' : 'normal'
                  }}>
                    {user.status === '在线' ? '● ' : '○ '}
                    {user.status}
                  </span>
                </Td>
                <Td>
                  <ActionButtonsContainer>
                    <ActionButton
                      variant="edit"
                      onClick={() => handleEdit(user)}
                    >
                      编辑
                    </ActionButton>
                    {user.username !== 'admin' && (
                      <ActionButton
                        variant="delete"
                        onClick={() => handleDelete(user.id)}
                      >
                        删除
                      </ActionButton>
                    )}
                  </ActionButtonsContainer>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      </TableContainer>

      <Pagination>
        <PageButton
          onClick={() => setCurrentPage(1)}
          disabled={currentPage === 1}
        >
          首页
        </PageButton>
        <PageButton
          onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          disabled={currentPage === 1}
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
            >
              {pageToShow}
            </PageButton>
          );
        })}
        <PageButton
          onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          disabled={currentPage === totalPages}
        >
          下一页
        </PageButton>
        <PageButton
          onClick={() => setCurrentPage(totalPages)}
          disabled={currentPage === totalPages}
        >
          末页
        </PageButton>
      </Pagination>

      {isModalOpen && (
        <ModalOverlay>
          <ModalContent>
            <ModalHeader isEdit={isEditMode}>{isEditMode ? '编辑用户' : '新建用户'}</ModalHeader>
            <FormGroup>
              <Label>账户名</Label>
              <Input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="请输入账户名"
                disabled={isSubmitting}
              />
            </FormGroup>
            <FormGroup>
              <Label>账户密码{isEditMode && ' (留空表示不修改)'}</Label>
              <PasswordContainer>
                <Input
                  type={showPasswords.modal ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder={isEditMode ? "留空表示不修改密码" : "请输入账户密码"}
                  disabled={isSubmitting}
                />
                <PasswordToggle
                  onClick={() => setShowPasswords(prev => ({
                    ...prev,
                    modal: !prev.modal
                  }))}
                  title={showPasswords.modal ? "隐藏密码" : "显示密码"}
                >
                  {showPasswords.modal ? "👁️" : "👁️‍🗨️"}
                </PasswordToggle>
              </PasswordContainer>
            </FormGroup>
            <FormGroup>
              <Label>账户权限</Label>
              <Select
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                disabled={editingUser?.username === 'admin' || isSubmitting}
              >
                <option value="管理员">管理员</option>
                <option value="操作员">操作员</option>
                <option value="访客">访客</option>
              </Select>
            </FormGroup>
            <ModalFooter>
              <Button 
                onClick={() => {
                  setIsModalOpen(false);
                  setIsEditMode(false);
                  setEditingUser(null);
                  setFormData({
                    username: '',
                    password: '',
                    role: '操作员'
                  });
                }}
                style={{ background: '#f5f5f5', color: '#333' }}
                disabled={isSubmitting}
              >
                取消
              </Button>
              <Button 
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? '保存中...' : '确定'}
              </Button>
            </ModalFooter>
          </ModalContent>
        </ModalOverlay>
      )}
    </Container>
  );
};

export default UserContent; 
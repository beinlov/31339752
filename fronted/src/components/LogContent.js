import React, { useState, useEffect } from 'react';
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

const SearchGroup = styled.div`
  display: flex;
  gap: 10px;
  align-items: center;
  flex: 0 0 auto;
  margin-left: -1.5%;
`;

const Select = styled.select`
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  width: 150px;
  appearance: none;
  background-color: rgba(26, 115, 232, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="6"><path d="M0 0l6 6 6-6z" fill="%2364b5f6"/></svg>');
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 10px;
  font-size: 13px;
  color: #e0e0e0;
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:focus {
    border-color: #64b5f6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.2);
  }
  
  option {
    padding: 10px;
    background: #1a2332;
    color: #e0e0e0;
  }
`;

const SearchInput = styled.input`
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  width: 220px;
  transition: all 0.3s ease;
  font-size: 13px;
  color: #e0e0e0;
  
  &:focus {
    border-color: #64b5f6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.2);
  }
  
  &::placeholder {
    color: #7a9cc6;
  }
`;

const DateTimeGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 20px;
`;

const DateTimeInput = styled.input`
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  width: 180px;
  transition: all 0.3s ease;
  font-size: 13px;
  color: #e0e0e0;
  
  &:focus {
    border-color: #64b5f6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.2);
  }
  
  &::placeholder {
    color: #7a9cc6;
    font-size: 12px;
  }
`;

const TableContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
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
`;

const Th = styled.th`
  padding: 14px 16px;
  background: linear-gradient(90deg, rgba(13, 71, 161, 0.3), rgba(21, 101, 192, 0.3));
  text-align: left;
  border-bottom: 2px solid rgba(100, 181, 246, 0.3);
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: 600;
  color: #64b5f6;
  transition: background 0.2s ease;
  
  &:hover {
    background: rgba(13, 71, 161, 0.4);
  }
`;

const Td = styled.td`
  padding: 14px 16px;
  border-bottom: 1px solid rgba(100, 181, 246, 0.1);
  transition: all 0.2s ease;
  color: #e0e0e0;
`;

const Tr = styled.tr`
  &:hover {
    background: rgba(26, 115, 232, 0.15);
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(26, 115, 232, 0.2);
  }
  transition: all 0.2s ease;
`;

const Pagination = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
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
  font-size: 13px;
  
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

const SearchCard = styled.div`
  background: linear-gradient(135deg, rgba(10, 25, 41, 0.95) 0%, rgba(13, 31, 45, 0.95) 100%);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(30, 70, 120, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 280px;
  box-sizing: border-box;
  justify-content: center;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(30, 70, 120, 0.6), transparent);
  }
`;

const SearchCardTitle = styled.h3`
  margin: 0 0 5px 0;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
`;

const CommandBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 16px;
  font-size: 0.8em;
  font-weight: 500;
  background-color: ${props => {
    if (props.command.includes('clear')) return 'rgba(76, 175, 80, 0.2)';
    if (props.command.includes('reuse')) return 'rgba(33, 150, 243, 0.2)';
    if (props.command.includes('ddos')) return 'rgba(244, 67, 54, 0.2)';
    if (props.command.includes('suppress')) return 'rgba(255, 152, 0, 0.2)';
    return 'rgba(156, 39, 176, 0.2)';
  }};
  color: ${props => {
    if (props.command.includes('clear')) return '#81c784';
    if (props.command.includes('reuse')) return '#64b5f6';
    if (props.command.includes('ddos')) return '#ef5350';
    if (props.command.includes('suppress')) return '#ffb74d';
    return '#ba68c8';
  }};
  border: 1px solid ${props => {
    if (props.command.includes('clear')) return 'rgba(76, 175, 80, 0.4)';
    if (props.command.includes('reuse')) return 'rgba(33, 150, 243, 0.4)';
    if (props.command.includes('ddos')) return 'rgba(244, 67, 54, 0.4)';
    if (props.command.includes('suppress')) return 'rgba(255, 152, 0, 0.4)';
    return 'rgba(156, 39, 176, 0.4)';
  }};
  transition: all 0.2s ease;
  
  &::before {
    content: ${props => {
      if (props.command.includes('clear')) return '"🧹 "';
      if (props.command.includes('reuse')) return '"♻️ "';
      if (props.command.includes('ddos')) return '"⚔️ "';
      if (props.command.includes('suppress')) return '"🛡️ "';
      return '"❓ "';
    }};
    margin-right: 4px;
    font-size: 1em;
  }
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(26, 115, 232, 0.3);
  }
`;

const NetworkIcon = styled.span`
  display: inline-block;
  margin-right: 8px;
  font-size: 1.2em;
`;

// 获取网络图标
const getNetworkIcon = (network) => {
  if (network === 'asruex') return '🟢';
  if (network === 'andromeda') return '🔵';
  if (network === 'mozi') return '🟠';
  if (network === 'leethozer') return '🟣';
  return '⚪';
};

// 获取当前时间的函数
const getCurrentDateTime = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${year}/${month}/${day}-${hours}:${minutes}`;
};

// 添加加载指示器组件
const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #64b5f6;
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

// 添加命令转换函数
const translateCommand = (command) => {
  if (command.includes('clear')) return '清除节点';
  if (command.includes('reuse')) return '节点再利用';
  if (command.includes('ddos')) return 'DDos攻击';
  if (command.includes('suppress')) return '抑制阻断';
  return command; // 如果没有匹配的命令，返回原始命令
};

const LogContent = ({ networkType }) => {
  const [logs, setLogs] = useState([]);
  const [searchType, setSearchType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [startDateTime, setStartDateTime] = useState('');
  const [endDateTime, setEndDateTime] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const itemsPerPage = 14;

  // 获取日志数据
  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      // 使用统一的日志接口
      const response = await fetch('http://localhost:8000/api/user-events');
      if (!response.ok) {
        throw new Error('Failed to fetch logs');
      }
      const data = await response.json();
      console.log('获取到的日志数据:', data);
      
      // 如果指定了网络类型，则过滤日志
      if (networkType && networkType !== '') {
        const filteredData = data.filter(log => log.botnet_type === networkType);
        setLogs(filteredData || []);
        console.log(`已过滤 ${networkType} 网络的日志，共 ${filteredData.length} 条`);
      } else {
        setLogs(data || []);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
      // 不再返回假数据，而是返回空数组
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [networkType]); // 当网络类型变化时重新获取日志

  // 更新结束时间的placeholder
  useEffect(() => {
    const interval = setInterval(() => {
      const dateTimeInput = document.querySelector('input[placeholder*="结束时间"]');
      if (dateTimeInput) {
        dateTimeInput.placeholder = `结束时间 (${getCurrentDateTime()})`;
      }
    }, 60000); // 每分钟更新一次

    return () => clearInterval(interval);
  }, []);

  // 过滤和排序逻辑
  const filteredLogs = logs
    .filter(log => {
      // 日期时间范围过滤
      if (startDateTime && endDateTime) {
        const logDateTime = log.time;
        const start = new Date(startDateTime.replace('-', ' '));
        const end = new Date(endDateTime.replace('-', ' '));
        const logDate = new Date(logDateTime);
        if (logDate < start || logDate > end) return false;
      }

      // 搜索条件过滤
      if (!searchTerm) return true;
      
      switch (searchType) {
        case 'account':
          return log.username?.toLowerCase().includes(searchTerm.toLowerCase());
        case 'location':
          return log.location?.toLowerCase().includes(searchTerm.toLowerCase());
        case 'network':
          return log.botnet_type?.toLowerCase().includes(searchTerm.toLowerCase());
        case 'command':
          return log.command?.toLowerCase().includes(searchTerm.toLowerCase());
        case 'all':
        default:
          return Object.values(log).some(value => 
            String(value).toLowerCase().includes(searchTerm.toLowerCase())
          );
      }
    })
    .sort((a, b) => {
      const dateTimeA = new Date(a.time);
      const dateTimeB = new Date(b.time);
      return dateTimeB - dateTimeA; // 降序排列，最新的在前面
    });

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const currentLogs = filteredLogs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // 计算统计数据
  const stats = {
    totalLogs: logs.length,
    adminLogs: logs.filter(log => log.username === 'admin').length,
    todayLogs: logs.filter(log => {
      const today = new Date();
      const logDate = new Date(log.time);
      return logDate.toDateString() === today.toDateString();
    }).length,
    uniqueLocations: new Set(logs.map(log => log.location)).size
  };

  // 准备图表数据
  const getCommandTypeOption = () => {
    // 分析命令类型
    const commandTypes = {};
    
    logs.forEach(log => {
      const command = log.command;
      if (command.includes('clear')) {
        commandTypes['清除节点'] = (commandTypes['清除节点'] || 0) + 1;
      } else if (command.includes('reuse')) {
        commandTypes['节点再利用'] = (commandTypes['节点再利用'] || 0) + 1;
      } else if (command.includes('ddos')) {
        commandTypes['DDos攻击'] = (commandTypes['DDos攻击'] || 0) + 1;
      } else if (command.includes('suppress')) {
        commandTypes['抑制阻断'] = (commandTypes['抑制阻断'] || 0) + 1;
      } else {
        commandTypes['其他操作'] = (commandTypes['其他操作'] || 0) + 1;
      }
    });
    
    // 转换为图表数据
    const data = Object.entries(commandTypes)
      .filter(([_, value]) => value > 0) // 只包含有数据的类型
      .map(([type, value]) => ({
        name: type,
        value
      }))
      .sort((a, b) => b.value - a.value); // 降序排列
    
    return {
      title: {
        text: '命令类型分布',
        left: 'center',
        top: '5%',
        textStyle: {
          fontWeight: 'bold',
          fontSize: 20,
          color: '#ffffff'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
        backgroundColor: 'rgba(15, 25, 35, 0.95)',
        borderColor: 'rgba(100, 181, 246, 0.3)',
        textStyle: {
          color: '#ffffff'
        }
      },
      legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 10,
        top: 40,
        bottom: 20,
        textStyle: {
          color: '#ffffff',
          fontSize: 12
        },
        pageTextStyle: {
          color: '#ffffff'
        }
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'rgba(15, 25, 35, 0.8)',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold',
            color: '#ffffff'
          }
        },
        labelLine: {
          show: false
        },
        data: data.map(item => ({
          ...item,
          itemStyle: {
            color: item.name === '清除节点' ? '#4caf50' :
                  item.name === '节点再利用' ? '#2196f3' :
                  item.name === 'DDos攻击' ? '#f44336' :
                  item.name === '抑制阻断' ? '#ff9800' :
                  '#9c27b0'
          }
        }))
      }]
    };
  };

  return (
    <Container>
      <StatsContainer>
        <StatCard
          title="总日志数"
          value={stats.totalLogs}
          trend="全部操作记录"
          background="linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)"
          titleIcon="📊"
        />
        <StatCard
          title="管理员操作"
          value={stats.adminLogs}
          trend={`${((stats.adminLogs / stats.totalLogs) * 100).toFixed(1)}% 管理员操作率`}
          background="linear-gradient(135deg, #c62828 0%, #b71c1c 100%)"
          titleIcon="👤"
        />
        <StatCard
          title="今日操作"
          value={stats.todayLogs}
          trend="今日活动数量"
          background="linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)"
          titleIcon="📅"
        />
        <StatCard
          title="操作地点"
          value={stats.uniqueLocations}
          trend="不同操作地点数"
          background="linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)"
          titleIcon="📍"
        />
      </StatsContainer>

      <ChartsContainer>
        <ChartCard 
          option={getCommandTypeOption()} 
          height="280px" 
          loading={isLoading}
          accentColor="linear-gradient(90deg, #0d47a1, #1565c0)"
        />
        <SearchCard>
          <SearchCardTitle>🔍 日志搜索</SearchCardTitle>
          <SearchGroup style={{ marginLeft: 0 }}>
            <Select 
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
            >
              <option value="all">全部</option>
              <option value="account">账户名</option>
              <option value="location">账户所在地</option>
              <option value="network">目标僵尸网络</option>
            </Select>
            <SearchInput
              placeholder="请输入关键字"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchGroup>
          <DateTimeGroup style={{ marginLeft: 0 }}>
            <span style={{ color: '#8db4d8', fontSize: '13px', whiteSpace: 'nowrap' }}>时间范围</span>
            <DateTimeInput
              type="text"
              placeholder="起始时间 (2024/3/17-11:57)"
              value={startDateTime}
              onChange={(e) => setStartDateTime(e.target.value)}
            />
            <span style={{ color: '#8db4d8', fontSize: '13px' }}>至</span>
            <DateTimeInput
              type="text"
              placeholder={`结束时间 (${getCurrentDateTime()})`}
              value={endDateTime}
              onChange={(e) => setEndDateTime(e.target.value)}
            />
          </DateTimeGroup>
        </SearchCard>
      </ChartsContainer>

      <TableContainer>
        <Table>
          <thead>
            <tr>
              <Th>时间</Th>
              <Th>操作用户</Th>
              <Th>操作地点</Th>
              <Th>目标节点IP</Th>
              <Th>目标网络</Th>
              <Th>操作内容</Th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <Tr>
                <Td colSpan={6}>
                  <LoadingContainer>
                    <Spinner />
                    <div style={{ fontWeight: 500 }}>加载中...</div>
                  </LoadingContainer>
                </Td>
              </Tr>
            ) : currentLogs.length > 0 ? (
              currentLogs.map((log, index) => (
                <Tr key={index}>
                  <Td>{log.time}</Td>
                  <Td>{log.username}</Td>
                  <Td>{log.location}</Td>
                  <Td>{log.ip}</Td>
                  <Td>
                    <NetworkIcon>{getNetworkIcon(log.botnet_type)}</NetworkIcon>
                    {log.botnet_type === 'asruex' ? 'Asruex僵尸网络' : 
                     log.botnet_type === 'andromeda' ? 'Andromeda僵尸网络' : 
                     log.botnet_type === 'mozi' ? 'Mozi僵尸网络' : 
                     log.botnet_type === 'leethozer' ? 'LeetHozer僵尸网络' : 
                     log.botnet_type}
                  </Td>
                  <Td>
                    <CommandBadge command={log.command}>
                      {translateCommand(log.command)}
                    </CommandBadge>
                  </Td>
                </Tr>
              ))
            ) : (
              <Tr>
                <Td colSpan={6} style={{ textAlign: 'center', padding: '40px' }}>
                  <div style={{ fontSize: '18px', color: '#999', marginBottom: '10px' }}>😕</div>
                  没有找到匹配的记录
                </Td>
              </Tr>
            )}
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
          // 显示当前页附近的页码
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
    </Container>
  );
};

export default LogContent; 
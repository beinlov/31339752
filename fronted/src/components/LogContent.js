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

const TopBar = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 0px;
  padding: 20px;
  flex-shrink: 0;
`;

const SearchGroup = styled.div`
  display: flex;
  gap: 10px;
  align-items: center;
  flex: 0 0 auto;
  margin-left: -1.5%;
`;

const Select = styled.select`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 150px;
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
  
  option {
    padding: 10px;
  }
`;

const SearchInput = styled.input`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 220px;
  transition: all 0.3s ease;
  font-size: 14px;
  
  &:focus {
    border-color: #1a237e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
    width: 250px;
  }
  
  &::placeholder {
    color: #aaa;
  }
`;

const DateTimeGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 20px;
`;

const DateTimeInput = styled.input`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 200px;
  transition: all 0.3s ease;
  font-size: 14px;
  
  &:focus {
    border-color: #1a237e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
  }
  
  &::placeholder {
    color: #aaa;
    font-size: 13px;
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

const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  border-radius: 8px;
  table-layout: fixed;
`;

const Th = styled.th`
  padding: 16px;
  background: #f5f5f5;
  text-align: left;
  border-bottom: 2px solid #ddd;
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: 600;
  color: #333;
  transition: background 0.2s ease;
  
  &:hover {
    background: #e0e0e0;
  }
`;

const Td = styled.td`
  padding: 16px;
  border-bottom: 1px solid #eee;
  transition: all 0.2s ease;
`;

const Tr = styled.tr`
  &:hover {
    background: #f8f9ff;
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
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
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  flex-shrink: 0;
`;

const CommandBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 500;
  background-color: ${props => {
    if (props.command.includes('clear')) return '#e8f5e9';
    if (props.command.includes('reuse')) return '#e3f2fd';
    if (props.command.includes('ddos')) return '#fce4ec';
    if (props.command.includes('suppress')) return '#fff3e0';
    return '#f3e5f5';
  }};
  color: ${props => {
    if (props.command.includes('clear')) return '#2e7d32';
    if (props.command.includes('reuse')) return '#1565c0';
    if (props.command.includes('ddos')) return '#c2185b';
    if (props.command.includes('suppress')) return '#e65100';
    return '#6a1b9a';
  }};
  border: 1px solid ${props => {
    if (props.command.includes('clear')) return '#a5d6a7';
    if (props.command.includes('reuse')) return '#90caf9';
    if (props.command.includes('ddos')) return '#f48fb1';
    if (props.command.includes('suppress')) return '#ffcc80';
    return '#ce93d8';
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
    font-size: 1.1em;
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
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
  color: #1a237e;
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
      const response = await fetch('/api/user-events');
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
  const getActivityTrendOption = () => {
    // 获取唯一的日期
    const dates = Array.from(new Set(logs.map(log => log.time.split(' ')[0])));
    
    // 获取唯一的网络
    const networks = Array.from(new Set(logs.map(log => log.botnet_type)));
    const networkColors = {
      'asruex': '#2e7d32',
      'andromeda': '#0d47a1',
      'mozi': '#e65100',
      'leethozer': '#6a1b9a'
    };
    
    // 为每个网络准备数据
    const series = networks.map(network => {
      const data = dates.map(date => 
        logs.filter(log => 
          log.time.startsWith(date) && 
          log.botnet_type === network
        ).length
      );
      
      return {
        name: network === 'asruex' ? 'Asruex僵尸网络' : 
              network === 'andromeda' ? 'Andromeda僵尸网络' : 
              network === 'mozi' ? 'Mozi僵尸网络' :
              network === 'leethozer' ? 'LeetHozer僵尸网络' :
              network,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: networkColors[network] || '#607d8b'
        },
        itemStyle: {
          color: networkColors[network] || '#607d8b'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, 
              color: `${networkColors[network] || '#607d8b'}50` // 添加透明度
            }, {
              offset: 1, 
              color: `${networkColors[network] || '#607d8b'}10`
            }]
          }
        },
        data
      };
    });

    return {
      title: {
        text: '操作活动趋势',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        }
      },
      legend: {
        data: networks.map(network => 
          network === 'asruex' ? 'Asruex僵尸网络' : 
          network === 'andromeda' ? 'Andromeda僵尸网络' : 
          network === 'mozi' ? 'Mozi僵尸网络' :
          network === 'leethozer' ? 'LeetHozer僵尸网络' :
          network
        ),
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
        top: 80
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '操作次数',
        nameTextStyle: {
          padding: [0, 0, 0, 40]
        }
      },
      series
    };
  };

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
          show: false
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
        data: data.map(item => ({
          ...item,
          itemStyle: {
            color: item.name === '清除节点' ? '#2e7d32' :
                  item.name === '节点再利用' ? '#1565c0' :
                  item.name === 'DDos攻击' ? '#c2185b' :
                  item.name === '抑制阻断' ? '#e65100' :
                  '#6a1b9a'
          }
        }))
      }]
    };
  };

  const getLocationHeatOption = () => {
    // 统计位置数据
    const locationData = {};
    logs.forEach(log => {
      if (!locationData[log.location]) {
        locationData[log.location] = 1;
      } else {
        locationData[log.location]++;
      }
    });
    
    // 转换为图表数据
    const data = Object.entries(locationData)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
    
    return {
      title: {
        text: '操作地理分布热力',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} 次操作'
      },
      visualMap: {
        min: 0,
        max: Math.max(...data.map(item => item.value), 1),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '5%',
        inRange: {
          color: ['#e8f5e9', '#c8e6c9', '#a5d6a7', '#81c784', '#66bb6a', '#4caf50', '#43a047', '#388e3c', '#2e7d32', '#1b5e20']
        }
      },
      series: [{
        type: 'map',
        map: 'china',
        roam: true,
        label: {
          show: true
        },
        emphasis: {
          label: {
            show: true
          },
          itemStyle: {
            areaColor: '#2e7d32'
          }
        },
        data
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
          option={getActivityTrendOption()} 
          height="300px" 
          loading={isLoading}
          accentColor="linear-gradient(90deg, #1a237e, #0d47a1)"
        />
        <ChartCard 
          option={getCommandTypeOption()} 
          height="300px" 
          loading={isLoading}
          accentColor="linear-gradient(90deg, #c62828, #b71c1c)"
        />
      </ChartsContainer>

      <TopBar>
        <SearchGroup>
          <Select 
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
          >
            <option value="all">全部</option>
            <option value="account">账户名</option>
            <option value="location">账户所在地</option>
            <option value="network">目标僵尸网络</option>
            <option value="command">指令信息</option>
          </Select>
          <SearchInput
            placeholder="请输入关键字"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </SearchGroup>
        <DateTimeGroup>
          <span>时间范围</span>
          <DateTimeInput
            type="text"
            placeholder="起始时间 (2024/3/17-11:57)"
            value={startDateTime}
            onChange={(e) => setStartDateTime(e.target.value)}
          />
          <span>至</span>
          <DateTimeInput
            type="text"
            placeholder={`结束时间 (${getCurrentDateTime()})`}
            value={endDateTime}
            onChange={(e) => setEndDateTime(e.target.value)}
          />
        </DateTimeGroup>
      </TopBar>

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
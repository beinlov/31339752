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
  color: #e6efff;
`;

const TopBar = styled.div`
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 0px;
  padding: 20px;
  flex-shrink: 0;
  background: rgba(6, 19, 33, 0.92);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(2, 12, 24, 0.55);
`;

const SearchGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  flex: 1;
`;

const StyledSelect = styled.select`
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(120, 160, 220, 0.5);
  width: 140px;
  background: rgba(12, 27, 45, 0.9);
  color: #f5f7ff;
  outline: none;
  transition: all 0.2s ease;
  box-shadow: inset 0 0 0 1px rgba(34, 75, 130, 0.4);

  &:focus {
    border-color: #4f8dff;
    box-shadow: 0 0 0 2px rgba(79, 141, 255, 0.25);
  }

  option {
    color: #0b1829;
  }
`;

const DateRangeGroup = styled.div`
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-right: 20px;
`;

const Label = styled.span`
  color: #cfdcff;
  white-space: nowrap;
  font-weight: 500;
`;

const Input = styled.input`
  padding: 10px 14px;
  border: 1px solid rgba(120, 160, 220, 0.5);
  border-radius: 10px;
  width: ${props => props.width || '180px'};
  transition: all 0.2s ease;
  background: rgba(12, 27, 45, 0.9);
  color: #f5f7ff;
  box-shadow: inset 0 0 0 1px rgba(34, 75, 130, 0.4);
  
  &:focus {
    outline: none;
    border-color: #4f8dff;
    box-shadow: 0 0 0 2px rgba(79, 141, 255, 0.25);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const SearchInput = styled(Input)`
  width: 200px;
`;

const SearchButton = styled.button`
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f8dff 0%, #2f4adf 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
  
  &:hover {
    background: linear-gradient(135deg, #5b96ff 0%, #3a57ff 100%);
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(47, 74, 223, 0.35);
  }
  
  &:active {
    transform: translateY(0);
    box-shadow: none;
  }
`;

const TableContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  border-radius: 16px;
  box-shadow: 0 20px 45px rgba(1, 8, 20, 0.65);
  margin-bottom: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  background: rgba(5, 14, 28, 0.95);
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: transparent;
  border-radius: 16px;
  table-layout: fixed;
`;

const Th = styled.th`
  padding: 14px;
  background: rgba(15, 36, 60, 0.95);
  text-align: left;
  border-bottom: 2px solid rgba(56, 96, 140, 0.45);
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: 600;
  color: #dbe5ff;
`;

const Td = styled.td`
  padding: 14px;
  border-bottom: 1px solid rgba(49, 81, 120, 0.45);
  transition: all 0.2s ease;
  color: #eef2ff;
`;

const Tr = styled.tr`
  &:hover {
    background: rgba(39, 76, 128, 0.35);
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
  color: #cfdcff;
`;

const PageButton = styled.button`
  padding: 6px 12px;
  border: 1px solid rgba(82, 120, 170, 0.6);
  background: ${props => props.active ? 'linear-gradient(135deg, #4f8dff, #2f4adf)' : 'rgba(10, 25, 41, 0.8)'};
  color: ${props => props.active ? 'white' : '#cdd8ff'};
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  
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
  
  @media (max-width: 1100px) {
    grid-template-columns: repeat(2, minmax(200px, 1fr));
  }
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
`;

const ContentRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  width: 100%;
  align-items: flex-start;
`;

const SeveritySection = styled.div`
  flex: 0 0 38%;
  max-width: 520px;
  min-width: 360px;
  flex-shrink: 0;
  
  @media (max-width: 1400px) {
    flex: 0 0 45%;
    max-width: none;
  }

  @media (max-width: 1200px) {
    flex: 0 0 100%;
    max-width: none;
  }
`;

const ListSection = styled.div`
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;

  @media (max-width: 1400px) {
    flex: 1;
  }

  @media (max-width: 1200px) {
    width: 100%;
  }
`;

const AnomalyBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 500;
  background-color: ${props => {
    if (props.type.includes('DDoS')) return '#ffebee';
    if (props.type.includes('流量')) return '#e3f2fd';
    if (props.type.includes('未授权')) return '#fff3e0';
    if (props.type.includes('恶意软件')) return '#e8f5e9';
    if (props.type.includes('数据泄露')) return '#f3e5f5';
    return '#e0f2f1';
  }};
  color: ${props => {
    if (props.type.includes('DDoS')) return '#c62828';
    if (props.type.includes('流量')) return '#0d47a1';
    if (props.type.includes('未授权')) return '#e65100';
    if (props.type.includes('恶意软件')) return '#2e7d32';
    if (props.type.includes('数据泄露')) return '#6a1b9a';
    return '#00695c';
  }};
  border: 1px solid ${props => {
    if (props.type.includes('DDoS')) return '#ef9a9a';
    if (props.type.includes('流量')) return '#90caf9';
    if (props.type.includes('未授权')) return '#ffcc80';
    if (props.type.includes('恶意软件')) return '#a5d6a7';
    if (props.type.includes('数据泄露')) return '#ce93d8';
    return '#80cbc4';
  }};
`;

const SeverityIndicator = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 5px;
  
  &::before {
    content: '';
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: ${props => {
      switch (props.level) {
        case 'high': return '#c62828';
        case 'medium': return '#f57c00';
        case 'low': return '#2e7d32';
        default: return '#757575';
      }
    }};
  }
  
  color: ${props => {
    switch (props.level) {
      case 'high': return '#c62828';
      case 'medium': return '#f57c00';
      case 'low': return '#2e7d32';
      default: return '#757575';
    }
  }};
  font-weight: 500;
`;

const normalizeSeverity = (value) => {
  if (!value) return 'low';
  const mapping = {
    '高危': 'high',
    '高': 'high',
    '中危': 'medium',
    '中': 'medium',
    '低危': 'low',
    '低': 'low'
  };
  return mapping[value] || value;
};

const ReportContent = () => {
  const [reports, setReports] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all'); // 'all', 'high', 'medium', 'low'
  const [error, setError] = useState(null);

  const itemsPerPage = 14;
  
  // 获取异常报告数据
  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/anomaly-reports');
      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }
      const data = await response.json();
      console.log('获取到的异常报告数据:', data);
      const normalized = (data || []).map(report => ({
        ...report,
        severity: normalizeSeverity(report.severity)
      }));
      setReports(normalized);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError('获取异常报告数据失败，请稍后再试');
      setReports([]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 组件加载时获取数据
  useEffect(() => {
    fetchReports();
  }, []);
  
  // 过滤和搜索逻辑
  const filteredReports = reports.filter(report => {
    // 搜索词过滤
    const matchesSearch = 
      report.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.ip.includes(searchTerm) ||
      report.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    // 日期范围过滤
    const reportDate = new Date(report.time);
    const start = startDate ? new Date(startDate) : null;
    const end = endDate ? new Date(endDate) : null;
    const matchesDateRange = (!start || reportDate >= start) && (!end || reportDate <= end);
    
    // 严重程度过滤
    const matchesSeverity = severityFilter === 'all' || report.severity === severityFilter;
    
    return matchesSearch && matchesDateRange && matchesSeverity;
  });

  const totalPages = Math.ceil(filteredReports.length / itemsPerPage);
  const currentReports = filteredReports.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSearch = () => {
    setCurrentPage(1);
    // 实际应用中这里可能需要调用API
  };
  
  const handleSeverityFilter = (severity) => {
    setSeverityFilter(severity);
    setCurrentPage(1);
  };

  // 计算统计数据
  const stats = {
    totalReports: reports.length,
    highSeverity: reports.filter(report => report.severity === 'high').length,
    mediumSeverity: reports.filter(report => report.severity === 'medium').length,
    lowSeverity: reports.filter(report => report.severity === 'low').length,
    ddosAttacks: reports.filter(report => report.description.includes('DDoS')).length,
    malwareReports: reports.filter(report => report.description.includes('恶意软件')).length,
    dataLeaks: reports.filter(report => report.description.includes('数据泄露')).length,
    unauthorizedAccess: reports.filter(report => report.description.includes('未授权')).length,
    trafficAnomaly: reports.filter(report => report.description.includes('流量')).length
  };

  // 准备图表数据
  const getAnomalyTrendOption = () => {
    // 获取最近几天的日期
    const dates = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      const formattedDate = `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
      dates.push(formattedDate);
    }
    
    const anomalyTypes = ['DDoS攻击', '异常流量', '未授权访问', '恶意软件', '数据泄露'];
    const typeColors = {
      'DDoS攻击': '#c62828',
      '异常流量': '#0d47a1',
      '未授权访问': '#e65100',
      '恶意软件': '#2e7d32',
      '数据泄露': '#6a1b9a'
    };
    
    return {
      title: {
        text: '异常类型趋势',
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
      legend: {
        data: anomalyTypes,
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
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '异常数量',
        nameTextStyle: {
          padding: [0, 0, 0, 40]
        }
      },
      series: anomalyTypes.map(type => ({
        name: type,
        type: 'bar',
        stack: 'total',
        emphasis: {
          focus: 'series'
        },
        itemStyle: {
          color: typeColors[type]
        },
        data: dates.map(date => {
          // 为每个日期和类型生成随机数据
          const dayReports = reports.filter(report => 
            report.time.startsWith(date) && 
            report.description.includes(type)
          );
          return dayReports.length;
        })
      }))
    };
  };

  const getLocationDistributionOption = () => ({
    title: {
      text: '地理分布',
      left: 'center',
      textStyle: {
        fontWeight: 'normal',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(6, 19, 33, 0.95)',
      borderColor: '#4f8dff',
      borderWidth: 1,
      textStyle: {
        color: '#f5f8ff'
      },
      padding: 12
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
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: Array.from(
        reports.reduce((acc, report) => {
          acc.set(report.location, (acc.get(report.location) || 0) + 1);
          return acc;
        }, new Map())
      ).map(([name, value]) => ({ name, value }))
    }]
  });
  
  const getSeverityDistributionOption = () => {
    const severityData = [
      { name: '高危', value: stats.highSeverity, itemStyle: { color: '#c62828' } },
      { name: '中危', value: stats.mediumSeverity, itemStyle: { color: '#f57c00' } },
      { name: '低危', value: stats.lowSeverity, itemStyle: { color: '#2e7d32' } }
    ];
    
    return {
      title: {
        text: '异常严重程度分布',
        left: 'center',
        textStyle: {
          fontWeight: 'normal',
          fontSize: 16,
          color: '#f5f8ff'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
        backgroundColor: 'rgba(6, 19, 33, 0.95)',
        borderColor: '#4f8dff',
        borderWidth: 1,
        textStyle: {
          color: '#f5f8ff'
        },
        padding: 12
      },
      legend: {
        bottom: 10,
        left: 'center',
        data: severityData.map(item => item.name),
        textStyle: {
          color: '#f5f8ff'
        }
      },
      series: [{
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        data: severityData,
        minAngle: 6,
        avoidLabelOverlap: false,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {c} ({d}%)',
          color: '#ffffff',
          fontSize: 14
        },
        labelLine: {
          show: true,
          smooth: true,
          length: 15,
          length2: 10,
          lineStyle: {
            color: '#f5f8ff'
          }
        }
      }]
    };
  };

  return (
    <Container>
      <StatsContainer>
        <StatCard
          title="总异常数"
          value={stats.totalReports}
          trend="全部异常报告"
          background="linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)"
          titleIcon="🔔"
        />
        <StatCard
          title="高危异常"
          value={stats.highSeverity}
          trend={`${((stats.highSeverity / stats.totalReports) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #c62828 0%, #b71c1c 100%)"
          titleIcon="⚠️"
        />
        <StatCard
          title="DDoS攻击"
          value={stats.ddosAttacks}
          trend={`${((stats.ddosAttacks / stats.totalReports) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #6a1b9a 0%, #4a148c 100%)"
          titleIcon="🛡️"
        />
        <StatCard
          title="恶意软件"
          value={stats.malwareReports}
          trend={`${((stats.malwareReports / stats.totalReports) * 100).toFixed(1)}% 占比`}
          background="linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)"
          titleIcon="🦠"
        />
      </StatsContainer>

      <ContentRow>
        <SeveritySection>
          <ChartCard 
            option={getSeverityDistributionOption()} 
            height="480px"
            loading={isLoading}
            accentColor="linear-gradient(90deg, #c62828, #b71c1c)"
          />
        </SeveritySection>
        <ListSection>
          <TopBar>
            <DateRangeGroup>
              <Label>时间范围</Label>
              <Input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
              <Label>至</Label>
              <Input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </DateRangeGroup>
            <SearchGroup>
              <Label>严重程度</Label>
              <StyledSelect
                value={severityFilter}
                onChange={(e) => handleSeverityFilter(e.target.value)}
              >
                <option value="all">全部</option>
                <option value="high">高危</option>
                <option value="medium">中危</option>
                <option value="low">低危</option>
              </StyledSelect>
              <SearchInput
                placeholder="请输入所属地或IP"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <SearchButton onClick={handleSearch}>
                <span>🔍</span>
                搜索
              </SearchButton>
            </SearchGroup>
          </TopBar>

          <TableContainer>
            <Table>
              <thead>
                <tr>
                  <Th>IP</Th>
                  <Th>所属地</Th>
                  <Th>异常时间</Th>
                  <Th>严重程度</Th>
                  <Th>异常信息</Th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <Tr>
                    <Td colSpan={5} style={{ textAlign: 'center', padding: '30px' }}>
                      加载中...
                    </Td>
                  </Tr>
                ) : error ? (
                  <Tr>
                    <Td colSpan={5} style={{ textAlign: 'center', padding: '30px', color: 'red' }}>
                      {error}
                    </Td>
                  </Tr>
                ) : currentReports.length > 0 ? (
                  currentReports.map(report => (
                    <Tr key={report.id}>
                      <Td>{report.ip}</Td>
                      <Td>{report.location}</Td>
                      <Td>{report.time}</Td>
                      <Td>
                        <SeverityIndicator level={report.severity}>
                          {report.severity === 'high' ? '高危' : 
                           report.severity === 'medium' ? '中危' : '低危'}
                        </SeverityIndicator>
                      </Td>
                      <Td>
                        <AnomalyBadge type={report.description}>
                          {report.description}
                        </AnomalyBadge>
                      </Td>
                    </Tr>
                  ))
                ) : (
                  <Tr>
                    <Td colSpan={5} style={{ textAlign: 'center', padding: '30px' }}>
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
        </ListSection>
      </ContentRow>
    </Container>
  );
};

export default ReportContent; 
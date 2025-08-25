import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import * as d3 from 'd3';

const ViewerContainer = styled.div`
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const ControlPanel = styled.div`
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
`;

const StatsPanel = styled.div`
  padding: 20px;
  background: linear-gradient(135deg, #1a237e05 0%, #1a237e10 100%);
  border-radius: 12px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  border: 1px solid rgba(26, 35, 126, 0.1);
`;

const StatBox = styled.div`
  text-align: center;
  padding: 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  }
  
  h3 {
    margin: 0;
    font-size: 15px;
    color: #666;
    font-weight: 500;
  }
  
  p {
    margin: 12px 0 0;
    font-size: 28px;
    font-weight: 600;
    color: #1a237e;
    
    &:after {
      content: '';
      display: block;
      width: 40px;
      height: 3px;
      background: #1a237e;
      margin: 8px auto 0;
      border-radius: 2px;
    }
  }
`;

const SessionSelect = styled.select`
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
  background: white;
  min-width: 400px;
  font-size: 14px;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #1a237e;
    box-shadow: 0 0 0 3px rgba(26, 35, 126, 0.1);
  }
  
  &:hover {
    border-color: #1a237e;
  }
  
  option {
    padding: 8px;
  }
`;

const Button = styled.button`
  padding: 12px 20px;
  border-radius: 8px;
  border: none;
  background: #1a237e;
  color: white;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(26, 35, 126, 0.2);
  
  &:hover {
    background: #0d1642;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26, 35, 126, 0.3);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  svg {
    width: 18px;
    height: 18px;
  }
  
  &:disabled {
    background: #bbc1e1;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const SessionInfo = styled.div`
  margin: 0;
  padding: 16px 20px;
  background: #e8eaf6;
  border-radius: 8px;
  font-size: 14px;
  color: #1a237e;
  display: flex;
  align-items: center;
  gap: 16px;
  border-left: 4px solid #1a237e;
  
  strong {
    font-weight: 600;
  }
  
  .info-item {
    display: flex;
    align-items: center;
    gap: 6px;
    
    &:not(:last-child):after {
      content: '•';
      margin-left: 16px;
      color: #1a237e;
      opacity: 0.5;
    }
  }
  
  .label {
    color: #3949ab;
    font-weight: 500;
  }
`;

const VisualizationContainer = styled.div`
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  border: 1px solid #e0e0e0;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);
  
  svg {
    width: 100%;
    height: 100%;
  }
`;

const Tooltip = styled.div`
  position: absolute;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  pointer-events: none;
  z-index: 100;
  max-width: 300px;
  opacity: 0;
  transition: all 0.2s ease;
  border: 1px solid rgba(26, 35, 126, 0.1);
  
  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    color: #1a237e;
    padding-bottom: 8px;
    border-bottom: 1px solid #e0e0e0;
  }
  
  p {
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.4;
  }
  
  .label {
    font-weight: 600;
    color: #666;
    margin-right: 6px;
  }
  
  .value {
    color: #333;
  }
`;

const Legend = styled.div`
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  border: 1px solid rgba(26, 35, 126, 0.1);
  
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: #1a237e;
    font-weight: 600;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    margin: 8px 0;
    font-size: 13px;
    
    &:hover {
      .color-box {
        transform: scale(1.2);
      }
    }
  }
  
  .color-box {
    width: 14px;
    height: 14px;
    margin-right: 8px;
    border-radius: 3px;
    transition: transform 0.2s ease;
  }
`;

const AsruexLogViewer = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalSessions: 0,
    uniqueIPs: 0,
    totalCommands: 0,
    activeConnections: 0
  });
  
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  
  // 获取命令的颜色和描述
  const getCommandInfo = (command, status) => {
    const commandMap = {
      'b2': {
        color: '#1a237e',
        description: '初始验证 - 蠕虫程序首次请求验证C2有效性'
      },
      'a0': {
        color: '#00796b',
        description: '文件操作请求'
      },
      'a1': {
        color: '#f57c00',
        description: '删除询问'
      },
      'a4': {
        color: '#d32f2f',
        description: 'POST文件上传'
      },
      'a5': {
        color: '#7b1fa2',
        description: '命令列表查询'
      },
      'a3': {
        color: '#0288d1',
        description: '文件列表查询'
      },
      'a7': {
        color: '#388e3c',
        description: '下载确认'
      },
      'a6': {
        color: '#689f38',
        description: '保存完成'
      },
      'a8': {
        color: '#f57c00',
        description: '删除询问'
      },
      'a9': {
        color: '#7b1fa2',
        description: '命令列表查询，准备下载'
      },
      'b0': {
        color: '#c2185b',
        description: '下载请求'
      },
      'b1': {
        color: '#00acc1',
        description: '操作确认'
      }
    };

    // 如果没有命令但有状态，使用状态的颜色和描述
    if (!command && status) {
      const statusMap = {
        'clean': { color: '#4caf50', description: '清理完成' },
        'clean1': { color: '#81c784', description: '清理阶段1' },
        'access': { color: '#2196f3', description: '访问请求' },
        'qla0': { color: '#ff9800', description: '查询操作' }
      };
      return statusMap[status] || { color: '#9e9e9e', description: status };
    }

    return commandMap[command] || { color: '#9e9e9e', description: '未知命令' };
  };

  // 将日志按IP和时间分组成会话
  const groupLogsIntoSessions = (logs) => {
    const sessions = [];
    const groupedByIP = {};
    const uniqueIPs = new Set();
    let totalCommands = 0;

    logs.forEach(log => {
      if (!groupedByIP[log.ip]) {
        groupedByIP[log.ip] = [];
        uniqueIPs.add(log.ip);
      }
      if (log.command) totalCommands++;
      groupedByIP[log.ip].push(log);
    });

    // 按时间顺序排序并分组成会话
    Object.entries(groupedByIP).forEach(([ip, ipLogs]) => {
      const sortedLogs = ipLogs.sort((a, b) => 
        new Date(a.log_time) - new Date(b.log_time)
      );

      let currentSession = [];
      sortedLogs.forEach(log => {
        if (log.command === 'b2' || currentSession.length === 0) {
          if (currentSession.length > 0) {
            sessions.push(currentSession);
          }
          currentSession = [log];
        } else {
          currentSession.push(log);
          if (log.status === 'clean') {
            sessions.push(currentSession);
            currentSession = [];
          }
        }
      });
      if (currentSession.length > 0) {
        sessions.push(currentSession);
      }
    });

    // 更新统计信息
    setStats({
      totalSessions: sessions.length,
      uniqueIPs: uniqueIPs.size,
      totalCommands,
      activeConnections: Object.keys(groupedByIP).length
    });

    return sessions;
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  // 获取所有会话
  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/asruex/logs');
      const data = await response.json();
      
      const groupedSessions = groupLogsIntoSessions(data);
      setSessions(groupedSessions);
      setLoading(false);
    } catch (error) {
      console.error('获取会话列表失败', error);
      setLoading(false);
    }
  };

  const handleSessionSelect = (e) => {
    const sessionIndex = parseInt(e.target.value);
    if (!isNaN(sessionIndex)) {
      setSelectedSession(sessions[sessionIndex]);
      renderVisualization(sessions[sessionIndex]);
    }
  };

  // 渲染交互可视化
  const renderVisualization = (sessionData) => {
    if (!svgRef.current || !sessionData || sessionData.length === 0) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    const margin = { top: 50, right: 50, bottom: 50, left: 50 };
    
    // 创建时间轴
    const timeExtent = d3.extent(sessionData, d => new Date(d.log_time));
    const timeScale = d3.scaleTime()
      .domain(timeExtent)
      .range([margin.left, width - margin.right]);
    
    // 创建节点和连线
    const nodes = sessionData.map((log, i) => ({
      id: i,
      log: log,
      x: timeScale(new Date(log.log_time)),
      y: height / 2
    }));
    
    const links = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      links.push({
        source: nodes[i],
        target: nodes[i + 1]
      });
    }
    
    // 绘制时间轴
    const timeAxis = d3.axisBottom(timeScale)
      .ticks(10)
      .tickFormat(d3.timeFormat("%H:%M:%S"));
    
    svg.append("g")
      .attr("transform", `translate(0, ${height - margin.bottom})`)
      .call(timeAxis)
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em");
    
    // 绘制连线
    svg.selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y)
      .attr("stroke", "#999")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "5,5");
    
    // 绘制节点
    const nodeElements = svg.selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
      .attr("r", 8)
      .attr("fill", d => {
        const { color } = getCommandInfo(d.log.command, d.log.status);
        return color;
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer");
    
    // 添加悬停效果和工具提示
    const tooltip = d3.select(tooltipRef.current);
    
    nodeElements
      .on("mouseover", (event, d) => {
        const { color, description } = getCommandInfo(d.log.command, d.log.status);
        
        tooltip
          .style("opacity", 1)
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 10}px`)
          .html(`
            <h4>${d.log.command ? `命令: ${d.log.command}` : `状态: ${d.log.status}`}</h4>
            <p><span class="label">时间:</span> <span class="value">${d.log.log_time}</span></p>
            <p><span class="label">IP:</span> <span class="value">${d.log.ip}</span></p>
            <p><span class="label">描述:</span> <span class="value">${d.log.description || description}</span></p>
          `);
        
        d3.select(event.target)
          .attr("r", 12)
          .attr("stroke-width", 3);
      })
      .on("mouseout", (event) => {
        tooltip
          .style("opacity", 0);
        
        d3.select(event.target)
          .attr("r", 8)
          .attr("stroke-width", 2);
      });
    
    // 添加图例
    const legend = svg.append("g")
      .attr("transform", `translate(${width - margin.right - 150}, ${margin.top})`);
    
    const commandTypes = [
      { command: 'b2', status: '' },
      { command: 'a9', status: '' },
      { command: 'b0', status: '' },
      { command: '', status: 'access' },
      { command: '', status: 'clean' }
    ];
    
    commandTypes.forEach((item, i) => {
      const { color, description } = getCommandInfo(item.command, item.status);
      const legendRow = legend.append("g")
        .attr("transform", `translate(0, ${i * 20})`);
      
      legendRow.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", 6)
        .attr("fill", color);
      
      legendRow.append("text")
        .attr("x", 15)
        .attr("y", 4)
        .text(item.command ? `${item.command}: ${description.substring(0, 15)}...` : `${item.status}: ${description.substring(0, 15)}...`)
        .style("font-size", "12px");
    });
    
    // 添加交互流程图
    const flowHeight = 100;
    const flowY = height - margin.bottom - flowHeight;
    
    // 创建流程阶段
    const stages = [
      { name: "初始验证", color: "#1a237e" },
      { name: "命令查询", color: "#7b1fa2" },
      { name: "文件操作", color: "#00796b" },
      { name: "下载执行", color: "#c2185b" },
      { name: "清理", color: "#4caf50" }
    ];
    
    const stageWidth = (width - margin.left - margin.right) / stages.length;
    
    // 绘制流程阶段背景
    svg.selectAll(".stage-bg")
      .data(stages)
      .enter()
      .append("rect")
      .attr("x", (d, i) => margin.left + i * stageWidth)
      .attr("y", flowY)
      .attr("width", stageWidth)
      .attr("height", flowHeight)
      .attr("fill", d => `${d.color}20`)
      .attr("stroke", d => d.color)
      .attr("stroke-width", 1)
      .attr("rx", 4);
    
    // 绘制流程阶段标签
    svg.selectAll(".stage-label")
      .data(stages)
      .enter()
      .append("text")
      .attr("x", (d, i) => margin.left + i * stageWidth + stageWidth / 2)
      .attr("y", flowY - 10)
      .attr("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .style("fill", d => d.color)
      .text(d => d.name);
    
    // 将节点映射到流程阶段
    const getStageIndex = (log) => {
      if (log.command === 'b2') return 0;
      if (['a5', 'a9'].includes(log.command)) return 1;
      if (['a0', 'a1', 'a3', 'a4', 'a6', 'a7', 'a8'].includes(log.command)) return 2;
      if (['b0', 'b1'].includes(log.command)) return 3;
      if (['clean', 'clean1'].includes(log.status)) return 4;
      return 2; // 默认放在中间
    };
    
    // 绘制流程点
    svg.selectAll(".flow-node")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("cx", d => d.x)
      .attr("cy", d => flowY + flowHeight / 2)
      .attr("r", 5)
      .attr("fill", d => {
        const { color } = getCommandInfo(d.log.command, d.log.status);
        return color;
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1);
    
    // 绘制从主节点到流程点的连线
    svg.selectAll(".node-to-flow")
      .data(nodes)
      .enter()
      .append("line")
      .attr("x1", d => d.x)
      .attr("y1", d => d.y)
      .attr("x2", d => d.x)
      .attr("y2", d => flowY + flowHeight / 2)
      .attr("stroke", d => {
        const { color } = getCommandInfo(d.log.command, d.log.status);
        return color;
      })
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "3,3");
  };

  useEffect(() => {
    const handleResize = () => {
      if (selectedSession) {
        renderVisualization(selectedSession);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [selectedSession]);

  return (
    <ViewerContainer>
      <StatsPanel>
        <StatBox>
          <h3>总会话数</h3>
          <p>{stats.totalSessions}</p>
        </StatBox>
        <StatBox>
          <h3>独立IP数</h3>
          <p>{stats.uniqueIPs}</p>
        </StatBox>
        <StatBox>
          <h3>命令总数</h3>
          <p>{stats.totalCommands}</p>
        </StatBox>
        <StatBox>
          <h3>活跃连接</h3>
          <p>{stats.activeConnections}</p>
        </StatBox>
      </StatsPanel>

      <ControlPanel>
        <SessionSelect
          onChange={handleSessionSelect}
          disabled={loading}
        >
          <option value="">选择要查看的会话</option>
          {sessions.map((session, index) => {
            const startTime = new Date(session[0].log_time).toLocaleString();
            const endTime = new Date(session[session.length - 1].log_time).toLocaleString();
            return (
              <option key={index} value={index}>
                {`${session[0].ip} - ${startTime} 到 ${endTime} (${session.length}步操作)`}
              </option>
            );
          })}
        </SessionSelect>
        <Button onClick={fetchSessions} disabled={loading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          {loading ? '加载中...' : '刷新会话列表'}
        </Button>
      </ControlPanel>

      {selectedSession && (
        <SessionInfo>
          <div className="info-item">
            <span className="label">IP:</span>
            {selectedSession[0].ip}
          </div>
          <div className="info-item">
            <span className="label">开始时间:</span>
            {new Date(selectedSession[0].log_time).toLocaleString()}
          </div>
          <div className="info-item">
            <span className="label">结束时间:</span>
            {new Date(selectedSession[selectedSession.length - 1].log_time).toLocaleString()}
          </div>
          <div className="info-item">
            <span className="label">操作数:</span>
            {selectedSession.length}
          </div>
        </SessionInfo>
      )}

      <VisualizationContainer>
        <svg ref={svgRef}></svg>
        <Tooltip ref={tooltipRef}></Tooltip>
      </VisualizationContainer>
    </ViewerContainer>
  );
};

export default AsruexLogViewer;
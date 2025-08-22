import React, { useState } from 'react';
import styled from 'styled-components';

// 扩展与应用组件
const ExtensionContent = () => {
  const [activeTab, setActiveTab] = useState('tools');
  
  // 样式定义
  const Container = styled.div`
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    padding: 0px;
    box-sizing: border-box;
    position: relative;
  `;
  
  const TabsContainer = styled.div`
    display: flex;
    border-bottom: 2px solid #e0e0e0;
    margin-bottom: 20px;
    background: #f9f9f9;
    border-radius: 8px 8px 0 0;
    padding: 0 10px;
    flex-shrink: 0;
  `;
  
  const Tab = styled.div`
    padding: 16px 24px;
    cursor: pointer;
    font-weight: ${props => props.active ? '600' : '400'};
    color: ${props => props.active ? '#1a237e' : '#757575'};
    border-bottom: 3px solid ${props => props.active ? '#1a237e' : 'transparent'};
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    
    &:hover {
      color: #1a237e;
      background-color: ${props => props.active ? 'transparent' : 'rgba(26, 35, 126, 0.05)'};
    }
  `;
  
  const ContentContainer = styled.div`
    flex: 1;
    overflow-y: auto;
    padding: 0 20px 20px;
    scroll-behavior: smooth;
  `;
  
  const Grid = styled.div`
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 25px;
    margin-bottom: 30px;
  `;
  
  const Card = styled.div`
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    padding: 25px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    border: 1px solid #f0f0f0;
    position: relative;
    overflow: hidden;
    
    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
      border-color: #e0e0e0;
    }
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 4px;
      background: ${props => props.accentColor || '#1a237e'};
      transform: scaleX(0);
      transform-origin: 0 0;
      transition: transform 0.3s ease;
    }
    
    &:hover::after {
      transform: scaleX(1);
    }
  `;
  
  const CardHeader = styled.div`
    display: flex;
    align-items: center;
    margin-bottom: 18px;
  `;
  
  const IconContainer = styled.div`
    width: 56px;
    height: 56px;
    border-radius: 16px;
    background: ${props => props.color || '#e3f2fd'};
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin-right: 18px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    
    ${Card}:hover & {
      transform: scale(1.05);
    }
  `;
  
  const CardTitle = styled.h3`
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
  `;
  
  const CardDescription = styled.p`
    margin: 0;
    color: #666;
    font-size: 15px;
    line-height: 1.6;
  `;
  
  const Button = styled.button`
    background: ${props => props.secondary ? 'transparent' : '#1a237e'};
    color: ${props => props.secondary ? '#1a237e' : 'white'};
    border: ${props => props.secondary ? '1px solid #1a237e' : 'none'};
    padding: 10px 18px;
    border-radius: 8px;
    margin-top: 18px;
    cursor: pointer;
    font-weight: 500;
    font-size: 15px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    
    &:hover {
      background: ${props => props.secondary ? 'rgba(26, 35, 126, 0.1)' : '#0d1642'};
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    &:active {
      transform: translateY(0);
      box-shadow: none;
    }
  `;
  
  const SectionTitle = styled.h2`
    margin-top: 10px;
    margin-bottom: 25px;
    color: #333;
    font-weight: 600;
    font-size: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
    
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: #e0e0e0;
      margin-left: 15px;
    }
  `;
  
  const FormGroup = styled.div`
    margin-bottom: 20px;
  `;
  
  const Label = styled.label`
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #333;
  `;
  
  const Input = styled.input`
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #ddd;
    font-size: 15px;
    transition: all 0.2s ease;
    
    &:focus {
      border-color: #1a237e;
      outline: none;
      box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
    }
  `;
  
  const CheckboxContainer = styled.div`
    display: flex;
    align-items: center;
    margin-bottom: 12px;
  `;
  
  const CustomCheckbox = styled.div`
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid ${props => props.checked ? '#1a237e' : '#aaa'};
    background: ${props => props.checked ? '#1a237e' : 'transparent'};
    margin-right: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    cursor: pointer;
    
    &::after {
      content: '✓';
      color: white;
      font-size: 14px;
      opacity: ${props => props.checked ? 1 : 0};
    }
    
    &:hover {
      border-color: #1a237e;
    }
  `;
  
  const SettingsCard = styled.div`
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    padding: 25px;
    margin-bottom: 25px;
    border: 1px solid #f0f0f0;
  `;
  
  const SettingsCardTitle = styled.h3`
    margin-top: 0;
    margin-bottom: 20px;
    color: #333;
    font-weight: 600;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f0;
  `;
  
  const Badge = styled.span`
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    background-color: #e3f2fd;
    color: #1a237e;
    margin-left: 10px;
  `;

  // 工具和插件数据
  const tools = [
    {
      icon: '🔍',
      color: '#e3f2fd',
      title: '僵尸网络节点搜索',
      description: '基于机器学习的节点识别系统，支持IP信誉度评分、域名威胁等级分析、C&C服务器特征匹配。可通过网络行为特征、通信模式快速定位僵尸网络节点。',
      action: '可扩展应用',
      accentColor: '#1565c0'
    },
    {
      icon: '📊',
      color: '#e8f5e9',
      title: '传播路径分析',
      description: '基于Neo4j的僵尸网络拓扑分析，实时展示感染传播链、节点控制关系、通信网络。支持模拟清除策略，预测网络瓦解效果。',
      action: '可扩展应用',
      accentColor: '#2e7d32'
    },
    {
      icon: '🔔',
      color: '#fff3e0',
      title: '自动化清除',
      description: '集成多源威胁情报，支持自动化清除模板配置。可联动防火墙、EDR等安全设备，一键下发清除指令，实现批量僵尸网络节点处置。',
      action: '可扩展应用',
      accentColor: '#f57c00'
    },
    {
      icon: '📝',
      color: '#f1f8e9',
      title: '取证与溯源',
      description: '自动收集僵尸网络样本、通信日志、行为特征。支持样本反编译分析、加密流量解析，协助确定攻击来源与技术特征。',
      action: '可扩展应用',
      accentColor: '#558b2f'
    },
    {
      icon: '🛡️',
      color: '#ede7f6',
      title: '防火墙联动',
      description: '支持对接主流防火墙产品，自动下发阻断策略，切断僵尸网络通信。',
      action: '可扩展应用',
      accentColor: '#5e35b1'
    },
    {
      icon: '🌐',
      color: '#e1f5fe',
      title: 'DNS清除',
      description: '对接DNS服务器，自动封禁僵尸网络域名，阻断僵尸网络控制通道。',
      action: '可扩展应用',
      accentColor: '#0288d1'
    },
    {
      icon: '🔒',
      color: '#fce4ec',
      title: 'EDR联动',
      description: '集成主流EDR产品，实现终端僵尸网络进程查杀、文件清理、注册表清理等。',
      action: '可扩展应用',
      accentColor: '#d81b60'
    },
    {
      icon: '📡',
      color: '#fff3e0',
      title: '蜜罐诱捕',
      description: '部署专用蜜罐节点，诱捕僵尸网络攻击，获取最新变种样本与攻击特征。',
      action: '可扩展应用',
      accentColor: '#f57c00'
    }
  ];

  
  // 自定义复选框组件
  const Checkbox = ({ id, label, defaultChecked }) => {
    const [checked, setChecked] = useState(defaultChecked);
    
    return (
      <CheckboxContainer>
        <input 
          type="checkbox" 
          id={id} 
          checked={checked}
          onChange={() => setChecked(!checked)}
          style={{ display: 'none' }}
        />
        <CustomCheckbox 
          checked={checked} 
          onClick={() => setChecked(!checked)}
        />
        <label htmlFor={id}>{label}</label>
      </CheckboxContainer>
    );
  };
  
  return (
    <Container>
      <ContentContainer>
        <SectionTitle>🧰 功能扩展</SectionTitle>
        <Grid>
          {tools.map((tool, index) => (
            <Card key={index} accentColor={tool.accentColor}>
              <CardHeader>
                <IconContainer color={tool.color}>
                  {tool.icon}
                </IconContainer>
                <CardTitle>{tool.title}</CardTitle>
              </CardHeader>
              <CardDescription>{tool.description}</CardDescription>
              <Button>
                {tool.action}
              </Button>
            </Card>
          ))}
        </Grid>
      </ContentContainer>
    </Container>
  );
};

export default ExtensionContent; 
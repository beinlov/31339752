import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { withRouter } from 'dva/router';
import { Select } from 'antd';
import NodeManagement from './NodeManagement';
import LogContent from './LogContent';
import UserContent from './UserContent';
import ReportContent from './ReportContent';
import ExtensionContent from './ExtensionContent';
import BotnetRegistration from './BotnetRegistration';
import NodeDistribution from './NodeDistribution';
import ServerManagement from './ServerManagement';
import SuppressionStrategy from './SuppressionStrategy';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const { Option } = Select;

// 样式定义
const AdminContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(135deg, #0a1628 0%, #1a2332 50%, #0d1b2a 100%);
`;

const Header = styled.div`
  width: 100%;
  height: 64px;
  background: linear-gradient(90deg, #0a1f3d 0%, #0d2847 50%, #0f3057 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 2%;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 0 15px rgba(15, 48, 87, 0.3);
  border-bottom: 2px solid rgba(30, 70, 120, 0.4);
`;

const HeaderTitle = styled.div`
  font-size: 2em;
  font-weight: bold;
  flex: 1;
  background: linear-gradient(90deg, #ffffff 0%, #64b5f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 30px rgba(100, 181, 246, 0.5);
  letter-spacing: 2px;
`;

const NetworkSelect = styled(Select)`
  width: 220px;
  margin-right: 20px;
  color: white;

  .ant-select-selector {
    background: rgba(26, 115, 232, 0.2) !important;
    border: 1px solid rgba(100, 181, 246, 0.6) !important;
    border-radius: 6px !important;
    box-shadow: 0 0 10px rgba(26, 115, 232, 0.3);
    height: 40px !important;
    display: flex;
    align-items: center;
  }

  .ant-select-selection-item {
    color: white !important;
    font-size: 14px;
  }

  .ant-select-arrow {
    color: #64b5f6 !important;
  }

  .ant-select-dropdown {
    background: rgba(13, 39, 92, 0.95);
    border: 1px solid rgba(100, 181, 246, 0.6);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  }

  .ant-select-item {
    color: white;
  }

  .ant-select-item-option-active,
  .ant-select-item-option-selected {
    background: rgba(100, 181, 246, 0.25) !important;
  }
`;

const HeaderButton = styled.button`
  padding: 8px 16px;
  margin-left: 10px;
  background: rgba(26, 115, 232, 0.2);
  border: 1px solid rgba(100, 181, 246, 0.5);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(26, 115, 232, 0.3);
  transition: all 0.3s ease;
  font-weight: 500;
  letter-spacing: 0.5px;

  &:hover {
    background: rgba(26, 115, 232, 0.4);
    border-color: rgba(100, 181, 246, 0.8);
    box-shadow: 0 0 15px rgba(26, 115, 232, 0.5);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
`;

const LogoutButton = styled(HeaderButton)`
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.6);

  &:hover {
    background: rgba(244, 67, 54, 0.3);
    border-color: rgba(244, 67, 54, 0.9);
    box-shadow: 0 0 15px rgba(244, 67, 54, 0.4);
  }
`;

const MainContent = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
  height: calc(100vh - 64px);
`;

const Sidebar = styled.div`
  width: 240px;
  background: linear-gradient(180deg, #0a1929 0%, #0d1f2d 100%);
  padding: 20px 0;
  border-right: 1px solid rgba(30, 70, 120, 0.3);
  box-shadow: 2px 0 15px rgba(0, 0, 0, 0.4), inset -1px 0 0 rgba(30, 70, 120, 0.2);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.3s ease;
  flex-shrink: 0;
  overflow-y: auto;
`;

const SidebarItem = styled.div`
  padding: 14px 24px;
  margin: 0 12px;
  cursor: pointer;
  background: ${props => props.active ? 'linear-gradient(90deg, #0f3057, rgba(15, 48, 87, 0.9))' : 'transparent'};
  color: ${props => props.active ? '#ffffff' : '#7a9cc6'};
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 1px solid ${props => props.active ? 'rgba(30, 70, 120, 0.4)' : 'transparent'};
  box-shadow: ${props => props.active ? '0 0 15px rgba(15, 48, 87, 0.4)' : 'none'};

  &:hover {
    background: ${props => props.active ? 'linear-gradient(90deg, #0f3057, rgba(15, 48, 87, 0.9))' : 'rgba(15, 48, 87, 0.2)'};
    color: ${props => props.active ? '#ffffff' : '#5a8fc4'};
    transform: translateX(4px);
    border-color: rgba(30, 70, 120, 0.4);
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 0;
    background: linear-gradient(180deg, #1e4678, #2d5a8f);
    border-radius: 0 2px 2px 0;
    transition: height 0.2s ease;
    box-shadow: 0 0 10px rgba(30, 70, 120, 0.5);
  }

  &:hover::before {
    height: ${props => props.active ? '0' : '70%'};
  }

  .icon {
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: ${props => props.active ? '#ffffff' : '#5a8fc4'};
    transition: all 0.3s ease;
    filter: ${props => props.active ? 'drop-shadow(0 0 5px rgba(90, 143, 196, 0.5))' : 'none'};
  }

  &:hover .icon {
    transform: scale(1.1);
    filter: drop-shadow(0 0 8px rgba(90, 143, 196, 0.6));
  }
`;

const SidebarDivider = styled.div`
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(30, 70, 120, 0.4), transparent);
  margin: 8px 24px;
  box-shadow: 0 0 5px rgba(30, 70, 120, 0.3);
`;

const SidebarGroupHeader = styled.button`
  padding: 14px 24px 10px;
  font-size: 16px;
  font-weight: 600;
  color: #9fd3ff;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  opacity: 0.95;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: color 0.2s ease;
  text-shadow: 0 2px 12px rgba(100, 181, 246, 0.35);

  span:first-child {
    background: linear-gradient(90deg, #69b7ff, #8f8cff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  &:hover {
    color: #8fb7e4;
  }

  .chevron {
    transform: rotate(${props => (props.open ? '0deg' : '-90deg')});
    transition: transform 0.2s ease;
  }
`;

const Content = styled.div`
  flex: 1;
  padding: 20px;
  background: linear-gradient(135deg, #0f1923 0%, #1a2838 100%);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
`;

// 教学引导样式
const TutorialOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: ${props => props.show ? 'block' : 'none'};
  pointer-events: none;
`;

const TutorialHighlight = styled.div`
  position: absolute;
  border: 2px solid #1a73e8;
  border-radius: 4px;
  z-index: 1001;
  transition: all 0.3s ease;
  pointer-events: none;
  box-shadow: 0 0 20px rgba(26, 115, 232, 0.5);
`;

const TutorialTooltip = styled.div`
  position: absolute;
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 1002;
  max-width: 300px;
  transition: all 0.3s ease;
  pointer-events: all;

  &:after {
    content: '';
    position: absolute;
    border: 8px solid transparent;
    ${props => {
      switch(props.position) {
        case 'bottom':
          return `
            top: -16px;
            left: 20px;
            border-bottom-color: white;
          `;
        case 'top':
          return `
            bottom: -16px;
            left: 20px;
            border-top-color: white;
          `;
        case 'left':
          return `
            right: -16px;
            top: 20px;
            border-left-color: white;
          `;
        case 'right':
          return `
            left: -16px;
            top: 20px;
            border-right-color: white;
          `;
        default:
          return '';
      }
    }}
  }
`;

const TutorialButton = styled.button`
  background: linear-gradient(90deg, #1565c0, #1a73e8);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  margin-top: 10px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(26, 115, 232, 0.3);
  transition: all 0.3s ease;
  font-weight: 500;

  &:hover {
    background: linear-gradient(90deg, #0d47a1, #1565c0);
    box-shadow: 0 0 15px rgba(26, 115, 232, 0.5);
    transform: translateY(-1px);
  }
`;

const AdminPage = ({ history }) => {
  const [activeMenu, setActiveMenu] = useState('clear');
  const [selectedNetwork, setSelectedNetwork] = useState('utg-q-008');
  const [currentContent, setCurrentContent] = useState(<NodeManagement networkType="utg-q-008" />);
  const [showTutorial, setShowTutorial] = useState(false);
  const [tutorialStep, setTutorialStep] = useState(0);
  const [networkTypes, setNetworkTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openGroups, setOpenGroups] = useState({
    '僵尸网络管理': true,
    '系统管理': true
  });

  useEffect(() => {
    fetchNetworkTypes();
  }, []);

  // 检查是否有初始菜单参数（用于免登录接口直接跳转到指定功能）
  useEffect(() => {
    const initialMenu = localStorage.getItem('initialMenu');
    if (initialMenu) {
      console.log('Detected initial menu parameter:', initialMenu);
      // 延迟执行以确保组件已完全加载
      setTimeout(() => {
        handleMenuClick(initialMenu);
        // 清除已使用的参数
        localStorage.removeItem('initialMenu');
      }, 100);
    }
  }, [networkTypes]); // 依赖 networkTypes 确保数据已加载

  const fetchNetworkTypes = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/botnet-types'));
      if (response.data.status === 'success') {
        setNetworkTypes(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching network types:', error);
    } finally {
      setLoading(false);
    }
    handleNetChange("ramnit")
  };

  const getMenuGroups = (networkId) => {
    const botnetItems = [
      {
        id: 'clear',
        name: '受控节点监控',
        component: NodeManagement,
        icon: '&#xe88f;'
      },
      {
        id: 'node_distribution',
        name: '受控节点分布情况',
        component: NodeDistribution,
        icon: '📍'
      },
      {
        id: 'suppression',
        name: '抑制阻断策略',
        component: SuppressionStrategy,
        icon: '🛡️'
      },
      {
        id: 'report',
        name: '节点失控日志',
        component: ReportContent,
        icon: '&#xe86e;'
      },
      {
        id: 'register_botnet',
        name: '僵尸网络添加',
        component: BotnetRegistration,
        icon: '✚'
      },
      {
        id: 'server',
        name: 'C2状态监控',
        component: ServerManagement,
        icon: '💻'
      }
    ];

    const systemItems = [
      {
        id: 'user',
        name: '用户管理',
        component: UserContent,
        icon: '&#xe7fb;'
      },
      {
        id: 'log',
        name: '操作日志',
        component: LogContent,
        icon: '&#xe777;'
      }
    ];

    return [
      { title: '僵尸网络管理', items: botnetItems },
      { title: '系统管理', items: systemItems }
    ];
  };

  const getAllMenuItems = (networkId) =>
    getMenuGroups(networkId).flatMap(group => group.items);

  const handleMenuClick = (menuId) => {
    setActiveMenu(menuId);
    const menuItems = getAllMenuItems(selectedNetwork);
    const selectedItem = menuItems.find(item => item.id === menuId);
    if (selectedItem) {
      if (menuId === 'clear') {
        setCurrentContent(
          <selectedItem.component
            networkType={selectedNetwork}
          />
        );
      } else if (menuId === 'node_distribution') {
        setCurrentContent(
          <selectedItem.component
            networkType={selectedNetwork}
          />
        );
      } else if (menuId === 'register_botnet') {
        setCurrentContent(<selectedItem.component />);
      } else {
        setCurrentContent(<selectedItem.component />);
      }
    }
  };


  const handleNetworkChange = (value) => {
    const newNetwork = value;
    setSelectedNetwork(newNetwork);
    // 保存选择的网络到localStorage
    localStorage.setItem('selectedNetwork', newNetwork);

    // 无论当前在哪个菜单，都重新渲染当前内容组件
    const menuItems = getAllMenuItems(newNetwork);
    const selectedItem = menuItems.find(item => item.id === activeMenu);
    if (selectedItem) {
      setCurrentContent(
        <selectedItem.component
          networkType={newNetwork}
          key={newNetwork} // 添加 key 属性，强制组件重新渲染
        />
      );
    }
  };

  const handleCommandCenterClick = () => {
    // 跳转到指挥中心页面
    history.push('/index');
  };

  const handleLogout = () => {
    // 这里可以添加登出相关逻辑，比如清除本地存储的token等
    history.push('/login');
  };

  // 教学步骤定义
  const tutorialSteps = [
    {
      target: 'select.network-select',
      title: '第一步：选择僵尸网络',
      content: '在这里选择要管理的僵尸网络类型。不同的僵尸网络可能有不同的功能选项。',
      position: 'bottom',
      offset: { x: 0, y: 10 }
    },
    {
      target: 'div.sidebar',
      title: '第二步：功能菜单',
      content: '这里是主要功能区，包括清除/抑制阻断、操作日志、异常报告等功能。点击可以切换不同的功能页面。',
      position: 'right',
      offset: { x: 10, y: 0 }
    },
    {
      target: 'div.content',
      title: '第三步：操作区域',
      content: '这里是主要的操作区域，会根据左侧选择的功能显示对应的内容和操作界面。',
      position: 'left',
      offset: { x: -10, y: 0 }
    },
    {
      target: 'button.command-center',
      title: '第四步：僵尸网络展示处置平台',
      content: '点击这里可以切换到僵尸网络展示处置平台视图，查看更多可视化数据和整体状况。',
      position: 'bottom',
      offset: { x: 0, y: 10 }
    }
  ];

  const startTutorial = () => {
    setShowTutorial(true);
    setTutorialStep(0);
  };

  const nextTutorialStep = () => {
    if (tutorialStep < tutorialSteps.length - 1) {
      setTutorialStep(tutorialStep + 1);
    } else {
      setShowTutorial(false);
    }
  };

  return (
    <AdminContainer>
      <Header>
        <HeaderTitle>僵尸网络接管与清除后台管理系统</HeaderTitle>
        <NetworkSelect
          className="network-select"
          value={selectedNetwork || undefined}
          onChange={handleNetworkChange}
          disabled={loading}
          placeholder="请选择僵尸网络"
          listHeight={240} // 显示约6个选项（每项约40px）
          dropdownStyle={{ maxHeight: 240, overflowY: 'auto' }}
        >
          <Option key="placeholder" value="">
            请选择僵尸网络
          </Option>
          {networkTypes.map(network => (
            <Option key={network.name} value={network.name}>
              {network.display_name}
            </Option>
          ))}
        </NetworkSelect>
        <HeaderButton onClick={startTutorial}>帮助</HeaderButton>
        <HeaderButton className="command-center" onClick={handleCommandCenterClick}>
          僵尸网络展示处置平台
        </HeaderButton>
        <LogoutButton onClick={handleLogout}>退出登录</LogoutButton>
      </Header>
      <MainContent>
        <Sidebar className="sidebar">
          {getMenuGroups(selectedNetwork).map((group, groupIndex) => (
            <React.Fragment key={group.title}>
              <SidebarGroupHeader
                type="button"
                open={openGroups[group.title]}
                onClick={() =>
                  setOpenGroups(prev => ({
                    ...prev,
                    [group.title]: !prev[group.title]
                  }))
                }
              >
                <span>{group.title}</span>
                <span className="chevron">⌄</span>
              </SidebarGroupHeader>
              {openGroups[group.title] &&
                group.items.map(item => (
                  <SidebarItem
                    key={item.id}
                    active={activeMenu === item.id}
                    onClick={() => handleMenuClick(item.id)}
                  >
                    {item.icon.startsWith('&') ? (
                      <span className="icon iconfont" dangerouslySetInnerHTML={{ __html: item.icon }} />
                    ) : (
                      <span className="icon">{item.icon}</span>
                    )}
                    <span>{item.name}</span>
                  </SidebarItem>
                ))}
              {groupIndex !== getMenuGroups(selectedNetwork).length - 1 && <SidebarDivider />}
            </React.Fragment>
          ))}
        </Sidebar>
        <Content className="content">
          {currentContent}
        </Content>
      </MainContent>

      {showTutorial && (
        <>
          <TutorialOverlay show={showTutorial}>
            <svg
              width="100%"
              height="100%"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
              }}
            >
              <defs>
                <mask id="spotlight">
                  <rect width="100%" height="100%" fill="white" />
                  {(() => {
                    if (tutorialSteps[tutorialStep].target) {
                      const pos = getTutorialHighlightPosition(tutorialSteps[tutorialStep].target);
                      return (
                        <rect
                          x={pos.left}
                          y={pos.top}
                          width={pos.width}
                          height={pos.height}
                          fill="black"
                        />
                      );
                    }
                    return null;
                  })()}
                </mask>
              </defs>
              <rect
                width="100%"
                height="100%"
                fill="rgba(0, 0, 0, 0.7)"
                mask="url(#spotlight)"
              />
            </svg>
          </TutorialOverlay>
          <TutorialHighlight
            style={{
              ...getTutorialHighlightPosition(tutorialSteps[tutorialStep].target)
            }}
          />
          <TutorialTooltip
            style={{
              ...getTutorialTooltipPosition(
                tutorialSteps[tutorialStep].target,
                tutorialSteps[tutorialStep].position,
                tutorialSteps[tutorialStep].offset
              )
            }}
            position={tutorialSteps[tutorialStep].position}
          >
            <h3 style={{ margin: '0 0 10px 0', color: '#1a73e8' }}>
              {tutorialSteps[tutorialStep].title}
            </h3>
            <p style={{ margin: '0 0 15px 0', lineHeight: '1.5' }}>
              {tutorialSteps[tutorialStep].content}
            </p>
            <TutorialButton onClick={nextTutorialStep}>
              {tutorialStep === tutorialSteps.length - 1 ? '完成教学' : '下一步'}
            </TutorialButton>
          </TutorialTooltip>
        </>
      )}
    </AdminContainer>
  );
};

// 获取目标元素位置
const getTutorialHighlightPosition = (selector) => {
  const element = document.querySelector(selector);
  if (!element) {
    console.error(`Tutorial target element not found: ${selector}`);
    return { top: 0, left: 0, width: 0, height: 0 };
  }
  const rect = element.getBoundingClientRect();
  console.log(`Tutorial highlight position for ${selector}:`, rect);
  return {
    top: rect.top - 2,
    left: rect.left - 2,
    width: rect.width + 4,
    height: rect.height + 4
  };
};

// 获取提示框位置
const getTutorialTooltipPosition = (selector, position, offset = { x: 0, y: 0 }) => {
  const element = document.querySelector(selector);
  if (!element) return {};
  const rect = element.getBoundingClientRect();

  switch(position) {
    case 'bottom':
      return {
        top: rect.bottom + offset.y,
        left: rect.left + offset.x
      };
    case 'top':
      return {
        bottom: window.innerHeight - rect.top + offset.y,
        left: rect.left + offset.x
      };
    case 'left':
      return {
        top: rect.top + offset.y,
        right: window.innerWidth - rect.left + offset.x
      };
    case 'right':
      return {
        top: rect.top + offset.y,
        left: rect.right + offset.x
      };
    default:
      return {
        top: rect.bottom + offset.y,
        left: rect.left + offset.x
      };
  }
};

export default withRouter(AdminPage);

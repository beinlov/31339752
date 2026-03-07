import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

// Modal 遮罩层
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 15000;
  animation: fadeIn 0.3s ease;

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
`;

// Modal 容器
const ModalContainer = styled.div`
  background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
  border-radius: 16px;
  width: 90%;
  max-width: 1000px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(26, 115, 232, 0.3), 
              0 0 0 1px rgba(100, 181, 246, 0.2);
  animation: slideUp 0.3s ease;
  overflow: hidden;

  @keyframes slideUp {
    from {
      transform: translateY(30px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
`;

// Modal 头部
const ModalHeader = styled.div`
  padding: 24px 30px;
  border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, rgba(26, 115, 232, 0.1) 0%, rgba(26, 115, 232, 0.05) 100%);
`;

const ModalTitle = styled.h2`
  margin: 0;
  color: #64b5f6;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;

  .icon {
    font-size: 24px;
  }

  .count-badge {
    background: rgba(76, 175, 80, 0.2);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 14px;
    color: #81c784;
    border: 1px solid rgba(76, 175, 80, 0.3);
    font-weight: 500;
  }

  .warning-badge {
    background: rgba(255, 152, 0, 0.2);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 14px;
    color: #ffb74d;
    border: 1px solid rgba(255, 152, 0, 0.3);
    font-weight: 500;
  }
`;

const CloseButton = styled.button`
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #ef5350;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: rgba(244, 67, 54, 0.2);
    border-color: #ef5350;
    transform: scale(1.05);
  }
`;

// Modal 内容区域
const ModalContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px 30px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(10, 25, 41, 0.3);
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(100, 181, 246, 0.3);
    border-radius: 4px;

    &:hover {
      background: rgba(100, 181, 246, 0.5);
    }
  }
`;

// 僵网卡片
const BotnetCard = styled.div`
  background: linear-gradient(135deg, rgba(26, 115, 232, 0.08) 0%, rgba(26, 115, 232, 0.03) 100%);
  border: 1px solid rgba(100, 181, 246, 0.2);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(100, 181, 246, 0.4);
    box-shadow: 0 4px 12px rgba(26, 115, 232, 0.15);
  }

  ${props => !props.hasPermission && `
    opacity: 0.6;
    background: linear-gradient(135deg, rgba(158, 158, 158, 0.08) 0%, rgba(158, 158, 158, 0.03) 100%);
    border-color: rgba(158, 158, 158, 0.2);
  `}
`;

const BotnetHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const BotnetInfo = styled.div`
  flex: 1;
`;

const BotnetName = styled.h3`
  margin: 0 0 8px 0;
  color: #90caf9;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const BotnetMeta = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
`;

const MetaBadge = styled.span`
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  
  ${props => props.type === 'c2' && `
    background: rgba(76, 175, 80, 0.2);
    color: #81c784;
    border: 1px solid rgba(76, 175, 80, 0.3);
  `}

  ${props => props.type === 'no-c2' && `
    background: rgba(255, 152, 0, 0.2);
    color: #ffb74d;
    border: 1px solid rgba(255, 152, 0, 0.3);
  `}

  ${props => props.type === 'status' && `
    background: rgba(26, 115, 232, 0.2);
    color: #64b5f6;
    border: 1px solid rgba(26, 115, 232, 0.3);
  `}
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
`;

const ActionButton = styled.button`
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 80px;

  ${props => props.variant === 'cleanup' && !props.disabled && `
    background: rgba(244, 67, 54, 0.1);
    border-color: rgba(244, 67, 54, 0.4);
    color: #ef5350;

    &:hover {
      background: rgba(244, 67, 54, 0.2);
      border-color: #ef5350;
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(244, 67, 54, 0.3);
    }
  `}

  ${props => props.variant === 'status' && !props.disabled && `
    background: rgba(26, 115, 232, 0.1);
    border-color: rgba(26, 115, 232, 0.4);
    color: #64b5f6;

    &:hover {
      background: rgba(26, 115, 232, 0.2);
      border-color: #64b5f6;
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(26, 115, 232, 0.3);
    }
  `}

  ${props => props.variant === 'reset' && !props.disabled && `
    background: rgba(255, 152, 0, 0.1);
    border-color: rgba(255, 152, 0, 0.4);
    color: #ffb74d;

    &:hover {
      background: rgba(255, 152, 0, 0.2);
      border-color: #ffb74d;
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
    }
  `}

  ${props => props.disabled && `
    opacity: 0.4;
    cursor: not-allowed;
    background: rgba(158, 158, 158, 0.1);
    border-color: rgba(158, 158, 158, 0.3);
    color: #9e9e9e;
  `}

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
`;

const StatusMessage = styled.div`
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  animation: slideIn 0.3s ease;

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  ${props => props.type === 'success' && `
    background: rgba(76, 175, 80, 0.15);
    border: 1px solid rgba(76, 175, 80, 0.3);
    color: #81c784;
  `}

  ${props => props.type === 'error' && `
    background: rgba(244, 67, 54, 0.15);
    border: 1px solid rgba(244, 67, 54, 0.3);
    color: #ef5350;
  `}

  ${props => props.type === 'info' && `
    background: rgba(26, 115, 232, 0.15);
    border: 1px solid rgba(26, 115, 232, 0.3);
    color: #64b5f6;
  `}
`;

const LoadingMessage = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #64b5f6;
  font-size: 16px;
  
  &:before {
    content: "⏳";
    display: block;
    font-size: 48px;
    margin-bottom: 16px;
  }
`;

const ErrorMessage = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #ef5350;
  font-size: 16px;

  &:before {
    content: "⚠️";
    display: block;
    font-size: 48px;
    margin-bottom: 16px;
  }
`;

const EmptyMessage = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #9e9e9e;
  font-size: 16px;

  &:before {
    content: "📭";
    display: block;
    font-size: 48px;
    margin-bottom: 16px;
  }
`;

// 主组件
const CleanupModal = ({ onClose, dispatch, selectedNetwork }) => {
  const [botnets, setBotnets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionStatus, setActionStatus] = useState({}); // 存储每个僵网的操作状态
  const [actionLoading, setActionLoading] = useState({}); // 存储每个僵网的加载状态

  // 获取僵网列表和权限信息
  const fetchBotnets = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      console.log('🔍 [CleanupModal] 开始获取僵网列表, selectedNetwork:', selectedNetwork);
      
      const response = await axios.get(`${API_BASE_URL}/api/cleanup/check-permissions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('📦 [CleanupModal] API响应:', response.data);
      
      if (response.data.status === 'success') {
        const allBotnets = response.data.data.botnets || [];
        console.log('📋 [CleanupModal] 所有僵网列表:', allBotnets);
        console.log('📋 [CleanupModal] 僵网名称列表:', allBotnets.map(b => b.botnet_name));
        
        // 如果有选中的僵网，只显示该僵网；否则显示所有僵网
        if (selectedNetwork) {
          // 容错处理：同时支持下划线和连字符格式的匹配
          const normalizeFormat = (name) => name?.replace(/[-_]/g, '_').toLowerCase();
          const normalizedSelected = normalizeFormat(selectedNetwork);
          
          const filteredBotnets = allBotnets.filter(b => {
            const normalizedBotnet = normalizeFormat(b.botnet_name);
            return normalizedBotnet === normalizedSelected;
          });
          
          console.log('🎯 [CleanupModal] 过滤后的僵网:', filteredBotnets);
          console.log('🎯 [CleanupModal] 过滤条件:', { 
            selectedNetwork, 
            normalizedSelected,
            匹配数量: filteredBotnets.length 
          });
          
          // 如果过滤后为空，回退到显示所有僵网（避免一直加载）
          if (filteredBotnets.length === 0) {
            console.warn('⚠️ [CleanupModal] 未找到匹配的僵网，回退显示全部');
            console.warn('⚠️ [CleanupModal] 可用的僵网:', allBotnets.map(b => b.botnet_name));
            setBotnets(allBotnets);
            setError(`未找到僵网 "${selectedNetwork}"，显示所有僵网`);
          } else {
            setBotnets(filteredBotnets);
          }
        } else {
          console.log('📋 [CleanupModal] 未选中僵网，显示全部');
          setBotnets(allBotnets);
        }
      } else {
        console.error('❌ [CleanupModal] API返回失败状态');
        setError('获取僵网列表失败');
      }
    } catch (err) {
      console.error('❌ [CleanupModal] 获取僵网列表失败:', err);
      console.error('❌ [CleanupModal] 错误详情:', err.response);
      setError(err.response?.data?.detail || '网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBotnets();
  }, [selectedNetwork]);

  // 执行操作
  const handleAction = async (botnetName, action) => {
    const key = `${botnetName}_${action}`;
    
    setActionLoading(prev => ({ ...prev, [key]: true }));
    setActionStatus(prev => ({ ...prev, [botnetName]: null }));
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/cleanup/execute/${botnetName}/${action}`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (response.data.status === 'success') {
        const c2Response = response.data.data.c2_response;
        let message = response.data.message;
        
        // 如果C2返回了详细信息，添加到消息中
        if (c2Response) {
          if (c2Response.mode) {
            message += ` - 当前模式: ${c2Response.mode}`;
          }
          if (c2Response.cleanup_mode !== undefined) {
            message += ` (清除模式: ${c2Response.cleanup_mode})`;
          }
        }
        
        setActionStatus(prev => ({
          ...prev,
          [botnetName]: { type: 'success', message }
        }));

        // 如果是清除操作且成功，触发红色飞线动画
        if (action === 'cleanup' && dispatch) {
          dispatch({
            type: 'mapState/handleFlyLines'
          });
        }
      } else {
        setActionStatus(prev => ({
          ...prev,
          [botnetName]: { type: 'error', message: '操作失败' }
        }));
      }
    } catch (err) {
      console.error('执行操作失败:', err);
      const errorMsg = err.response?.data?.detail || '操作失败，请稍后重试';
      setActionStatus(prev => ({
        ...prev,
        [botnetName]: { type: 'error', message: errorMsg }
      }));
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const withPermission = botnets.filter(b => b.has_c2_permission).length;
  const withoutPermission = botnets.filter(b => !b.has_c2_permission).length;

  // 使用Portal渲染到body，避免z-index堆叠上下文问题
  return ReactDOM.createPortal(
    <ModalOverlay onClick={onClose}>
      <ModalContainer onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>
            <span className="icon">🎯</span>
            <span>
              {selectedNetwork ? 
                (botnets.length > 0 ? 
                  `${botnets[0].display_name || selectedNetwork} - 一键清除` : 
                  `${selectedNetwork} - 一键清除`) : 
                '僵网一键清除'
              }
            </span>
            {!loading && !selectedNetwork && (
              <>
                <span className="count-badge">有权限: {withPermission}</span>
                {withoutPermission > 0 && (
                  <span className="warning-badge">无权限: {withoutPermission}</span>
                )}
              </>
            )}
          </ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        <ModalContent>
          {loading ? (
            <LoadingMessage>加载僵网列表中...</LoadingMessage>
          ) : error ? (
            <ErrorMessage>{error}</ErrorMessage>
          ) : botnets.length === 0 ? (
            <EmptyMessage>
              {selectedNetwork ? 
                `未找到僵网 "${selectedNetwork}" 的清除配置信息` : 
                '暂无僵网数据'
              }
            </EmptyMessage>
          ) : (
            botnets.map(botnet => (
              <BotnetCard key={botnet.botnet_name} hasPermission={botnet.has_c2_permission}>
                <BotnetHeader>
                  <BotnetInfo>
                    <BotnetName>
                      {botnet.display_name || botnet.botnet_name}
                      {botnet.has_c2_permission && <span>✓</span>}
                    </BotnetName>
                    <BotnetMeta>
                      {botnet.has_c2_permission ? (
                        <>
                          <MetaBadge type="c2">C2: {botnet.c2_ip}</MetaBadge>
                          {botnet.c2_status && (
                            <MetaBadge type="status">状态: {botnet.c2_status}</MetaBadge>
                          )}
                        </>
                      ) : (
                        <MetaBadge type="no-c2">
                          {botnet.reason || '无C2权限'}
                        </MetaBadge>
                      )}
                    </BotnetMeta>
                  </BotnetInfo>
                  <ButtonGroup>
                    <ActionButton
                      variant="status"
                      disabled={!botnet.has_c2_permission || actionLoading[`${botnet.botnet_name}_status`]}
                      onClick={() => handleAction(botnet.botnet_name, 'status')}
                    >
                      {actionLoading[`${botnet.botnet_name}_status`] ? '查询中...' : '查询'}
                    </ActionButton>
                    <ActionButton
                      variant="cleanup"
                      disabled={!botnet.has_c2_permission || actionLoading[`${botnet.botnet_name}_cleanup`]}
                      onClick={() => handleAction(botnet.botnet_name, 'cleanup')}
                    >
                      {actionLoading[`${botnet.botnet_name}_cleanup`] ? '清除中...' : '清除'}
                    </ActionButton>
                    <ActionButton
                      variant="reset"
                      disabled={!botnet.has_c2_permission || actionLoading[`${botnet.botnet_name}_reset`]}
                      onClick={() => handleAction(botnet.botnet_name, 'reset')}
                    >
                      {actionLoading[`${botnet.botnet_name}_reset`] ? '重置中...' : '重置'}
                    </ActionButton>
                  </ButtonGroup>
                </BotnetHeader>
                
                {actionStatus[botnet.botnet_name] && (
                  <StatusMessage type={actionStatus[botnet.botnet_name].type}>
                    {actionStatus[botnet.botnet_name].message}
                  </StatusMessage>
                )}
              </BotnetCard>
            ))
          )}
        </ModalContent>
      </ModalContainer>
    </ModalOverlay>,
    document.body
  );
};

export default CleanupModal;

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { getApiUrl } from '../config/api';
import { Modal, Input, Checkbox, message } from 'antd';

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
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  flex-shrink: 0;
  background: rgba(6, 19, 33, 0.92);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(2, 12, 24, 0.55);
`;

const Title = styled.h2`
  margin: 0;
  font-size: 24px;
  color: #dbe5ff;
  font-weight: 600;
`;

const ActionButton = styled.button`
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
  font-weight: 500;
  
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

const ContentArea = styled.div`
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const LevelCard = styled.div`
  background: rgba(6, 19, 33, 0.92);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 12px 30px rgba(2, 12, 24, 0.55);
  border: 1px solid rgba(79, 141, 255, 0.2);
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(79, 141, 255, 0.4);
    box-shadow: 0 12px 30px rgba(47, 74, 223, 0.25);
  }
`;

const LevelHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(79, 141, 255, 0.2);
`;

const LevelTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const LevelBadge = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: ${props => {
    switch(props.level) {
      case 1: return 'linear-gradient(135deg, #4caf50, #2e7d32)';
      case 2: return 'linear-gradient(135deg, #2196f3, #1565c0)';
      case 3: return 'linear-gradient(135deg, #ff9800, #e65100)';
      case 4: return 'linear-gradient(135deg, #f44336, #c62828)';
      case 5: return 'linear-gradient(135deg, #9c27b0, #6a1b9a)';
      default: return 'linear-gradient(135deg, #607d8b, #455a64)';
    }
  }};
  color: white;
  font-weight: bold;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
`;

const LevelName = styled.h3`
  margin: 0;
  font-size: 20px;
  color: #dbe5ff;
  font-weight: 600;
`;

const LevelDescription = styled.p`
  margin: 0 0 16px 0;
  color: #b8c8ff;
  line-height: 1.6;
  font-size: 15px;
`;

const InstructionType = styled.div`
  display: inline-block;
  padding: 6px 12px;
  background: rgba(79, 141, 255, 0.15);
  border: 1px solid rgba(79, 141, 255, 0.3);
  border-radius: 8px;
  color: #9fb7ff;
  font-size: 13px;
  margin-bottom: 16px;
`;

const BotnetList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 40px;
`;

const BotnetTag = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(79, 141, 255, 0.1);
  border: 1px solid rgba(79, 141, 255, 0.3);
  border-radius: 8px;
  color: #c5d7ff;
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(79, 141, 255, 0.15);
    border-color: rgba(79, 141, 255, 0.5);
  }
`;

const RemoveButton = styled.button`
  background: none;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  padding: 0;
  font-size: 16px;
  line-height: 1;
  transition: all 0.2s ease;
  
  &:hover {
    color: #ff4444;
    transform: scale(1.2);
  }
`;

const AddButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(79, 141, 255, 0.1);
  border: 1px dashed rgba(79, 141, 255, 0.4);
  border-radius: 8px;
  color: #9fb7ff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(79, 141, 255, 0.2);
    border-color: rgba(79, 141, 255, 0.6);
    color: #c5d7ff;
  }
`;

const EmptyState = styled.div`
  padding: 20px;
  text-align: center;
  color: #7a9cc6;
  font-size: 14px;
  font-style: italic;
`;

const StyledModal = styled(Modal)`
  .ant-modal-content {
    background: rgba(13, 27, 45, 0.98);
    border: 1px solid rgba(79, 141, 255, 0.3);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
  }

  .ant-modal-header {
    background: transparent;
    border-bottom: 1px solid rgba(79, 141, 255, 0.2);
  }

  .ant-modal-title {
    color: #dbe5ff;
    font-size: 18px;
    font-weight: 600;
  }

  .ant-modal-body {
    padding: 24px;
  }

  .ant-modal-footer {
    border-top: 1px solid rgba(79, 141, 255, 0.2);
    background: transparent;
  }

  .ant-input {
    background: rgba(12, 27, 45, 0.9);
    border: 1px solid rgba(79, 141, 255, 0.3);
    color: #f5f7ff;
    
    &:focus {
      border-color: #4f8dff;
      box-shadow: 0 0 0 2px rgba(79, 141, 255, 0.25);
    }

    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }

  .ant-checkbox-wrapper {
    color: #c5d7ff;
    margin: 8px 0;
    display: flex;
    align-items: center;
    
    .ant-checkbox {
      top: 0;
      
      .ant-checkbox-inner {
        background: rgba(12, 27, 45, 0.9);
        border-color: rgba(79, 141, 255, 0.3);
      }
      
      &.ant-checkbox-checked .ant-checkbox-inner {
        background: #4f8dff;
        border-color: #4f8dff;
      }
    }
    
    &:hover .ant-checkbox .ant-checkbox-inner {
      border-color: #4f8dff;
    }
    
    span:not(.ant-checkbox) {
      padding-left: 8px;
    }
  }

  .ant-btn {
    border-radius: 8px;
    font-weight: 500;
    
    &.ant-btn-primary {
      background: linear-gradient(135deg, #4f8dff 0%, #2f4adf 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #5b96ff 0%, #3a57ff 100%);
        box-shadow: 0 4px 12px rgba(47, 74, 223, 0.35);
      }
    }
    
    &.ant-btn-default {
      background: rgba(79, 141, 255, 0.1);
      border: 1px solid rgba(79, 141, 255, 0.3);
      color: #c5d7ff;
      
      &:hover {
        background: rgba(79, 141, 255, 0.15);
        border-color: rgba(79, 141, 255, 0.5);
        color: #dbe5ff;
      }
    }
  }
`;

const ControllabilityAssessment = () => {
  const [levels, setLevels] = useState([]);
  const [mappings, setMappings] = useState({});
  const [availableBotnetTypes, setAvailableBotnetTypes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedLevelId, setSelectedLevelId] = useState(null);
  const [selectedBotnets, setSelectedBotnets] = useState([]);

  // 获取可控性等级定义
  const fetchLevels = async () => {
    try {
      const response = await fetch(getApiUrl('/api/controllability/levels'));
      if (!response.ok) throw new Error('Failed to fetch levels');
      const data = await response.json();
      setLevels(data);
    } catch (error) {
      console.error('Error fetching levels:', error);
      message.error('获取可控性等级失败');
    }
  };

  // 获取僵尸网络映射关系
  const fetchMappings = async () => {
    try {
      const response = await fetch(getApiUrl('/api/controllability/mappings'));
      if (!response.ok) throw new Error('Failed to fetch mappings');
      const data = await response.json();
      
      // 按等级组织数据
      const mappingsByLevel = {};
      data.forEach(mapping => {
        if (!mappingsByLevel[mapping.level_id]) {
          mappingsByLevel[mapping.level_id] = [];
        }
        mappingsByLevel[mapping.level_id].push(mapping);
      });
      
      setMappings(mappingsByLevel);
    } catch (error) {
      console.error('Error fetching mappings:', error);
      message.error('获取僵尸网络映射关系失败');
    }
  };

  // 获取所有僵尸网络类型
  const fetchBotnetTypes = async () => {
    try {
      const response = await fetch(getApiUrl('/api/controllability/available-botnets'));
      if (!response.ok) throw new Error('Failed to fetch botnet types');
      const data = await response.json();
      if (data.status === 'success') {
        setAvailableBotnetTypes(data.data);
      }
    } catch (error) {
      console.error('Error fetching botnet types:', error);
      message.error('获取僵尸网络类型失败');
    }
  };

  // 初始加载
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchLevels(), fetchMappings(), fetchBotnetTypes()]);
      setIsLoading(false);
    };
    loadData();
  }, []);

  // 显示添加僵尸网络对话框
  const showAddModal = async (levelId) => {
    setSelectedLevelId(levelId);
    setSelectedBotnets([]);
    setModalVisible(true);
    // 刷新僵尸网络列表，确保显示最新添加的僵尸网络类型
    await fetchBotnetTypes();
  };

  // 添加僵尸网络到等级
  const handleAddBotnets = async () => {
    if (selectedBotnets.length === 0) {
      message.warning('请至少选择一个僵尸网络');
      return;
    }

    try {
      const response = await fetch(getApiUrl('/api/controllability/mappings'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          level_id: selectedLevelId,
          botnet_names: selectedBotnets
        })
      });

      if (!response.ok) throw new Error('Failed to add botnets');
      
      message.success('添加成功');
      setModalVisible(false);
      await fetchMappings();
    } catch (error) {
      console.error('Error adding botnets:', error);
      message.error('添加失败，请重试');
    }
  };

  // 删除僵尸网络映射
  const handleRemoveBotnet = async (mappingId, botnetName) => {
    try {
      const response = await fetch(getApiUrl(`/api/controllability/mappings/${mappingId}`), {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to remove botnet');
      
      message.success(`已移除 ${botnetName}`);
      await fetchMappings();
    } catch (error) {
      console.error('Error removing botnet:', error);
      message.error('删除失败，请重试');
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setIsLoading(true);
    await Promise.all([fetchLevels(), fetchMappings()]);
    setIsLoading(false);
    message.success('刷新成功');
  };

  // 获取未分配到当前等级的僵尸网络
  const getAvailableBotnetsForLevel = (levelId) => {
    const assignedBotnets = (mappings[levelId] || []).map(m => m.botnet_name);
    return availableBotnetTypes.filter(b => !assignedBotnets.includes(b));
  };

  return (
    <Container>
      <TopBar>
        <Title>可控性量化评估</Title>
        <ActionButton onClick={handleRefresh}>
          <span>🔄</span>
          刷新数据
        </ActionButton>
      </TopBar>

      <ContentArea>
        {isLoading ? (
          <EmptyState>加载中...</EmptyState>
        ) : levels.length === 0 ? (
          <EmptyState>暂无可控性等级数据</EmptyState>
        ) : (
          levels.map(level => (
            <LevelCard key={level.id}>
              <LevelHeader>
                <LevelTitle>
                  <LevelBadge level={level.id}>{level.id}</LevelBadge>
                  <div>
                    <LevelName>种类{level.id}（{level.level_name}）</LevelName>
                  </div>
                </LevelTitle>
              </LevelHeader>

              <LevelDescription>{level.description}</LevelDescription>
              
              {level.instruction_type && (
                <InstructionType>指令类型：{level.instruction_type}</InstructionType>
              )}

              <BotnetList>
                {mappings[level.id] && mappings[level.id].length > 0 ? (
                  mappings[level.id].map(mapping => (
                    <BotnetTag key={mapping.id}>
                      <span>{mapping.botnet_name}</span>
                      <RemoveButton 
                        onClick={() => handleRemoveBotnet(mapping.id, mapping.botnet_name)}
                        title="移除"
                      >
                        ×
                      </RemoveButton>
                    </BotnetTag>
                  ))
                ) : null}
                
                <AddButton onClick={() => showAddModal(level.id)}>
                  <span>+</span>
                  添加僵尸网络
                </AddButton>
              </BotnetList>
            </LevelCard>
          ))
        )}
      </ContentArea>

      <StyledModal
        title="添加僵尸网络"
        open={modalVisible}
        onOk={handleAddBotnets}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16, color: '#b8c8ff' }}>
          选择要添加到此等级的僵尸网络：
        </div>
        {selectedLevelId && getAvailableBotnetsForLevel(selectedLevelId).map(botnet => (
          <Checkbox
            key={botnet}
            checked={selectedBotnets.includes(botnet)}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedBotnets([...selectedBotnets, botnet]);
              } else {
                setSelectedBotnets(selectedBotnets.filter(b => b !== botnet));
              }
            }}
          >
            {botnet}
          </Checkbox>
        ))}
        {selectedLevelId && getAvailableBotnetsForLevel(selectedLevelId).length === 0 && (
          <div style={{ color: '#7a9cc6', fontStyle: 'italic' }}>
            所有僵尸网络都已添加到此等级
          </div>
        )}
      </StyledModal>
    </Container>
  );
};

export default ControllabilityAssessment;

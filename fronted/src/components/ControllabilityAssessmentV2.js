import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { getApiUrl } from '../config/api';
import { Modal, Checkbox, Input, message } from 'antd';

const { TextArea } = Input;

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

const RefreshButton = styled.button`
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #4f8dff 0%, #2f4adf 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 13px;
  
  &:hover {
    background: linear-gradient(135deg, #5b96ff 0%, #3a57ff 100%);
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(47, 74, 223, 0.35);
  }
`;

const LegendSection = styled.div`
  background: rgba(6, 19, 33, 0.92);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 12px 30px rgba(2, 12, 24, 0.55);
`;

const LegendTitle = styled.h3`
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #dbe5ff;
  font-weight: 600;
  text-align: center;
`;

const LegendGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
`;

const LegendCard = styled.div`
  background: rgba(15, 36, 60, 0.5);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid ${props => {
    switch(props.level) {
      case 1: return '#4caf50';
      case 2: return '#2196f3';
      case 3: return '#ff9800';
      case 4: return '#f44336';
      case 5: return '#9c27b0';
      default: return '#607d8b';
    }
  }};
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(15, 36, 60, 0.7);
    transform: translateX(4px);
  }
`;

const LegendHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
`;

const LevelBadge = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  border-radius: 6px;
  background: ${props => {
    switch(props.level) {
      case 1: return '#4caf50';
      case 2: return '#2196f3';
      case 3: return '#ff9800';
      case 4: return '#f44336';
      case 5: return '#9c27b0';
      default: return '#607d8b';
    }
  }};
  color: white;
  font-weight: bold;
  font-size: 14px;
`;

const LegendName = styled.span`
  font-size: 16px;
  font-weight: 600;
  color: #dbe5ff;
`;

const LegendDesc = styled.p`
  margin: 0;
  font-size: 14px;
  color: #b8c8ff;
  line-height: 1.5;
`;

const TableSection = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(6, 19, 33, 0.92);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(2, 12, 24, 0.55);
  overflow: hidden;
`;

const TableHeader = styled.div`
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(79, 141, 255, 0.2);
  background: rgba(15, 36, 60, 0.5);
`;

const TableContainer = styled.div`
  flex: 1;
  overflow: auto;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: transparent;
`;

const Thead = styled.thead`
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(15, 36, 60, 0.95);
`;

const Th = styled.th`
  padding: 16px 12px;
  text-align: center;
  border-bottom: 2px solid rgba(79, 141, 255, 0.3);
  font-weight: 600;
  color: #dbe5ff;
  font-size: 14px;
  white-space: nowrap;
  
  &:first-child {
    text-align: left;
    padding-left: 24px;
  }
  
  &:last-child {
    text-align: right;
    padding-right: 24px;
  }
`;

const Tbody = styled.tbody``;

const Tr = styled.tr`
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(39, 76, 128, 0.25);
  }
`;

const Td = styled.td`
  padding: 16px 12px;
  border-bottom: 1px solid rgba(79, 141, 255, 0.1);
  color: #eef2ff;
  text-align: center;
  font-size: 14px;
  
  &:first-child {
    text-align: left;
    padding-left: 24px;
    font-weight: 500;
  }
  
  &:last-child {
    text-align: right;
    padding-right: 24px;
  }
`;

const CheckIcon = styled.span`
  color: ${props => props.checked ? '#4caf50' : '#f44336'};
  font-size: 18px;
  font-weight: bold;
`;

const LevelsDisplay = styled.span`
  color: #9fb7ff;
  font-weight: 500;
`;

const EditButton = styled.button`
  padding: 6px 14px;
  border: 1px solid rgba(79, 141, 255, 0.5);
  border-radius: 6px;
  background: rgba(79, 141, 255, 0.1);
  color: #9fb7ff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(79, 141, 255, 0.2);
    border-color: rgba(79, 141, 255, 0.8);
    color: #c5d7ff;
    transform: translateY(-1px);
  }
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
    max-height: 60vh;
    overflow-y: auto;
  }

  .ant-modal-footer {
    border-top: 1px solid rgba(79, 141, 255, 0.2);
    background: transparent;
  }

  .ant-checkbox-wrapper {
    color: #c5d7ff;
    margin: 12px 0;
    display: flex;
    align-items: center;
    
    .ant-checkbox {
      top: 0;
      
      .ant-checkbox-inner {
        background: rgba(12, 27, 45, 0.9);
        border-color: rgba(79, 141, 255, 0.3);
        width: 20px;
        height: 20px;
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
      padding-left: 10px;
      font-size: 15px;
    }
  }

  .ant-input,
  .ant-input-textarea textarea {
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

const FeatureSection = styled.div`
  margin-bottom: 20px;
`;

const SectionTitle = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #dbe5ff;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(79, 141, 255, 0.2);
`;

const PreviewLevels = styled.div`
  margin-top: 20px;
  padding: 16px;
  background: rgba(79, 141, 255, 0.1);
  border: 1px solid rgba(79, 141, 255, 0.3);
  border-radius: 8px;
`;

const PreviewTitle = styled.div`
  font-size: 14px;
  color: #b8c8ff;
  margin-bottom: 8px;
`;

const PreviewValue = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #dbe5ff;
`;

const ControllabilityAssessmentV2 = () => {
  const [levels, setLevels] = useState([]);
  const [botnets, setBotnets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedBotnet, setSelectedBotnet] = useState(null);
  const [editForm, setEditForm] = useState({
    has_uninstall_instruction: false,
    has_download_instruction: false,
    has_command_execution: false,
    has_special_cleanup: false,
    notes: ''
  });

  // 计算等级（前端预览用）
  const calculateLevels = (features) => {
    const levels = [];
    
    if (features.has_uninstall_instruction) levels.push(1);
    if (features.has_download_instruction) levels.push(2);
    if (features.has_command_execution) levels.push(3);
    
    if (!features.has_uninstall_instruction && 
        !features.has_download_instruction && 
        !features.has_command_execution && 
        features.has_special_cleanup) {
      levels.push(4);
    }
    
    if (levels.length === 0) levels.push(5);
    
    return levels.sort().map(l => `类别${l}`).join('、');
  };

  // 获取等级定义
  const fetchLevels = async () => {
    try {
      const response = await fetch(getApiUrl('/api/controllability-v2/levels'));
      if (!response.ok) throw new Error('Failed to fetch levels');
      const data = await response.json();
      setLevels(data);
    } catch (error) {
      console.error('Error fetching levels:', error);
      message.error('获取等级定义失败');
    }
  };

  // 获取所有僵尸网络特征
  const fetchBotnets = async () => {
    try {
      const response = await fetch(getApiUrl('/api/controllability-v2/features'));
      if (!response.ok) throw new Error('Failed to fetch botnets');
      const data = await response.json();
      setBotnets(data);
    } catch (error) {
      console.error('Error fetching botnets:', error);
      message.error('获取僵尸网络数据失败');
    }
  };

  // 初始加载
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchLevels(), fetchBotnets()]);
      setIsLoading(false);
    };
    loadData();
  }, []);

  // 打开编辑对话框
  const handleEdit = (botnet) => {
    setSelectedBotnet(botnet);
    setEditForm({
      has_uninstall_instruction: botnet.has_uninstall_instruction,
      has_download_instruction: botnet.has_download_instruction,
      has_command_execution: botnet.has_command_execution,
      has_special_cleanup: botnet.has_special_cleanup,
      notes: botnet.notes || ''
    });
    setModalVisible(true);
  };

  // 提交更新
  const handleSubmit = async () => {
    try {
      const response = await fetch(
        getApiUrl(`/api/controllability-v2/features/${selectedBotnet.botnet_name}`),
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(editForm)
        }
      );

      if (!response.ok) throw new Error('Update failed');
      
      const result = await response.json();
      message.success(`已更新 ${selectedBotnet.botnet_name} 的特征，新等级：${result.levels_display}`);
      
      setModalVisible(false);
      await fetchBotnets();
    } catch (error) {
      console.error('Error updating botnet:', error);
      message.error('更新失败，请重试');
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setIsLoading(true);
    await Promise.all([fetchLevels(), fetchBotnets()]);
    setIsLoading(false);
    message.success('刷新成功');
  };

  return (
    <Container>
      {/* 等级说明书 */}
      <LegendSection>
        <LegendTitle>📋 可控性等级说明</LegendTitle>
        <LegendGrid>
          {levels.map((level) => (
            <LegendCard key={level.id} level={level.id}>
              <LegendHeader>
                <LevelBadge level={level.id}>类别{level.id}</LevelBadge>
                <LegendName>{level.level_name}</LegendName>
              </LegendHeader>
              <LegendDesc>{level.description}</LegendDesc>
            </LegendCard>
          ))}
        </LegendGrid>
      </LegendSection>

      {/* 僵尸网络特征表格 */}
      <TableSection>
        <TableHeader>
          <RefreshButton onClick={handleRefresh}>
            <span>🔄</span>
            刷新数据
          </RefreshButton>
        </TableHeader>
        <TableContainer>
          <Table>
          <Thead>
            <tr>
              <Th>僵尸网络</Th>
              <Th>是否有卸载<br/>或等效指令</Th>
              <Th>是否有<br/>下载指令</Th>
              <Th>是否可执行<br/>任意系统命令</Th>
              <Th>是否可通过<br/>特定方法清除</Th>
              <Th>判别等级</Th>
              <Th>操作</Th>
            </tr>
          </Thead>
          <Tbody>
            {isLoading ? (
              <Tr>
                <Td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                  加载中...
                </Td>
              </Tr>
            ) : botnets.length === 0 ? (
              <Tr>
                <Td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                  暂无数据
                </Td>
              </Tr>
            ) : (
              botnets.map((botnet) => (
                <Tr key={botnet.id}>
                  <Td>{botnet.botnet_name}</Td>
                  <Td>
                    <CheckIcon checked={botnet.has_uninstall_instruction}>
                      {botnet.has_uninstall_instruction ? '✓' : '✗'}
                    </CheckIcon>
                  </Td>
                  <Td>
                    <CheckIcon checked={botnet.has_download_instruction}>
                      {botnet.has_download_instruction ? '✓' : '✗'}
                    </CheckIcon>
                  </Td>
                  <Td>
                    <CheckIcon checked={botnet.has_command_execution}>
                      {botnet.has_command_execution ? '✓' : '✗'}
                    </CheckIcon>
                  </Td>
                  <Td>
                    <CheckIcon checked={botnet.has_special_cleanup}>
                      {botnet.has_special_cleanup ? '✓' : '✗'}
                    </CheckIcon>
                  </Td>
                  <Td>
                    <LevelsDisplay>{botnet.levels_display}</LevelsDisplay>
                  </Td>
                  <Td>
                    <EditButton onClick={() => handleEdit(botnet)}>
                      编辑
                    </EditButton>
                  </Td>
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </TableContainer>
      </TableSection>

      {/* 编辑对话框 */}
      <StyledModal
        title={`编辑僵尸网络特征 - ${selectedBotnet?.botnet_name}`}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <FeatureSection>
          <SectionTitle>特征选择</SectionTitle>
          <Checkbox
            checked={editForm.has_uninstall_instruction}
            onChange={(e) => setEditForm({...editForm, has_uninstall_instruction: e.target.checked})}
          >
            是否有卸载或等效指令
          </Checkbox>
          <Checkbox
            checked={editForm.has_download_instruction}
            onChange={(e) => setEditForm({...editForm, has_download_instruction: e.target.checked})}
          >
            是否有下载指令
          </Checkbox>
          <Checkbox
            checked={editForm.has_command_execution}
            onChange={(e) => setEditForm({...editForm, has_command_execution: e.target.checked})}
          >
            是否可执行任意系统命令
          </Checkbox>
          <Checkbox
            checked={editForm.has_special_cleanup}
            onChange={(e) => setEditForm({...editForm, has_special_cleanup: e.target.checked})}
          >
            是否可通过特定方法清除
          </Checkbox>
        </FeatureSection>

        <FeatureSection>
          <SectionTitle>备注信息</SectionTitle>
          <TextArea
            value={editForm.notes}
            onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
            placeholder="输入备注信息（可选）"
            rows={3}
          />
        </FeatureSection>

        <PreviewLevels>
          <PreviewTitle>根据选择的特征，系统将自动判定为：</PreviewTitle>
          <PreviewValue>{calculateLevels(editForm)}</PreviewValue>
        </PreviewLevels>
      </StyledModal>
    </Container>
  );
};

export default ControllabilityAssessmentV2;

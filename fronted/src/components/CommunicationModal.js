import React, { useState, useEffect } from 'react';
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
  z-index: 10000;
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
  max-width: 1200px;
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

  .ip-badge {
    background: rgba(26, 115, 232, 0.2);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 16px;
    color: #90caf9;
    border: 1px solid rgba(100, 181, 246, 0.3);
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
  padding: 0;

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

// 表格容器
const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const TableHeader = styled.thead`
  background: linear-gradient(90deg, rgba(26, 115, 232, 0.15) 0%, rgba(26, 115, 232, 0.08) 100%);
  position: sticky;
  top: 0;
  z-index: 10;

  th {
    padding: 14px 16px;
    text-align: left;
    color: #64b5f6;
    font-weight: 600;
    font-size: 13px;
    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  }
`;

const TableBody = styled.tbody`
  tr {
    border-bottom: 1px solid rgba(100, 181, 246, 0.1);
    transition: all 0.2s ease;

    &:hover {
      background: rgba(26, 115, 232, 0.08);
    }

    td {
      padding: 12px 16px;
      color: #b0bec5;
      font-size: 13px;

      &.time {
        color: #81c784;
        font-family: 'Courier New', monospace;
      }

      &.location {
        color: #90caf9;
      }

      &.status {
        font-weight: 500;
      }
    }
  }
`;

const StatusBadge = styled.span`
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  
  ${props => props.status === 'active' ? `
    background: rgba(76, 175, 80, 0.2);
    color: #81c784;
    border: 1px solid rgba(76, 175, 80, 0.3);
  ` : `
    background: rgba(158, 158, 158, 0.2);
    color: #9e9e9e;
    border: 1px solid rgba(158, 158, 158, 0.3);
  `}
`;

// 分页栏
const PaginationBar = styled.div`
  padding: 16px 30px;
  border-top: 1px solid rgba(100, 181, 246, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(10, 25, 41, 0.4);
`;

const PageInfo = styled.div`
  color: #90caf9;
  font-size: 13px;
`;

const PageControls = styled.div`
  display: flex;
  gap: 8px;
`;

const PageButton = styled.button`
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  background: rgba(26, 115, 232, 0.1);
  color: #90caf9;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    background: rgba(26, 115, 232, 0.2);
    border-color: #64b5f6;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &.active {
    background: rgba(26, 115, 232, 0.3);
    border-color: #1a73e8;
    color: #64b5f6;
  }
`;

// 加载和空状态
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

// 主组件
const CommunicationModal = ({ ip, botnetType, onClose }) => {
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);

  const fetchCommunications = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        botnet_type: botnetType,
        ip: ip,
        page: page,
        page_size: pageSize
      };

      const response = await axios.get(`${API_BASE_URL}/api/node-communications`, { params });
      
      if (response.data.status === 'success') {
        setCommunications(response.data.data.communications || []);
        setTotal(response.data.data.total || 0);
      } else {
        setError('获取数据失败');
      }
    } catch (err) {
      console.error('获取通信记录失败:', err);
      setError(err.response?.data?.detail || '网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommunications();
  }, [page]);

  const totalPages = Math.ceil(total / pageSize);

  const formatTime = (timeStr) => {
    if (!timeStr) return '-';
    return new Date(timeStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContainer onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>
            <span>🌐 节点通信记录</span>
            <span className="ip-badge">{ip}</span>
            {!loading && <span className="count-badge">共 {total} 条记录</span>}
          </ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        <ModalContent>
          {loading ? (
            <LoadingMessage>加载中...</LoadingMessage>
          ) : error ? (
            <ErrorMessage>{error}</ErrorMessage>
          ) : communications.length === 0 ? (
            <EmptyMessage>暂无通信记录</EmptyMessage>
          ) : (
            <Table>
              <TableHeader>
                <tr>
                  <th>序号</th>
                  <th>通信时间</th>
                  <th>地理位置</th>
                  <th>ISP</th>
                  <th>状态</th>
                  <th>数据接收时间</th>
                </tr>
              </TableHeader>
              <TableBody>
                {communications.map((comm, index) => (
                  <tr key={comm.id}>
                    <td>{(page - 1) * pageSize + index + 1}</td>
                    <td className="time">{formatTime(comm.communication_time)}</td>
                    <td className="location">
                      {[comm.country, comm.province, comm.city]
                        .filter(Boolean)
                        .join(' - ') || '未知'}
                    </td>
                    <td>{comm.isp || '-'}</td>
                    <td className="status">
                      <StatusBadge status={comm.status}>
                        {comm.status === 'active' ? '在线' : '离线'}
                      </StatusBadge>
                    </td>
                    <td className="time">{formatTime(comm.received_at)}</td>
                  </tr>
                ))}
              </TableBody>
            </Table>
          )}
        </ModalContent>

        {!loading && !error && communications.length > 0 && (
          <PaginationBar>
            <PageInfo>
              第 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} 条，
              共 {total} 条记录
            </PageInfo>
            <PageControls>
              <PageButton
                onClick={() => setPage(1)}
                disabled={page === 1}
              >
                首页
              </PageButton>
              <PageButton
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                上一页
              </PageButton>
              <PageButton className="active">
                {page} / {totalPages}
              </PageButton>
              <PageButton
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
              >
                下一页
              </PageButton>
              <PageButton
                onClick={() => setPage(totalPages)}
                disabled={page >= totalPages}
              >
                末页
              </PageButton>
            </PageControls>
          </PaginationBar>
        )}
      </ModalContainer>
    </ModalOverlay>
  );
};

export default CommunicationModal;

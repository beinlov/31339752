import React, { useState, useEffect } from 'react';
import { getServers, createServer, updateServer, deleteServer } from '../services';
import styled from 'styled-components';
import { Table, Button, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;

const Container = styled.div`
  padding: 20px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const Title = styled.h2`
  margin: 0;
  color: #64b5f6;
  text-shadow: 0 0 10px rgba(100, 181, 246, 0.3);
  font-weight: 600;
`;

const ServerManagement = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingServer, setEditingServer] = useState(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取服务器列表
  const fetchServers = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await getServers(page, pageSize);
      console.log('API Response:', response); // 添加日志以便调试
      if (response && response.status === 'success') {
        // 按ID升序排序服务器数据
        const sortedServers = (response.data.servers || []).sort((a, b) => a.id - b.id);
        setServers(sortedServers);
        setPagination({
          current: page,
          pageSize: pageSize,
          total: response.data.pagination?.total_count || 0
        });
      } else {
        console.error('Invalid response format:', response);
        message.error('获取服务器列表失败: 响应格式错误');
      }
    } catch (error) {
      console.error('Error fetching servers:', error);
      message.error('获取服务器列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      key: 'index',
      width: 60,
      render: (_, __, index) => index + 1 + (pagination.current - 1) * pagination.pageSize,
    },
    {
      title: '地理位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
    },
    {
      title: '域名',
      dataIndex: 'domain',
      key: 'domain',
    },
    {
      title: '链路状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === '在线' ? '#52c41a' : status === '故障' ? '#f5222d' : '#faad14';
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {status}
          </span>
        );
      }
    },
    {
      title: '操作系统',
      dataIndex: 'os',
      key: 'os',
    },
    {
      title: '所属僵尸网络',
      dataIndex: 'botnet_name',
      key: 'botnet_name',
      render: (botnet_name) => botnet_name || '-',
    },
    {
      title: '节点总数统计',
      dataIndex: 'node_count',
      key: 'node_count',
      render: (count) => (count === null || count === undefined ? 'Null' : count),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <span>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个服务器吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 处理表格分页
  const handleTableChange = (pagination) => {
    fetchServers(pagination.current, pagination.pageSize);
  };

  // 打开添加服务器模态框
  const showAddModal = () => {
    setEditingServer(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑服务器模态框
  const handleEdit = (server) => {
    setEditingServer(server);
    form.setFieldsValue({
      location: server.location,
      ip: server.ip,
      domain: server.domain,
      status: server.status,
      os: server.os,
      botnet_name: server.botnet_name,
    });
    setModalVisible(true);
  };

  // 处理删除服务器
  const handleDelete = async (id) => {
    try {
      const response = await deleteServer(id);
      console.log('Delete Response:', response); // 添加日志以便调试
      if (response && response.status === 'success') {
        message.success('服务器删除成功');
        fetchServers(pagination.current, pagination.pageSize);
      } else {
        console.error('Invalid delete response:', response);
        message.error('删除服务器失败: 响应格式错误');
      }
    } catch (error) {
      console.error('Error deleting server:', error);
      message.error('删除服务器失败');
    }
  };

  // 处理模态框确认
  const handleModalOk = () => {
    form.validateFields().then(async (values) => {
      try {
        if (editingServer) {
          // 更新服务器
          const response = await updateServer(editingServer.id, values);
          console.log('Update Response:', response); // 添加日志以便调试
          if (response && response.status === 'success') {
            message.success('服务器更新成功');
            setModalVisible(false);
            fetchServers(pagination.current, pagination.pageSize);
          } else {
            console.error('Invalid update response:', response);
            message.error('更新服务器失败: 响应格式错误');
          }
        } else {
          // 添加服务器
          const response = await createServer(values);
          console.log('Create Response:', response); // 添加日志以便调试
          if (response && response.status === 'success') {
            message.success('服务器添加成功');
            setModalVisible(false);
            fetchServers(pagination.current, pagination.pageSize);
          } else {
            console.error('Invalid create response:', response);
            message.error('添加服务器失败: 响应格式错误');
          }
        }
      } catch (error) {
        console.error('Error saving server:', error);
        message.error(editingServer ? '更新服务器失败' : '添加服务器失败');
      }
    });
  };

  // 处理模态框取消
  const handleModalCancel = () => {
    setModalVisible(false);
  };

  return (
    <Container>
      <Header>
        <Title>服务器管理</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={showAddModal}
        >
          添加服务器
        </Button>
      </Header>

      <Table
        columns={columns}
        dataSource={servers}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />

      <Modal
        title={editingServer ? '编辑服务器' : '添加服务器'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="location"
            label="地理位置"
            rules={[{ required: true, message: '请输入地理位置' }]}
          >
            <Input placeholder="例如：北京市朝阳区" />
          </Form.Item>

          <Form.Item
            name="ip"
            label="IP地址"
            rules={[
              { required: true, message: '请输入IP地址' },
              { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: 'IP地址格式不正确' }
            ]}
          >
            <Input placeholder="例如：192.168.1.1" />
          </Form.Item>

          <Form.Item
            name="domain"
            label="域名"
            rules={[{ required: true, message: '请输入域名' }]}
          >
            <Input placeholder="例如：example.com" />
          </Form.Item>

          <Form.Item
            name="status"
            label="链路状态"
            rules={[{ required: true, message: '请选择链路状态' }]}
          >
            <Select placeholder="请选择链路状态">
              <Option value="在线">在线</Option>
              <Option value="离线">离线</Option>
              <Option value="故障">故障</Option>
              <Option value="维护中">维护中</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="os"
            label="操作系统"
            rules={[{ required: true, message: '请输入操作系统' }]}
          >
            <Input placeholder="例如：CentOS 7.9" />
          </Form.Item>

          <Form.Item
            name="botnet_name"
            label="所控制的僵尸网络"
            rules={[{ required: false, message: '请输入僵尸网络名称' }]}
          >
            <Input placeholder="例如：mirai" />
          </Form.Item>
        </Form>
      </Modal>
    </Container>
  );
};

export default ServerManagement;

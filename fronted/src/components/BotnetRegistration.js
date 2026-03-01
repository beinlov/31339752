import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const Container = styled.div`
  padding: 40px 50px;
  background: linear-gradient(135deg, rgba(10, 25, 41, 0.95) 0%, rgba(13, 31, 45, 0.95) 100%);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(30, 70, 120, 0.4);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  width: 95%;
  max-width: 1200px;
  margin: 0 auto;
  
  /* 顶部发光线 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #5a8fc4, transparent);
    box-shadow: 0 0 15px rgba(90, 143, 196, 0.8);
    z-index: 2;
  }
  
  &:hover {
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(90, 143, 196, 0.6);
    transform: translateY(-3px);
  }
`;

const Title = styled.h2`
  color: #ffffff;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  font-size: 36px;
  position: relative;
  text-shadow: 0 0 20px rgba(90, 143, 196, 0.8);
  letter-spacing: 2px;
  padding-bottom: 10px;
  
  &::before {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 3px;
    background: linear-gradient(90deg, transparent, #5a8fc4, transparent);
    box-shadow: 0 0 15px rgba(90, 143, 196, 0.8);
  }
  
  .iconfont {
    font-size: 42px;
    color: #5a8fc4;
    text-shadow: 0 0 15px rgba(90, 143, 196, 0.9);
    animation: pulse 2s infinite;
    
    @keyframes pulse {
      0% { opacity: 0.8; text-shadow: 0 0 15px rgba(90, 143, 196, 0.6); }
      50% { opacity: 1; text-shadow: 0 0 25px rgba(90, 143, 196, 1); }
      100% { opacity: 0.8; text-shadow: 0 0 15px rgba(90, 143, 196, 0.6); }
    }
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 100%;
  position: relative;
  z-index: 5;
  max-width: 900px;
  margin: 0 auto;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.3s ease;
  position: relative;
  
  &:focus-within {
    transform: translateY(-2px);
  }
  
  &:not(:last-child)::after {
    content: '';
    position: absolute;
    bottom: -16px;
    left: 5%;
    right: 5%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(90, 143, 196, 0.3), transparent);
  }
`;

const Label = styled.label`
  font-weight: 600;
  color: #ffffff;
  font-size: 15px;
  display: flex;
  align-items: center;
  text-shadow: 0 0 5px rgba(100, 181, 246, 0.3);
`;

const Input = styled.input`
  padding: 14px 18px;
  border: 2px solid rgba(30, 70, 120, 0.4);
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: rgba(15, 25, 35, 0.6);
  color: #ffffff;
  position: relative;
  z-index: 2;
  
  &:focus {
    outline: none;
    border-color: #5a8fc4;
    box-shadow: 0 0 20px rgba(90, 143, 196, 0.5);
    transform: translateY(-2px);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const TextArea = styled.textarea`
  padding: 12px 16px;
  border: 2px solid rgba(30, 70, 120, 0.3);
  border-radius: 8px;
  font-size: 15px;
  min-height: 120px;
  resize: vertical;
  transition: all 0.2s ease;
  background: rgba(15, 25, 35, 0.6);
  color: #ffffff;
  
  &:focus {
    outline: none;
    border-color: #5a8fc4;
    box-shadow: 0 0 15px rgba(90, 143, 196, 0.4);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const SubmitButton = styled.button`
  padding: 18px 40px;
  background: linear-gradient(90deg, #0f3057, rgba(15, 48, 87, 0.9));
  color: white;
  border: 1px solid rgba(90, 143, 196, 0.5);
  border-radius: 8px;
  font-weight: 600;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  box-shadow: 0 4px 20px rgba(15, 48, 87, 0.6);
  margin: 20px auto;
  position: relative;
  overflow: hidden;
  min-width: 280px;
  max-width: 100%;
  text-align: center;
  
  /* 科技感光效 */
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, #5a8fc4, transparent, #5a8fc4);
    z-index: -1;
    animation: rotate 4s linear infinite;
  }
  
  /* 按钮光效 */
  &::after {
    content: '';
    position: absolute;
    width: 30px;
    height: 200%;
    background: rgba(255, 255, 255, 0.2);
    transform: rotate(35deg);
    top: -50%;
    left: -100px;
    transition: all 0.6s ease;
    z-index: 0;
  }
  
  &:hover::after {
    left: 120%;
  }
  
  @keyframes rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  &::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    background: linear-gradient(90deg, #0f3057, rgba(15, 48, 87, 0.9));
    border-radius: 6px;
    z-index: -1;
  }
  
  &:hover {
    background: linear-gradient(90deg, #0a1f3d, #0d2847);
    transform: translateY(-3px);
    box-shadow: 0 0 25px rgba(90, 143, 196, 0.6);
    border-color: rgba(90, 143, 196, 0.7);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background: rgba(100, 100, 100, 0.3);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  
  .iconfont {
    font-size: 22px;
    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.7));
    position: relative;
    z-index: 2;
  }
  
  span {
    position: relative;
    z-index: 2;
  }
`;

const ErrorMessage = styled.div`
  color: #f44336;
  font-size: 14px;
  margin-top: 4px;
  padding: 10px 16px;
  background: rgba(244, 67, 54, 0.08);
  border-radius: 6px;
  border-left: 4px solid #f44336;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:before {
    content: '⚠️';
  }
`;

const SuccessMessage = styled.div`
  color: #2e7d32;
  font-size: 15px;
  padding: 16px;
  background: rgba(46, 125, 50, 0.08);
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 4px solid #2e7d32;
  font-weight: 500;
  
  &:before {
    content: '✅';
  }
`;

const InfoIcon = styled.span`
  font-size: 18px;
  color: #5a8fc4;
  margin-left: 8px;
  cursor: help;
  opacity: 0.8;
  transition: all 0.2s ease;
  
  &:hover {
    opacity: 1;
    text-shadow: 0 0 10px rgba(90, 143, 196, 0.6);
  }
`;

const TableNamePreview = styled.div`
  background: rgba(30, 70, 120, 0.2);
  padding: 12px 16px;
  border-radius: 8px;
  font-family: 'Consolas', monospace;
  color: #5a8fc4;
  margin-top: 8px;
  font-size: 15px;
  border: 1px dashed rgba(90, 143, 196, 0.4);
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:before {
    content: '💾';
  }
`;

const HelperText = styled.div`
  font-size: 13px;
  color: #7a9cc6;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  
  &:before {
    content: 'ℹ️';
    font-size: 12px;
  }
`;

const FormHeader = styled.div`
  margin-bottom: 50px;
  padding-bottom: 25px;
  position: relative;
  text-align: center;
  
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 5%;
    right: 5%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(90, 143, 196, 0.6), transparent);
    box-shadow: 0 0 15px rgba(90, 143, 196, 0.5);
  }
  
  &::before {
    content: '';
    position: absolute;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, rgba(90, 143, 196, 0.2) 0%, transparent 70%);
    top: -20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: -1;
    filter: blur(20px);
  }
`;

const BotnetRegistration = () => {
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: ''
  });
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 自动生成display_name
    if (name === 'name') {
      setFormData(prev => ({
        ...prev,
        display_name: `${value.charAt(0).toUpperCase() + value.slice(1)}僵尸网络`
      }));
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);
    
    try {
      // 验证输入
      if (!formData.name.trim()) {
        throw new Error('请输入僵尸网络名称');
      }
      
      if (!formData.name.match(/^[a-z0-9_]+$/)) {
        throw new Error('僵尸网络名称只能包含小写字母、数字和下划线');
      }
      
      // 自动生成table_name
      const table_name = `china_botnet_${formData.name.toLowerCase()}`;
      
      // 获取token
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('请先登录');
      }
      
      console.log('发送请求，token:', token ? '存在' : '不存在');
      console.log('请求数据:', { ...formData, table_name });
      
      const response = await axios.post(getApiUrl('/api/botnet-types'), {
        ...formData,
        table_name,
        clean_methods: ["clear", "suppress"]  // 默认清理方法
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('响应:', response.data);
      
      if (response.data.status === 'success') {
        setSuccess('僵尸网络类型添加成功！相关数据表已自动创建。');
        // 清空表单
        setFormData({
          name: '',
          display_name: '',
          description: ''
        });
        
        // 3秒后刷新页面或跳转
        setTimeout(() => {
          setSuccess('');
        }, 3000);
      }
    } catch (err) {
      console.error('添加失败:', err);
      console.error('错误响应:', err.response?.data);
      
      let errorMsg = '添加失败，请稍后重试';
      
      if (err.response?.status === 401) {
        errorMsg = '认证失败，请重新登录';
        // 清除过期的token
        localStorage.removeItem('token');
        // 3秒后跳转到登录页
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else if (err.response?.status === 403) {
        errorMsg = '权限不足，需要管理员权限';
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Container>
      <FormHeader>
        <Title>
          <span className="iconfont">&#xe328;</span>
          添加新僵尸网络
        </Title>
      </FormHeader>
      
      {success && <SuccessMessage>{success}</SuccessMessage>}
  
      <Form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="name">
            僵尸网络名称 *
            <InfoIcon className="iconfont" title="将用于生成数据表名：china_botnet_名称">&#xe88f;</InfoIcon>
          </Label>
          <Input
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="请输入英文名称，如：mirai"
          />
          <HelperText>
            只能包含小写字母、数字和下划线，不能包含空格和特殊字符
          </HelperText>
          {/* {formData.name && (
            <TableNamePreview>
              表名: china_botnet_{formData.name.toLowerCase()}
            </TableNamePreview>
          )} */}
        </FormGroup>
        
        <FormGroup>
          <Label htmlFor="display_name">显示名称 *</Label>
          <Input
            id="display_name"
            name="display_name"
            value={formData.display_name}
            onChange={handleChange}
            placeholder="显示名称会自动生成，也可手动修改"
          />
        </FormGroup>
        
        <FormGroup>
          <Label htmlFor="description">描述</Label>
          <TextArea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="请输入该僵尸网络的详细描述，包括特征、危害等信息"
          />
        </FormGroup>
        
        {error && <ErrorMessage>{error}</ErrorMessage>}
        
        <SubmitButton type="submit" disabled={isSubmitting}>
          <span className="iconfont">&#xe146;</span>
          {isSubmitting ? '添加中...' : '添加新僵尸网络'}
        </SubmitButton>
      </Form>
    </Container>
  );
};

export default BotnetRegistration; 
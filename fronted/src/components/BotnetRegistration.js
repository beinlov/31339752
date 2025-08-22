import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const Container = styled.div`
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
  }
`;

const Title = styled.h2`
  color: #1a237e;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  position: relative;
  
  &:after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 60px;
    height: 4px;
    background: #1a237e;
    border-radius: 2px;
  }
  
  .icon {
    font-size: 32px;
    color: #1a237e;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 600px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.3s ease;
  
  &:focus-within {
    transform: translateY(-2px);
  }
`;

const Label = styled.label`
  font-weight: 600;
  color: #333;
  font-size: 15px;
  display: flex;
  align-items: center;
`;

const Input = styled.input`
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #1a237e;
    box-shadow: 0 0 0 3px rgba(26, 35, 126, 0.15);
  }
  
  &::placeholder {
    color: #aaa;
  }
`;

const TextArea = styled.textarea`
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  min-height: 120px;
  resize: vertical;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #1a237e;
    box-shadow: 0 0 0 3px rgba(26, 35, 126, 0.15);
  }
  
  &::placeholder {
    color: #aaa;
  }
`;

const SubmitButton = styled.button`
  padding: 14px 28px;
  background: #1a237e;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(26, 35, 126, 0.25);
  
  &:hover {
    background: #0d1642;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(26, 35, 126, 0.35);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background: #bbc1e1;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
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
  color: #1a237e;
  margin-left: 8px;
  cursor: help;
  opacity: 0.8;
  transition: all 0.2s ease;
  
  &:hover {
    opacity: 1;
  }
`;

const TableNamePreview = styled.div`
  background: rgba(26, 35, 126, 0.08);
  padding: 12px 16px;
  border-radius: 8px;
  font-family: 'Consolas', monospace;
  color: #1a237e;
  margin-top: 8px;
  font-size: 15px;
  border: 1px dashed rgba(26, 35, 126, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:before {
    content: '💾';
  }
`;

const HelperText = styled.div`
  font-size: 13px;
  color: #666;
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
  margin-bottom: 32px;
  border-bottom: 1px solid #eee;
  padding-bottom: 16px;
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
      
      const response = await axios.post('/api/botnet-types', {
        ...formData,
        table_name
      });
      
      if (response.data.status === 'success') {
        setSuccess('僵尸网络类型添加成功！');
        // 清空表单
        setFormData({
          name: '',
          display_name: '',
          description: ''
        });
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '添加失败，请稍后重试');
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
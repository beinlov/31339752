import React, { useState } from 'react';
import { withRouter } from 'dva/router';
import styled from 'styled-components';
import backgroundImage from '../assets/images/党旗3.png';
import axios from 'axios';

// 样式定义
const LoginContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: url(${backgroundImage}) no-repeat center center;
  background-size: cover;
`;

const LoginBox = styled.div`
  width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  text-align: center;
  color: #d32f2f;
  margin-bottom: 30px;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  margin: 10px 0;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
  &:focus {
    outline: none;
    border-color: #d32f2f;
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 12px;
  margin: 10px 0;
  background: #d32f2f;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  &:hover {
    background: #b71c1c;
  }
  &:disabled {
    background: #cccccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: #d32f2f;
  text-align: center;
  margin: 10px 0;
  font-size: 14px;
`;

const LoadingSpinner = styled.div`
  border: 3px solid #f3f3f3;
  border-radius: 50%;
  border-top: 3px solid #d32f2f;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoginPage = ({ history }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      // 使用URLSearchParams来正确编码表单数据
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');

      console.log('Sending login request with:', {
        username,
        password: password.length + ' characters'
      });

      const response = await axios.post(
        'http://localhost:8000/api/user/login',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      console.log('Login response:', response.data);

      const { access_token, role, username: loggedInUsername } = response.data;

      // 保存认证信息到localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('role', role);
      localStorage.setItem('username', loggedInUsername);

      // 根据角色重定向到不同页面
      if (role === '管理员') {
        history.push('/admin');
      } else {
        history.push('/index');
      }
    } catch (error) {
      console.error('Login error:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        setError(error.response.data.detail || '登录失败，请检查用户名和密码');
      } else {
        setError('网络错误，请稍后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <LoginContainer>
      <LoginBox>
        <Title>用户登录</Title>
        <Input
          type="text"
          placeholder="请输入用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          autoComplete="username"
        />
        <Input
          type="password"
          placeholder="请输入密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          autoComplete="current-password"
        />
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <Button onClick={handleLogin} disabled={isLoading}>
          {isLoading ? <LoadingSpinner /> : '登录'}
        </Button>
      </LoginBox>
    </LoginContainer>
  );
};

export default withRouter(LoginPage);

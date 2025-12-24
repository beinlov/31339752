import React, { useState } from 'react';
import { withRouter } from 'dva/router';
import styled, { keyframes } from 'styled-components';
import backgroundImage from '../assets/pageBg.png';
import axios from 'axios';

const pulseBackground = keyframes`
  0% {
    transform: scale(1) translateY(0px);
    opacity: 0.35;
  }
  50% {
    transform: scale(1.05) translateY(-10px);
    opacity: 0.45;
  }
  100% {
    transform: scale(1.1) translateY(0px);
    opacity: 0.35;
  }
`;

const rotateGlow = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const floatUp = keyframes`
  0% {
    opacity: 0;
    transform: translateY(30px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
`;

const driftStars = keyframes`
  0% {
    transform: translateY(0);
  }
  100% {
    transform: translateY(-200px);
  }
`;

const auroraFlow = keyframes`
  0% {
    transform: translateX(-20%) skewX(-8deg);
    opacity: 0.25;
  }
  50% {
    transform: translateX(15%) skewX(-4deg);
    opacity: 0.45;
  }
  100% {
    transform: translateX(40%) skewX(-10deg);
    opacity: 0.25;
  }
`;

const floatOrb = keyframes`
  0% {
    transform: translate(-20px, 0px) scale(0.9);
  }
  50% {
    transform: translate(20px, -20px) scale(1.05);
  }
  100% {
    transform: translate(-20px, 0px) scale(0.9);
  }
`;

const shimmerBorder = keyframes`
  0% {
    opacity: 0.35;
  }
  50% {
    opacity: 0.65;
  }
  100% {
    opacity: 0.35;
  }
`;

// 样式定义
const LoginContainer = styled.div`
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: radial-gradient(circle at top, rgba(0, 188, 212, 0.35), transparent 40%),
    #020a1a;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: url(${backgroundImage}) no-repeat center center/cover;
    opacity: 0.4;
    filter: saturate(1.4);
    animation: ${pulseBackground} 30s ease-in-out infinite alternate;
  }

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle, rgba(13, 71, 161, 0.55), rgba(2, 10, 26, 0.9));
    mix-blend-mode: screen;
    pointer-events: none;
    animation: ${rotateGlow} 60s linear infinite;
  }
`;

const StarField = styled.div`
  position: absolute;
  inset: -100px;
  pointer-events: none;
  background:
    radial-gradient(1px 1px at 5% 15%, rgba(255, 255, 255, 0.9), transparent),
    radial-gradient(1px 1px at 15% 85%, rgba(0, 188, 212, 0.7), transparent),
    radial-gradient(1px 1px at 80% 30%, rgba(77, 208, 225, 0.8), transparent),
    radial-gradient(1px 1px at 50% 70%, rgba(144, 202, 249, 0.7), transparent),
    radial-gradient(1px 1px at 30% 60%, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1px 1px at 60% 10%, rgba(0, 229, 255, 0.6), transparent),
    radial-gradient(1px 1px at 90% 80%, rgba(255, 255, 255, 0.8), transparent),
    radial-gradient(1px 1px at 40% 30%, rgba(3, 169, 244, 0.7), transparent);
  background-size: 320px 320px, 420px 420px, 360px 360px, 500px 500px;
  animation: ${driftStars} 70s linear infinite;
  opacity: 0.75;
  mix-blend-mode: screen;
`;

const AuroraLayer = styled.div`
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(0, 188, 212, 0.25), transparent 30%, rgba(26, 115, 232, 0.3));
  filter: blur(80px);
  animation: ${auroraFlow} 20s ease-in-out infinite alternate;
`;

const GridOverlay = styled.div`
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.25;
  mix-blend-mode: overlay;
`;

const FloatingOrbs = styled.div`
  position: absolute;
  inset: 0;
  pointer-events: none;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const FloatingOrb = styled.span`
  position: absolute;
  width: ${(props) => props.size || 220}px;
  height: ${(props) => props.size || 220}px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 188, 212, 0.55), rgba(2, 10, 26, 0));
  filter: blur(2px);
  animation: ${floatOrb} ${(props) => props.duration || 18}s ease-in-out infinite;
  top: ${(props) => props.top || 'auto'};
  bottom: ${(props) => props.bottom || 'auto'};
  left: ${(props) => props.left || 'auto'};
  right: ${(props) => props.right || 'auto'};
  opacity: 0.4;
`;

const LoginBox = styled.div`
  position: relative;
  width: 420px;
  padding: 48px 44px 40px;
  background: rgba(5, 12, 36, 0.85);
  border-radius: 20px;
  border: 1px solid rgba(0, 188, 212, 0.25);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55), 0 0 60px rgba(0, 188, 212, 0.1);
  backdrop-filter: blur(18px);
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
  animation: ${floatUp} 0.8s ease forwards;

  &::before {
    content: '';
    position: absolute;
    inset: 12px;
    border-radius: 16px;
    border: 1px solid rgba(33, 150, 243, 0.25);
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 20px;
    border: 1px solid rgba(0, 188, 212, 0.4);
    opacity: 0.5;
    animation: ${shimmerBorder} 3s ease-in-out infinite;
    pointer-events: none;
  }
`;

const Form = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 100%;
`;

const Title = styled.h2`
  text-align: center;
  color: #e0f7ff;
  letter-spacing: 0.2em;
  font-size: 24px;
  margin-bottom: 30px;
  text-transform: uppercase;
  background: linear-gradient(90deg, #64b5f6, #00bcd4, #64b5f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

const Input = styled.input`
  width: 100%;
  max-width: 320px;
  padding: 14px 16px;
  margin: 0 auto;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  font-size: 16px;
  color: #e0f7ff;
  background: rgba(7, 19, 54, 0.9);
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.35);
  transition: border 0.2s ease, box-shadow 0.2s ease;

  &::placeholder {
    color: rgba(224, 247, 255, 0.5);
    letter-spacing: 0.05em;
  }

  &:focus {
    outline: none;
    border-color: #00bcd4;
    box-shadow: 0 0 15px rgba(0, 188, 212, 0.4), inset 0 0 20px rgba(0, 0, 0, 0.35);
  }
`;

const Button = styled.button`
  width: 100%;
  max-width: 320px;
  padding: 14px;
  margin: 4px auto 0;
  background: linear-gradient(120deg, #1a73e8, #00bcd4);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.08em;
  cursor: pointer;
  box-shadow: 0 15px 30px rgba(0, 188, 212, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 35px rgba(0, 188, 212, 0.45);
    filter: brightness(1.05);
  }
  &:disabled {
    background: linear-gradient(120deg, rgba(26, 115, 232, 0.5), rgba(0, 188, 212, 0.5));
    box-shadow: none;
    cursor: not-allowed;
  }

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: -30%;
    width: 30%;
    height: 200%;
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-50%) rotate(25deg);
    transition: left 0.4s ease;
  }

  &:hover::after {
    left: 110%;
  }

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center, rgba(255, 255, 255, 0.45), transparent 60%);
    opacity: 0;
    transform: scale(0.3);
    transition: opacity 0.4s ease, transform 0.4s ease;
  }

  &:active::before {
    opacity: 0.5;
    transform: scale(1.4);
    transition: opacity 0.2s ease, transform 0.2s ease;
  }
`;

const ErrorMessage = styled.div`
  color: #ff8a80;
  text-align: center;
  margin: 10px 0;
  font-size: 14px;
`;

const LoadingSpinner = styled.div`
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top: 3px solid #00bcd4;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
  
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
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
        history.push('/admin');  // 管理员跳转到后台管理页面
      } else {
        history.push('/index');  // 操作员和访客都跳转到展示平台
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
      <StarField />
      <AuroraLayer />
      <GridOverlay />
      <FloatingOrbs>
        <FloatingOrb size={260} duration={22} top="18%" left="12%" />
        <FloatingOrb size={180} duration={16} bottom="15%" right="10%" />
        <FloatingOrb size={140} duration={14} top="65%" left="28%" />
      </FloatingOrbs>
      <LoginBox>
        <Title>用户登录</Title>
        <Form>
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
        </Form>
      </LoginBox>
    </LoginContainer>
  );
};

export default withRouter(LoginPage);

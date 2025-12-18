import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const TerminalCard = styled.div`
  background: linear-gradient(135deg, rgba(10, 25, 41, 0.95) 0%, rgba(13, 31, 45, 0.95) 100%);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(30, 70, 120, 0.4);
  padding: 16px;
  color: #e3f2fd;
`;

const Title = styled.h3`
  margin: 0 0 8px 0;
  color: #bcddff;
`;

const Output = styled.pre`
  background: rgba(8, 18, 32, 0.8);
  border: 1px solid rgba(90, 143, 196, 0.35);
  border-radius: 8px;
  padding: 12px;
  height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  color: #d0e7ff;
`;

const InputRow = styled.div`
  display: flex;
  gap: 8px;
`;

const CmdInput = styled.input`
  flex: 1;
  background: rgba(8, 18, 32, 0.8);
  border: 1px solid rgba(90, 143, 196, 0.35);
  border-radius: 8px;
  padding: 10px 12px;
  color: #ffffff;
  outline: none;
  &:focus { border-color: rgba(90, 143, 196, 0.8); box-shadow: 0 0 0 3px rgba(90, 143, 196, 0.15);} 
`;

const Btn = styled.button`
  padding: 10px 16px;
  background: linear-gradient(90deg, #0f3057, rgba(15,48,87,0.9));
  color: #fff;
  border: 1px solid rgba(90,143,196,0.5);
  border-radius: 8px;
  cursor: pointer;
  min-width: 96px;
`;

const Note = styled.div`
  color: #8fb6e6;
  font-size: 12px;
`;

const TechControl = () => {
  const [command, setCommand] = useState('');
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const outRef = useRef(null);

  const run = async () => {
    if (!command.trim() || busy) return;
    setBusy(true);
    const cmd = command;
    setCommand('');
    try {
      const res = await axios.post('http://localhost:8000/api/terminal/exec', {
        command: cmd,
        timeout_seconds: 15
      });
      const data = res.data || {};
      const block = `> ${cmd}\n${data.stdout || ''}${data.stderr ? `\n[stderr]\n${data.stderr}` : ''}\n[exit ${data.return_code}]\n`;
      setHistory(prev => [...prev, block]);
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || '执行失败';
      setHistory(prev => [...prev, `> ${cmd}\n[error] ${msg}\n`]);
    } finally {
      setBusy(false);
      setTimeout(() => { if (outRef.current) outRef.current.scrollTop = outRef.current.scrollHeight; }, 0);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      run();
    }
  };

  return (
    <Wrapper>
      <TerminalCard>
        <Title>技术操控 · 限制型命令行</Title>
        <Note>仅用于本机受限调试命令。系统已拦截危险命令，单次执行有超时限制。</Note>
        <Output ref={outRef}>{history.join('\n')}</Output>
        <InputRow>
          <CmdInput
            placeholder={busy ? '执行中...' : '输入命令后回车或点击运行，例如：dir 或 ls -la'}
            value={command}
            onChange={e => setCommand(e.target.value)}
            onKeyDown={onKey}
            disabled={busy}
          />
          <Btn onClick={run} disabled={busy}>{busy ? '运行中' : '运行'}</Btn>
        </InputRow>
      </TerminalCard>
    </Wrapper>
  );
};

export default TechControl;

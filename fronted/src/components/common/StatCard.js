import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: ${props => props.background || '#1a237e'};
  padding: 24px;
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 140px;
  text-align: center;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  }
`;

const Title = styled.div`
  font-size: 16px;
  opacity: 0.85;
  margin-bottom: 12px;
`;

const Value = styled.div`
  font-size: 36px;
  font-weight: 600;
  margin-bottom: 12px;
`;

const Trend = styled.div`
  font-size: 14px;
  opacity: 0.9;
`;

const StatCard = ({ title, value, trend, background }) => {
  return (
    <Card background={background}>
      <Title>{title}</Title>
      <Value>{value}</Value>
      <Trend>{trend}</Trend>
    </Card>
  );
};

export default StatCard; 
import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: ${props => props.background || '#1a237e'};
  padding: 20px;
  border-radius: 10px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-5px);
  }
`;

const Title = styled.div`
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 10px;
`;

const Value = styled.div`
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 10px;
`;

const Trend = styled.div`
  font-size: 14px;
  opacity: 0.8;
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
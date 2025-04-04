import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: ${props => props.theme.colors.background};
  padding: 20px;
`;

const Card = styled.div`
  background: ${props => props.theme.colors.white};
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  text-align: center;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.black};
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
`;

const Message = styled.p`
  color: ${props => props.theme.colors.black};
  margin-bottom: 30px;
  line-height: 1.6;
`;

const StatusIcon = styled.div`
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  border-radius: 50%;
  background-color: ${props => props.theme.colors.primary};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 40px;
`;

const VerificationPending = () => {
  return (
    <Container>
      <Card>
        <StatusIcon>⌛</StatusIcon>
        <Title>Identity Verification in Progress</Title>
        <Message>
          Your account is currently pending verification by our team. This process may take 24-48 hours.
          We will notify you via email once your account has been verified.
        </Message>
        <Message>
          Please check your email for the verification confirmation before attempting to log in.
        </Message>
      </Card>
    </Container>
  );
};

export default VerificationPending; 
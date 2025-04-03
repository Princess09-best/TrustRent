import React from 'react';
import Register from './Register';
import styled from 'styled-components';

const AppContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background-color: ${props => props.theme.colors.background};
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 30px;
  font-size: 2.5rem;
  font-weight: 600;
`;

function App() {
  return (
    <AppContainer>
      <Title>TrustRent</Title>
      <Register />
    </AppContainer>
  );
}

export default App;

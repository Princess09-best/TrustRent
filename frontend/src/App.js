import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Register from './Register';
import Login from './Login';
import VerificationPending from './VerificationPending';
import AdminVerifyUsers from './AdminVerifyUserPage';
import CreateProperty from './OwnerCreateProperty';
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
    <Router>
      <AppContainer>
        <Title>TrustRent</Title>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/verification-pending" element={<VerificationPending />} />
          <Route path="/admin/verify-users" element={<AdminVerifyUsers />} />
          <Route path="/create-property" element={<CreateProperty />} />
          <Route path="/" element={<Navigate to="/register" replace />} />
        </Routes>
      </AppContainer>
    </Router>
  );
}

export default App;

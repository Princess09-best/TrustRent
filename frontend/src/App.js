import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Register from './Register';
import Login from './Login';
import VerificationPending from './VerificationPending';
import AdminVerifyUsers from './AdminVerifyUserPage';
import AdminCreateAccount from './AdminCreateAccount';
import CreateProperty from './OwnerCreateProperty';
import LandRepManageProperties from './LandRepManageProperties';
import PropertyDetails from './PropertyDetails';
import RentalAgreementCreate from './RentalAgreementCreate';
import RentalAgreementDetails from './RentalAgreementDetails';
import RentalAgreementList from './RentalAgreementList';
import BlockchainVerification from './BlockchainVerification';
import Dashboard from './Dashboard';
import Navbar from './Navbar';
import LandingPage from './LandingPage';
import styled from 'styled-components';

const AppContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: ${props => props.theme.colors.background};
`;

const ContentContainer = styled.div`
  width: 100%;
  max-width: 1200px;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

function App() {
  // Check if user is on landing page to hide the navbar
  const isLandingPage = window.location.pathname === '/';
  
  // Check if user is authenticated
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <Router>
      <AppContainer>
        {/* Only show navbar if not on landing page AND authenticated */}
        {!isLandingPage && isAuthenticated && <Navbar />}
        
        <ContentContainer>
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/verification-pending" element={<VerificationPending />} />
            
            {/* Dashboard - Protected Route */}
            <Route 
              path="/dashboard" 
              element={isAuthenticated ? <Dashboard /> : <Login />} 
            />
            
            {/* Admin Routes - Protected */}
            <Route 
              path="/admin/verify-users" 
              element={isAuthenticated ? <AdminVerifyUsers /> : <Login />} 
            />
            <Route 
              path="/admin/create-account" 
              element={isAuthenticated ? <AdminCreateAccount /> : <Login />} 
            />
            <Route 
              path="/admin/blockchain-verification" 
              element={isAuthenticated ? <BlockchainVerification /> : <Login />} 
            />
            
            {/* Land Representative Routes - Protected */}
            <Route 
              path="/land-rep/manage-properties" 
              element={isAuthenticated ? <LandRepManageProperties /> : <Login />} 
            />
            
            {/* Property Routes - Protected */}
            <Route 
              path="/create-property" 
              element={isAuthenticated ? <CreateProperty /> : <Login />} 
            />
            <Route 
              path="/property/:propertyId" 
              element={isAuthenticated ? <PropertyDetails /> : <Login />} 
            />
            
            {/* Rental Agreement Routes - Protected */}
            <Route 
              path="/rental-agreements" 
              element={isAuthenticated ? <RentalAgreementList /> : <Login />} 
            />
            <Route 
              path="/rental-agreements/create" 
              element={isAuthenticated ? <RentalAgreementCreate /> : <Login />} 
            />
            <Route 
              path="/rental-agreements/:agreementId" 
              element={isAuthenticated ? <RentalAgreementDetails /> : <Login />} 
            />
            
            {/* Landing Page as Homepage */}
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </ContentContainer>
      </AppContainer>
    </Router>
  );
}

export default App;

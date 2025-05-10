import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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

// DEVELOPMENT MODE - Set to false for production
const isDevelopment = true;

function App() {
  // For development, we can set a mock user role
  const [devRole, setDevRole] = useState('property_owner');

  return (
    <Router>
      <AppContainer>
        {isDevelopment ? (
          // Development mode with role selector
          <div style={{ width: '100%', padding: '10px 0', backgroundColor: '#ff6b6b', color: 'white', textAlign: 'center' }}>
            <span style={{ marginRight: '10px' }}>DEVELOPMENT MODE</span>
            <select 
              value={devRole} 
              onChange={(e) => setDevRole(e.target.value)}
              style={{ padding: '5px', borderRadius: '4px' }}
            >
              <option value="admin">Admin</option>
              <option value="land_rep">Land Representative</option>
              <option value="property_owner">Property Owner</option>
              <option value="property_seeker">Property Seeker</option>
            </select>
          </div>
        ) : null}
        
        {/* Only show navbar if in dev mode or authenticated in production */}
        <Navbar devMode={isDevelopment} devRole={devRole} />
        
        <ContentContainer>
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/verification-pending" element={<VerificationPending />} />
            
            {/* Dashboard */}
            <Route path="/dashboard" element={<Dashboard devMode={isDevelopment} devRole={devRole} />} />
            
            {/* Admin Routes */}
            <Route path="/admin/verify-users" element={<AdminVerifyUsers />} />
            <Route path="/admin/create-account" element={<AdminCreateAccount />} />
            <Route path="/admin/blockchain-verification" element={<BlockchainVerification />} />
            
            {/* Land Representative Routes */}
            <Route path="/land-rep/manage-properties" element={<LandRepManageProperties />} />
            
            {/* Property Routes */}
            <Route path="/create-property" element={<CreateProperty />} />
            <Route path="/property/:propertyId" element={<PropertyDetails />} />
            
            {/* Rental Agreement Routes */}
            <Route path="/rental-agreements" element={<RentalAgreementList />} />
            <Route path="/rental-agreements/create" element={<RentalAgreementCreate />} />
            <Route path="/rental-agreements/:agreementId" element={<RentalAgreementDetails />} />
            
            <Route path="/" element={<Navigate to={isDevelopment ? "/dashboard" : "/login"} replace />} />
          </Routes>
        </ContentContainer>
      </AppContainer>
    </Router>
  );
}

export default App;

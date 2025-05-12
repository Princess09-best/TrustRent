import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
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
import AuthProvider from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

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

// NavbarWrapper to handle navbar visibility
const NavbarWrapper = ({ devMode, devRole }) => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';
  
  return !isLandingPage && <Navbar devMode={devMode} devRole={devRole} />;
};

function App() {
  // For development, we can set a mock user role
  const [devRole, setDevRole] = useState('property_owner');

  return (
    <AuthProvider>
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
          
          {/* Using NavbarWrapper for dynamic navbar visibility */}
          <NavbarWrapper devMode={isDevelopment} devRole={devRole} />
          
          <ContentContainer>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/verification-pending" element={<VerificationPending />} />
              
              {/* Protected routes - accessible to any authenticated user */}
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard devMode={isDevelopment} devRole={devRole} />
                </ProtectedRoute>
              } />
              
              {/* Admin Routes - only accessible to admin users */}
              <Route path="/admin/verify-users" element={
                <ProtectedRoute requiredRoles={['admin', 'sys_admin']}>
                  <AdminVerifyUsers />
                </ProtectedRoute>
              } />
              
              <Route path="/admin/create-account" element={
                <ProtectedRoute requiredRoles={['admin', 'sys_admin']}>
                  <AdminCreateAccount />
                </ProtectedRoute>
              } />
              
              <Route path="/admin/blockchain-verification" element={
                <ProtectedRoute requiredRoles={['admin', 'sys_admin']}>
                  <BlockchainVerification />
                </ProtectedRoute>
              } />
              
              {/* Land Representative Routes */}
              <Route path="/land-rep/manage-properties" element={
                <ProtectedRoute requiredRoles={['land_rep', 'admin', 'sys_admin']}>
                  <LandRepManageProperties />
                </ProtectedRoute>
              } />
              
              {/* Property Routes */}
              <Route path="/create-property" element={
                <ProtectedRoute requiredRoles={['property_owner']}>
                  <CreateProperty />
                </ProtectedRoute>
              } />
              
              <Route path="/property/:propertyId" element={
                <ProtectedRoute>
                  <PropertyDetails />
                </ProtectedRoute>
              } />
              
              {/* Rental Agreement Routes */}
              <Route path="/rental-agreements" element={
                <ProtectedRoute>
                  <RentalAgreementList />
                </ProtectedRoute>
              } />
              
              <Route path="/rental-agreements/create" element={
                <ProtectedRoute requiredRoles={['property_owner']}>
                  <RentalAgreementCreate />
                </ProtectedRoute>
              } />
              
              <Route path="/rental-agreements/:agreementId" element={
                <ProtectedRoute>
                  <RentalAgreementDetails />
                </ProtectedRoute>
              } />
              
              {/* Catch all other routes and redirect to dashboard for authenticated users, otherwise to landing page */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ContentContainer>
        </AppContainer>
      </Router>
    </AuthProvider>
  );
}

export default App;

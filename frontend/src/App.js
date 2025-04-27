import React from 'react';
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

function App() {
  return (
    <Router>
      <AppContainer>
        <Navbar />
        <ContentContainer>
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/verification-pending" element={<VerificationPending />} />
            
            {/* Admin Routes */}
            <Route path="/admin/verify-users" element={<AdminVerifyUsers />} />
            <Route path="/admin/create-account" element={<AdminCreateAccount />} />
            
            {/* Land Representative Routes */}
            <Route path="/land-rep/manage-properties" element={<LandRepManageProperties />} />
            
            {/* Property Routes */}
            <Route path="/create-property" element={<CreateProperty />} />
            <Route path="/property/:propertyId" element={<PropertyDetails />} />
            
            {/* Rental Agreement Routes */}
            <Route path="/rental-agreements" element={<RentalAgreementList />} />
            <Route path="/rental-agreements/create" element={<RentalAgreementCreate />} />
            <Route path="/rental-agreements/:agreementId" element={<RentalAgreementDetails />} />
            
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </ContentContainer>
      </AppContainer>
    </Router>
  );
}

export default App;

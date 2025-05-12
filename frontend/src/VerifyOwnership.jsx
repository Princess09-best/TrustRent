import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
`;

const PageHeader = styled.div`
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
  padding-bottom: 20px;
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  font-size: 2rem;
  margin-bottom: 10px;
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 1.1rem;
  line-height: 1.5;
`;

const FormSection = styled.div`
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 10px;
`;

const SectionTitle = styled.h3`
  color: ${props => props.theme.colors.primary};
  font-size: 1.4rem;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: ${props => props.theme.colors.text};
`;

const FormInput = styled.input`
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
`;

const FormSelect = styled.select`
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
`;

const Button = styled.button`
  background-color: ${props => props.variant === 'secondary' 
    ? '#6c757d' 
    : props.theme.colors.primary};
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 15px;
  margin-top: 30px;
`;

const ResultContainer = styled.div`
  margin-top: 30px;
  padding: 20px;
  border-radius: 10px;
  background-color: ${props => props.success ? '#e8f5e9' : '#ffebee'};
  border-left: 5px solid ${props => props.success ? '#4caf50' : '#f44336'};
`;

const ResultTitle = styled.h3`
  color: ${props => props.success ? '#2e7d32' : '#c62828'};
  margin-bottom: 15px;
`;

const ResultDetail = styled.div`
  margin-bottom: 10px;
  line-height: 1.6;
`;

const PropertyDetail = styled.div`
  display: flex;
  margin-bottom: 8px;
`;

const PropertyLabel = styled.span`
  font-weight: 600;
  width: 150px;
`;

const PropertyValue = styled.span`
  flex: 1;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
  
  &:after {
    content: " ";
    display: block;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 6px solid ${props => props.theme.colors.primary};
    border-color: ${props => props.theme.colors.primary} transparent;
    animation: spinner 1.2s linear infinite;
  }
  
  @keyframes spinner {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const ErrorMessage = styled.div`
  color: #f44336;
  background-color: #ffebee;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
`;

function VerifyOwnership() {
  const navigate = useNavigate();
  const { isAuthenticated, userRole } = useAuth();
  
  const [propertyDetails, setPropertyDetails] = useState({
    property_title: '',
    property_location: '',
    property_type: '1_bedroom'
  });
  
  const [ownerDetails, setOwnerDetails] = useState({
    owner_name: '',
    owner_id_type: 'Ghana Card',
    owner_id_value: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [verificationId, setVerificationId] = useState(null);
  
  const propertyTypes = [
    { value: '1_bedroom', label: '1 Bedroom' },
    { value: '2_bedroom', label: '2 Bedroom' },
    { value: '3_bedroom', label: '3 Bedroom' },
    { value: 'studio', label: 'Studio' },
    { value: 'apartment', label: 'Apartment' },
    { value: 'house', label: 'House' }
  ];
  
  const idTypes = [
    { value: 'Ghana Card', label: 'Ghana Card' },
    { value: 'Passport', label: 'Passport' }
  ];
  
  const handlePropertyChange = (e) => {
    const { name, value } = e.target;
    setPropertyDetails(prev => ({ ...prev, [name]: value }));
  };
  
  const handleOwnerChange = (e) => {
    const { name, value } = e.target;
    setOwnerDetails(prev => ({ ...prev, [name]: value }));
  };
  
  const handleVerify = async () => {
    try {
      setLoading(true);
      setError('');
      setVerificationResult(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      // First, create a verification request
      const createResponse = await axios.post('/api/trustchain/verify/create/', {
        ...propertyDetails,
        ...ownerDetails
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Verification request created:', createResponse.data);
      
      // Store verification ID
      const verification_id = createResponse.data.verification.verification_id;
      setVerificationId(verification_id);
      
      // Execute the verification
      const executeResponse = await axios.post(`/api/trustchain/verify/${verification_id}/execute/`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Verification executed:', executeResponse.data);
      
      // Get verification status
      const statusResponse = await axios.get(`/api/trustchain/verify/${verification_id}/status/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Verification status:', statusResponse.data);
      
      if (statusResponse.data && statusResponse.data.details) {
        setVerificationStatus(statusResponse.data.details);
        setVerificationResult(statusResponse.data.details.verification_data);
      } else {
        setError('Failed to get verification status. Please try again or check status later.');
      }
      
    } catch (err) {
      console.error('Error verifying ownership:', err);
      if (err.response) {
        setError(`Verification failed: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to verify ownership. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleCheckStatus = async () => {
    if (!verificationId) return;
    
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.get(`/api/trustchain/verify/${verificationId}/status/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Updated verification status:', response.data);
      
      if (response.data && response.data.details) {
        setVerificationStatus(response.data.details);
        setVerificationResult(response.data.details.verification_data);
      } else {
        setError('Failed to get verification status. Please try again.');
      }
      
    } catch (err) {
      console.error('Error checking verification status:', err);
      if (err.response) {
        setError(`Failed to check status: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to check verification status. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container>
      <PageHeader>
        <Title>Verify Property Ownership</Title>
        <Subtitle>
          Use blockchain technology to verify if a claimed property owner truly owns the property.
          This verification uses smart contracts to check the property ledger.
        </Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <FormSection>
        <SectionTitle>Property Details</SectionTitle>
        <FormGroup>
          <FormLabel>Property Title</FormLabel>
          <FormInput 
            type="text" 
            name="property_title"
            value={propertyDetails.property_title}
            onChange={handlePropertyChange}
            placeholder="Enter the exact property title"
            required
          />
        </FormGroup>
        
        <FormGroup>
          <FormLabel>Property Location</FormLabel>
          <FormInput 
            type="text" 
            name="property_location"
            value={propertyDetails.property_location}
            onChange={handlePropertyChange}
            placeholder="Enter the property location (e.g., East Legon, Accra)"
            required
          />
        </FormGroup>
        
        <FormGroup>
          <FormLabel>Property Type</FormLabel>
          <FormSelect 
            name="property_type"
            value={propertyDetails.property_type}
            onChange={handlePropertyChange}
            required
          >
            {propertyTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </FormSelect>
        </FormGroup>
      </FormSection>
      
      <FormSection>
        <SectionTitle>Claimed Owner Details</SectionTitle>
        <FormGroup>
          <FormLabel>Owner Full Name</FormLabel>
          <FormInput 
            type="text" 
            name="owner_name"
            value={ownerDetails.owner_name}
            onChange={handleOwnerChange}
            placeholder="Enter the full name of the claimed owner"
            required
          />
        </FormGroup>
        
        <FormGroup>
          <FormLabel>ID Type</FormLabel>
          <FormSelect 
            name="owner_id_type"
            value={ownerDetails.owner_id_type}
            onChange={handleOwnerChange}
            required
          >
            {idTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </FormSelect>
        </FormGroup>
        
        <FormGroup>
          <FormLabel>ID Number</FormLabel>
          <FormInput 
            type="text" 
            name="owner_id_value"
            value={ownerDetails.owner_id_value}
            onChange={handleOwnerChange}
            placeholder={ownerDetails.owner_id_type === 'Ghana Card' ? 'Format: GHA-XXXXXXXXX-X' : 'Format: LXXXXXXX'}
            required
          />
        </FormGroup>
      </FormSection>
      
      <ButtonGroup>
        <Button onClick={handleVerify} disabled={loading}>
          {loading ? 'Processing...' : 'Verify Ownership'}
        </Button>
        {verificationId && (
          <Button variant="secondary" onClick={handleCheckStatus} disabled={loading}>
            Check Status
          </Button>
        )}
      </ButtonGroup>
      
      {loading && <LoadingSpinner />}
      
      {verificationResult && (
        <ResultContainer success={verificationResult.is_owner}>
          <ResultTitle success={verificationResult.is_owner}>
            {verificationResult.is_owner 
              ? 'Ownership Verified ✓' 
              : 'Ownership Not Verified ✗'}
          </ResultTitle>
          
          <ResultDetail>
            {verificationResult.is_owner 
              ? 'The blockchain records confirm that the claimed owner is indeed the verified owner of this property.' 
              : 'The blockchain records do not confirm the claimed ownership of this property.'}
          </ResultDetail>
          
          {verificationStatus && (
            <div style={{ marginTop: '20px' }}>
              <h4>Property Information:</h4>
              <PropertyDetail>
                <PropertyLabel>Title:</PropertyLabel>
                <PropertyValue>{verificationStatus.property.title}</PropertyValue>
              </PropertyDetail>
              <PropertyDetail>
                <PropertyLabel>Location:</PropertyLabel>
                <PropertyValue>{verificationStatus.property.location}</PropertyValue>
              </PropertyDetail>
              <PropertyDetail>
                <PropertyLabel>Type:</PropertyLabel>
                <PropertyValue>{verificationStatus.property.type}</PropertyValue>
              </PropertyDetail>
              
              <h4>Claimed Owner:</h4>
              <PropertyDetail>
                <PropertyLabel>Name:</PropertyLabel>
                <PropertyValue>{verificationStatus.claimed_owner.name}</PropertyValue>
              </PropertyDetail>
              <PropertyDetail>
                <PropertyLabel>ID Type:</PropertyLabel>
                <PropertyValue>{verificationStatus.claimed_owner.id_type}</PropertyValue>
              </PropertyDetail>
              
              <h4>Verification Details:</h4>
              <PropertyDetail>
                <PropertyLabel>Verification ID:</PropertyLabel>
                <PropertyValue>{verificationStatus.verification_id}</PropertyValue>
              </PropertyDetail>
              <PropertyDetail>
                <PropertyLabel>Status:</PropertyLabel>
                <PropertyValue>{verificationStatus.status}</PropertyValue>
              </PropertyDetail>
              <PropertyDetail>
                <PropertyLabel>Verified At:</PropertyLabel>
                <PropertyValue>
                  {verificationResult.verified_at 
                    ? new Date(verificationResult.verified_at).toLocaleString() 
                    : 'Not yet verified'}
                </PropertyValue>
              </PropertyDetail>
            </div>
          )}
        </ResultContainer>
      )}
    </Container>
  );
}

export default VerifyOwnership; 
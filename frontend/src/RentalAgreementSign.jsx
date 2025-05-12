import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import { useAuth } from './context/AuthContext';

const Container = styled.div`
  max-width: 1000px;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  font-size: 2rem;
  margin-bottom: 10px;
`;

const StatusBadge = styled.span`
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  background-color: ${props => {
    switch(props.status?.toLowerCase()) {
      case 'active': return '#e8f5e9';
      case 'pending': return '#fff8e1';
      case 'terminated': return '#ffebee';
      case 'completed': return '#e0f7fa';
      case 'cancelled': return '#f5f5f5';
      default: return '#f5f5f5';
    }
  }};
  color: ${props => {
    switch(props.status?.toLowerCase()) {
      case 'active': return '#2e7d32';
      case 'pending': return '#f57c00';
      case 'terminated': return '#c62828';
      case 'completed': return '#0277bd';
      case 'cancelled': return '#757575';
      default: return '#757575';
    }
  }};
`;

const Section = styled.div`
  margin-bottom: 30px;
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
`;

const SectionTitle = styled.h3`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 15px;
  font-size: 1.2rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
`;

const DetailRow = styled.div`
  display: flex;
  margin-bottom: 10px;
  padding: 8px 0;
  border-bottom: 1px dashed #eee;
  
  &:last-child {
    border-bottom: none;
  }
`;

const DetailLabel = styled.div`
  width: 200px;
  font-weight: 600;
  color: #555;
`;

const DetailValue = styled.div`
  flex: 1;
`;

const SignatureSection = styled.div`
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
`;

const SignatureStatus = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
`;

const SignatureParty = styled.div`
  flex: 1;
  padding: 15px;
  text-align: center;
  border-right: ${props => props.isLast ? 'none' : '1px solid #ddd'};
`;

const SignatureIndicator = styled.div`
  margin-top: 10px;
  padding: 8px;
  border-radius: 4px;
  background-color: ${props => props.signed ? '#e8f5e9' : '#fff8e1'};
  color: ${props => props.signed ? '#2e7d32' : '#f57c00'};
  font-weight: 600;
`;

const SignatureBox = styled.div`
  margin-top: 20px;
  padding: 20px;
  border: 1px dashed #ccc;
  border-radius: 8px;
  text-align: center;
`;

const SignatureInput = styled.input`
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
`;

const Button = styled.button`
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  background-color: ${props => {
    if (props.variant === 'secondary') return '#f5f5f5';
    if (props.variant === 'danger') return '#ffebee';
    return props.theme.colors.primary;
  }};
  
  color: ${props => {
    if (props.variant === 'secondary') return '#333';
    if (props.variant === 'danger') return '#c62828';
    return 'white';
  }};
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    
    background-color: ${props => {
      if (props.variant === 'secondary') return '#e0e0e0';
      if (props.variant === 'danger') return '#ffcdd2';
      return '#006666';
    }};
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  
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

const SuccessMessage = styled.div`
  color: #2e7d32;
  background-color: #e8f5e9;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
`;

function RentalAgreementSign() {
  const { agreementId } = useParams();
  const navigate = useNavigate();
  const { currentUser, userRole } = useAuth();
  
  const [agreement, setAgreement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [signatureText, setSignatureText] = useState('');
  const [processing, setProcessing] = useState(false);
  
  useEffect(() => {
    fetchAgreement();
  }, [agreementId]);
  
  const fetchAgreement = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.get(`/api/trustchain/rental/${agreementId}/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setAgreement(response.data);
    } catch (err) {
      console.error('Error fetching agreement:', err);
      setError('Failed to load rental agreement. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSign = async () => {
    try {
      if (!signatureText.trim()) {
        setError('Please type your full name to sign the agreement');
        return;
      }
      
      setProcessing(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.post(`/api/trustchain/rental/${agreementId}/sign/`, {
        signature_text: signatureText
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setSuccess('Agreement signed successfully!');
      
      // Update the local agreement state
      if (userRole === 'property_owner') {
        setAgreement({
          ...agreement,
          owner_signature: {
            is_signed: true,
            signature_date: new Date().toISOString()
          },
          status: agreement.tenant_signature?.is_signed ? 'active' : 'pending'
        });
      } else {
        setAgreement({
          ...agreement,
          tenant_signature: {
            is_signed: true,
            signature_date: new Date().toISOString()
          },
          status: agreement.owner_signature?.is_signed ? 'active' : 'pending'
        });
      }
      
      // Clear signature text
      setSignatureText('');
      
      // Refresh agreement data after a short delay
      setTimeout(() => {
        fetchAgreement();
      }, 1000);
      
    } catch (err) {
      console.error('Error signing agreement:', err);
      if (err.response) {
        setError(`Failed to sign: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to sign agreement. Please try again.');
      }
    } finally {
      setProcessing(false);
    }
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };
  
  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };
  
  if (loading) {
    return (
      <Container>
        <LoadingSpinner />
      </Container>
    );
  }
  
  if (!agreement) {
    return (
      <Container>
        <Title>Agreement Not Found</Title>
        <ErrorMessage>The requested rental agreement could not be found or you don't have permission to view it.</ErrorMessage>
        <ButtonGroup>
          <Button onClick={() => navigate('/rental-agreements')}>Back to Agreements</Button>
        </ButtonGroup>
      </Container>
    );
  }
  
  const isOwner = userRole === 'property_owner';
  const isTenant = userRole === 'property_seeker';
  
  const canSign = agreement.status === 'pending' && (
    (isOwner && !agreement.owner_signature?.is_signed) ||
    (isTenant && !agreement.tenant_signature?.is_signed)
  );
  
  return (
    <Container>
      <PageHeader>
        <div>
          <Title>Rental Agreement</Title>
          <p>Agreement ID: {agreement.agreement_id}</p>
        </div>
        <StatusBadge status={agreement.status}>
          {agreement.status}
        </StatusBadge>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      
      <Section>
        <SectionTitle>Property Details</SectionTitle>
        <DetailRow>
          <DetailLabel>Property:</DetailLabel>
          <DetailValue>{agreement.property?.title || 'N/A'}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Location:</DetailLabel>
          <DetailValue>{agreement.property?.location || 'N/A'}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Type:</DetailLabel>
          <DetailValue>{agreement.property?.type || 'N/A'}</DetailValue>
        </DetailRow>
      </Section>
      
      <Section>
        <SectionTitle>Agreement Details</SectionTitle>
        <DetailRow>
          <DetailLabel>Start Date:</DetailLabel>
          <DetailValue>{formatDate(agreement.dates?.start_date)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>End Date:</DetailLabel>
          <DetailValue>{formatDate(agreement.dates?.end_date)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Monthly Rent:</DetailLabel>
          <DetailValue>{formatCurrency(agreement.financial?.monthly_rent)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Security Deposit:</DetailLabel>
          <DetailValue>{formatCurrency(agreement.financial?.security_deposit)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Created On:</DetailLabel>
          <DetailValue>{formatDate(agreement.dates?.created_at)}</DetailValue>
        </DetailRow>
      </Section>
      
      <Section>
        <SectionTitle>Parties</SectionTitle>
        <DetailRow>
          <DetailLabel>Property Owner:</DetailLabel>
          <DetailValue>{agreement.owner?.name || 'N/A'} ({agreement.owner?.email || 'N/A'})</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Tenant:</DetailLabel>
          <DetailValue>{agreement.tenant?.name || 'N/A'} ({agreement.tenant?.email || 'N/A'})</DetailValue>
        </DetailRow>
      </Section>
      
      <SignatureSection>
        <SectionTitle>Signatures</SectionTitle>
        <SignatureStatus>
          <SignatureParty>
            <h4>Property Owner</h4>
            <SignatureIndicator signed={agreement.signatures?.owner_signed}>
              {agreement.signatures?.owner_signed 
                ? `Signed on ${formatDate(agreement.dates?.signature_date_owner)}` 
                : 'Not Signed'}
            </SignatureIndicator>
          </SignatureParty>
          
          <SignatureParty isLast>
            <h4>Tenant</h4>
            <SignatureIndicator signed={agreement.signatures?.tenant_signed}>
              {agreement.signatures?.tenant_signed 
                ? `Signed on ${formatDate(agreement.dates?.signature_date_tenant)}` 
                : 'Not Signed'}
            </SignatureIndicator>
          </SignatureParty>
        </SignatureStatus>
        
        {canSign && (
          <SignatureBox>
            <h4>Sign Agreement</h4>
            <p>Please type your full name below to sign this agreement:</p>
            <SignatureInput
              type="text"
              value={signatureText}
              onChange={(e) => setSignatureText(e.target.value)}
              placeholder="Type your full name"
            />
            <Button 
              onClick={handleSign}
              disabled={processing || !signatureText.trim()}
            >
              {processing ? 'Processing...' : 'Sign Agreement'}
            </Button>
          </SignatureBox>
        )}
      </SignatureSection>
      
      <ButtonGroup>
        <Button 
          variant="secondary"
          onClick={() => navigate('/rental-agreements')}
        >
          Back to Agreements
        </Button>
      </ButtonGroup>
    </Container>
  );
}

export default RentalAgreementSign; 
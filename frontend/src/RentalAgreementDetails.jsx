import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const StatusBadge = styled.span`
  font-size: 14px;
  padding: 5px 10px;
  border-radius: 20px;
  background-color: ${props => {
    switch (props.status) {
      case 'PENDING': return '#FFF8E1';
      case 'ACTIVE': return '#E8F5E9';
      case 'TERMINATED': return '#FFEBEE';
      case 'EXPIRED': return '#ECEFF1';
      default: return '#E0E0E0';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'PENDING': return '#FF8F00';
      case 'ACTIVE': return '#2E7D32';
      case 'TERMINATED': return '#C62828';
      case 'EXPIRED': return '#546E7A';
      default: return '#757575';
    }
  }};
`;

const Section = styled.div`
  margin-bottom: 25px;
`;

const SectionTitle = styled.h3`
  color: ${props => props.theme.colors.black};
  margin-bottom: 10px;
  font-size: 18px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  padding-bottom: 5px;
`;

const DetailRow = styled.div`
  display: flex;
  margin-bottom: 10px;
  flex-wrap: wrap;
`;

const DetailLabel = styled.div`
  width: 180px;
  font-weight: 500;
  color: #555;
`;

const DetailValue = styled.div`
  flex: 1;
`;

const SignatureSection = styled.div`
  margin-top: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  border: 1px solid ${props => props.theme.colors.border};
`;

const SignatureStatus = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
`;

const SignatureParty = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 45%;
`;

const SignatureIndicator = styled.div`
  width: 100%;
  padding: 10px;
  border-radius: 4px;
  text-align: center;
  background-color: ${props => props.signed ? '#E8F5E9' : '#FFEBEE'};
  color: ${props => props.signed ? '#2E7D32' : '#C62828'};
  margin-top: 5px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
  margin-top: 20px;
`;

const Button = styled.button`
  padding: 12px 20px;
  background-color: ${props => props.variant === 'danger' 
    ? props.theme.colors.error 
    : props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: ${props => props.variant === 'danger' ? '#a30000' : '#006666'};
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.p`
  color: ${props => props.theme.colors.error};
  margin-top: 5px;
  font-size: 14px;
`;

const SuccessMessage = styled.p`
  color: ${props => props.theme.colors.success};
  margin-top: 15px;
  padding: 10px;
  background-color: rgba(0, 128, 128, 0.1);
  border-radius: 4px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
`;

function RentalAgreementDetails() {
  const { agreementId } = useParams();
  const navigate = useNavigate();
  const [agreement, setAgreement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [userRole, setUserRole] = useState('');
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch('/api/users/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user information');
        }

        const data = await response.json();
        setUserRole(data.role);
        setUserId(data.id);
      } catch (err) {
        console.error('Error fetching user info:', err);
        setError('Failed to load user information');
      }
    };

    const fetchAgreement = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch(`/api/trustchain/rental/${agreementId}/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch rental agreement');
        }

        const data = await response.json();
        setAgreement(data);
      } catch (err) {
        setError('Failed to load rental agreement. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo();
    fetchAgreement();
  }, [agreementId, navigate]);

  const handleSign = async () => {
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`/api/trustchain/rental/${agreementId}/sign/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign rental agreement');
      }

      const data = await response.json();
      setSuccess('Rental agreement signed successfully!');
      
      // Update the agreement data
      setAgreement(prevState => {
        if (userRole === 'property_owner') {
          return {
            ...prevState,
            owner_signature: {
              ...prevState.owner_signature,
              is_signed: true,
              signature_date: new Date().toISOString()
            }
          };
        } else {
          return {
            ...prevState,
            tenant_signature: {
              ...prevState.tenant_signature,
              is_signed: true,
              signature_date: new Date().toISOString()
            }
          };
        }
      });
    } catch (err) {
      setError(err.message || 'Failed to sign rental agreement. Please try again.');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTerminate = async () => {
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const reason = prompt('Please provide a reason for termination:');
      if (!reason) {
        setActionLoading(false);
        return;
      }

      const response = await fetch(`/api/trustchain/rental/${agreementId}/terminate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ reason })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to terminate rental agreement');
      }

      setSuccess('Rental agreement terminated successfully!');
      
      // Update the agreement status
      setAgreement(prevState => ({
        ...prevState,
        status: 'TERMINATED',
        termination_details: {
          terminated_by: userId,
          termination_date: new Date().toISOString(),
          reason: reason
        }
      }));
    } catch (err) {
      setError(err.message || 'Failed to terminate rental agreement. Please try again.');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
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
        <LoadingSpinner>Loading rental agreement details...</LoadingSpinner>
      </Container>
    );
  }

  if (!agreement) {
    return (
      <Container>
        <Title>Rental Agreement Not Found</Title>
        <ErrorMessage>
          The requested rental agreement could not be found or you don't have permission to view it.
        </ErrorMessage>
        <Button onClick={() => navigate('/rental-agreements')}>Back to Agreements</Button>
      </Container>
    );
  }

  const canSign = agreement.status === 'PENDING' && (
    (userRole === 'property_owner' && !agreement.owner_signature.is_signed) ||
    (userRole === 'property_seeker' && !agreement.tenant_signature.is_signed)
  );

  const canTerminate = agreement.status === 'ACTIVE' && userRole === 'property_owner';

  return (
    <Container>
      <Title>
        Rental Agreement 
        <StatusBadge status={agreement.status}>{agreement.status}</StatusBadge>
      </Title>

      <Section>
        <SectionTitle>Agreement Details</SectionTitle>
        <DetailRow>
          <DetailLabel>Agreement ID:</DetailLabel>
          <DetailValue>{agreement.agreement_id}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Created Date:</DetailLabel>
          <DetailValue>{formatDate(agreement.created_at)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Start Date:</DetailLabel>
          <DetailValue>{formatDate(agreement.start_date)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>End Date:</DetailLabel>
          <DetailValue>{formatDate(agreement.end_date)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Monthly Rent:</DetailLabel>
          <DetailValue>{formatCurrency(agreement.monthly_rent)}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Security Deposit:</DetailLabel>
          <DetailValue>{formatCurrency(agreement.security_deposit)}</DetailValue>
        </DetailRow>
      </Section>

      <Section>
        <SectionTitle>Property Details</SectionTitle>
        <DetailRow>
          <DetailLabel>Property ID:</DetailLabel>
          <DetailValue>{agreement.property.id}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Address:</DetailLabel>
          <DetailValue>
            {agreement.property.address}, {agreement.property.city}, {agreement.property.state} {agreement.property.zip_code}
          </DetailValue>
        </DetailRow>
      </Section>

      <Section>
        <SectionTitle>Parties</SectionTitle>
        <DetailRow>
          <DetailLabel>Owner:</DetailLabel>
          <DetailValue>
            {agreement.owner.first_name} {agreement.owner.last_name} ({agreement.owner.email})
          </DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Tenant:</DetailLabel>
          <DetailValue>
            {agreement.tenant.first_name} {agreement.tenant.last_name} ({agreement.tenant.email})
          </DetailValue>
        </DetailRow>
      </Section>

      {agreement.status === 'TERMINATED' && agreement.termination_details && (
        <Section>
          <SectionTitle>Termination Details</SectionTitle>
          <DetailRow>
            <DetailLabel>Terminated By:</DetailLabel>
            <DetailValue>{agreement.termination_details.terminated_by_name}</DetailValue>
          </DetailRow>
          <DetailRow>
            <DetailLabel>Termination Date:</DetailLabel>
            <DetailValue>{formatDate(agreement.termination_details.termination_date)}</DetailValue>
          </DetailRow>
          <DetailRow>
            <DetailLabel>Reason:</DetailLabel>
            <DetailValue>{agreement.termination_details.reason}</DetailValue>
          </DetailRow>
        </Section>
      )}

      <SignatureSection>
        <SectionTitle>Signatures</SectionTitle>
        <SignatureStatus>
          <SignatureParty>
            <DetailLabel>Owner Signature</DetailLabel>
            <SignatureIndicator signed={agreement.owner_signature.is_signed}>
              {agreement.owner_signature.is_signed 
                ? `Signed on ${formatDate(agreement.owner_signature.signature_date)}` 
                : 'Not Signed'}
            </SignatureIndicator>
          </SignatureParty>
          <SignatureParty>
            <DetailLabel>Tenant Signature</DetailLabel>
            <SignatureIndicator signed={agreement.tenant_signature.is_signed}>
              {agreement.tenant_signature.is_signed 
                ? `Signed on ${formatDate(agreement.tenant_signature.signature_date)}` 
                : 'Not Signed'}
            </SignatureIndicator>
          </SignatureParty>
        </SignatureStatus>
      </SignatureSection>

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      <ButtonGroup>
        {canSign && (
          <Button onClick={handleSign} disabled={actionLoading}>
            {actionLoading ? 'Processing...' : 'Sign Agreement'}
          </Button>
        )}
        {canTerminate && (
          <Button variant="danger" onClick={handleTerminate} disabled={actionLoading}>
            {actionLoading ? 'Processing...' : 'Terminate Agreement'}
          </Button>
        )}
        <Button onClick={() => navigate('/rental-agreements')}>
          Back to Agreements
        </Button>
      </ButtonGroup>
    </Container>
  );
}

export default RentalAgreementDetails; 
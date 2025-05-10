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
      case 'VERIFIED': return '#E8F5E9';
      case 'REJECTED': return '#FFEBEE';
      default: return '#E0E0E0';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'PENDING': return '#FF8F00';
      case 'VERIFIED': return '#2E7D32';
      case 'REJECTED': return '#C62828';
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

const ImagesContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 15px;
`;

const PropertyImage = styled.div`
  width: calc(33.333% - 10px);
  height: 150px;
  background-image: url(${props => props.src});
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  cursor: pointer;
  
  @media (max-width: 768px) {
    width: calc(50% - 7.5px);
  }
  
  @media (max-width: 480px) {
    width: 100%;
  }
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

const RejectionReason = styled.div`
  margin-top: 15px;
  padding: 15px;
  background-color: #FFEBEE;
  border-radius: 8px;
  border-left: 4px solid #C62828;
`;

function PropertyDetails() {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch('/api/user/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user information');
        }

        const data = await response.json();
        setUserRole(data.role);
      } catch (err) {
        console.error('Error fetching user info:', err);
        setError('Failed to load user information');
      }
    };

    const fetchProperty = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        let endpoint = `/api/property/${propertyId}/`;
        if (userRole === 'land_rep') {
          endpoint = `/api/land-rep/properties/${propertyId}/`;
        }

        const response = await fetch(endpoint, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch property details');
        }

        const data = await response.json();
        setProperty(data);
      } catch (err) {
        setError('Failed to load property details. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo().then(() => fetchProperty());
  }, [propertyId, navigate, userRole]);

  const handleVerify = async () => {
    if (userRole !== 'land_rep') return;
    
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`/api/land-rep/properties/${propertyId}/verify/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to verify property');
      }

      setSuccess('Property verified successfully!');
      
      // Update the property status
      setProperty(prev => ({
        ...prev,
        verification_status: 'VERIFIED'
      }));
    } catch (err) {
      setError(err.message || 'Failed to verify property. Please try again.');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (userRole !== 'land_rep') return;
    
    setActionLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) {
        setActionLoading(false);
        return;
      }

      const response = await fetch(`/api/land-rep/properties/${propertyId}/reject/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ reason })
      });

      if (!response.ok) {
        throw new Error('Failed to reject property');
      }

      setSuccess('Property rejected successfully!');
      
      // Update the property status
      setProperty(prev => ({
        ...prev,
        verification_status: 'REJECTED',
        rejection_reason: reason
      }));
    } catch (err) {
      setError(err.message || 'Failed to reject property. Please try again.');
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
        <LoadingSpinner>Loading property details...</LoadingSpinner>
      </Container>
    );
  }

  if (!property) {
    return (
      <Container>
        <Title>Property Not Found</Title>
        <ErrorMessage>
          The requested property could not be found or you don't have permission to view it.
        </ErrorMessage>
        <Button onClick={() => navigate(-1)}>Go Back</Button>
      </Container>
    );
  }

  const canVerify = userRole === 'land_rep' && 
    (property.verification_status === 'PENDING' || property.verification_status === 'REJECTED');
  
  const canReject = userRole === 'land_rep' && property.verification_status === 'PENDING';

  return (
    <Container>
      <Title>
        Property Details
        <StatusBadge status={property.verification_status}>
          {property.verification_status}
        </StatusBadge>
      </Title>

      <Section>
        <SectionTitle>Basic Information</SectionTitle>
        <DetailRow>
          <DetailLabel>Property ID:</DetailLabel>
          <DetailValue>{property.id}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Address:</DetailLabel>
          <DetailValue>{property.address}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>City:</DetailLabel>
          <DetailValue>{property.city}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>State:</DetailLabel>
          <DetailValue>{property.state}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Zip Code:</DetailLabel>
          <DetailValue>{property.zip_code}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Property Type:</DetailLabel>
          <DetailValue>{property.property_type}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Bedrooms:</DetailLabel>
          <DetailValue>{property.bedrooms}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Bathrooms:</DetailLabel>
          <DetailValue>{property.bathrooms}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Square Footage:</DetailLabel>
          <DetailValue>{property.square_footage} sq ft</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Listed Price:</DetailLabel>
          <DetailValue>{formatCurrency(property.list_price)}</DetailValue>
        </DetailRow>
      </Section>

      <Section>
        <SectionTitle>Owner Information</SectionTitle>
        <DetailRow>
          <DetailLabel>Owner:</DetailLabel>
          <DetailValue>{property.owner_name}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Email:</DetailLabel>
          <DetailValue>{property.owner_email}</DetailValue>
        </DetailRow>
      </Section>

      {property.verification_status === 'REJECTED' && property.rejection_reason && (
        <RejectionReason>
          <strong>Rejection Reason:</strong> {property.rejection_reason}
        </RejectionReason>
      )}

      {property.images && property.images.length > 0 && (
        <Section>
          <SectionTitle>Property Images</SectionTitle>
          <ImagesContainer>
            {property.images.map((image, index) => (
              <PropertyImage key={index} src={image.url} alt={`Property image ${index + 1}`} />
            ))}
          </ImagesContainer>
        </Section>
      )}

      {property.documents && property.documents.length > 0 && (
        <Section>
          <SectionTitle>Property Documents</SectionTitle>
          {property.documents.map((doc, index) => (
            <DetailRow key={index}>
              <DetailLabel>Document {index + 1}:</DetailLabel>
              <DetailValue>
                <a href={doc.url} target="_blank" rel="noopener noreferrer">
                  {doc.name || `Document ${index + 1}`}
                </a>
              </DetailValue>
            </DetailRow>
          ))}
        </Section>
      )}

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      <ButtonGroup>
        {canVerify && (
          <Button onClick={handleVerify} disabled={actionLoading}>
            {actionLoading ? 'Processing...' : 'Verify Property'}
          </Button>
        )}
        {canReject && (
          <Button variant="danger" onClick={handleReject} disabled={actionLoading}>
            {actionLoading ? 'Processing...' : 'Reject Property'}
          </Button>
        )}
        <Button onClick={() => navigate(-1)}>
          Back
        </Button>
      </ButtonGroup>
    </Container>
  );
}

export default PropertyDetails; 
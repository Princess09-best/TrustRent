import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styled from 'styled-components';
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

const FilterContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const FilterGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

const FilterLabel = styled.label`
  font-weight: 600;
  color: ${props => props.theme.colors.text};
`;

const FilterSelect = styled.select`
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
`;

const RequestsContainer = styled.div`
  margin-top: 20px;
`;

const RequestCard = styled.div`
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border-left: 5px solid ${props => {
    switch(props.status) {
      case 'approved': return '#4caf50';
      case 'denied': return '#f44336';
      default: return '#ff9800';
    }
  }};
`;

const RequestHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
`;

const PropertyTitle = styled.h3`
  color: ${props => props.theme.colors.primary};
  margin: 0;
`;

const RequestStatus = styled.span`
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  background-color: ${props => {
    switch(props.status) {
      case 'approved': return '#e8f5e9';
      case 'denied': return '#ffebee';
      default: return '#fff8e1';
    }
  }};
  color: ${props => {
    switch(props.status) {
      case 'approved': return '#2e7d32';
      case 'denied': return '#c62828';
      default: return '#f57c00';
    }
  }};
`;

const RequestDetails = styled.div`
  margin-bottom: 15px;
`;

const DetailRow = styled.div`
  display: flex;
  margin-bottom: 8px;
`;

const DetailLabel = styled.span`
  font-weight: 600;
  width: 150px;
  color: ${props => props.theme.colors.text};
`;

const DetailValue = styled.span`
  flex: 1;
`;

const RequestReason = styled.div`
  background-color: #fff;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #eee;
`;

const ReasonLabel = styled.h4`
  margin-top: 0;
  margin-bottom: 10px;
  color: ${props => props.theme.colors.text};
`;

const Button = styled.button`
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 50px 20px;
  color: #666;
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

function MyDocumentRequests() {
  const navigate = useNavigate();
  const { isAuthenticated, userRole } = useAuth();
  
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filter
  const [statusFilter, setStatusFilter] = useState('all');
  
  useEffect(() => {
    // Check if user is authenticated and has the right role
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (userRole !== 'property_seeker') {
      navigate('/dashboard');
      return;
    }
    
    fetchRequests();
  }, [isAuthenticated, userRole, navigate]);
  
  const fetchRequests = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.get('/api/document/requests/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Document requests:', response.data);
      setRequests(response.data || []);
      
    } catch (err) {
      console.error('Error fetching document requests:', err);
      setError('Failed to load document requests. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Filter requests based on status
  const filteredRequests = requests.filter(request => {
    return statusFilter === 'all' || request.status === statusFilter;
  });
  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };
  
  const getStatusMessage = (status) => {
    switch(status) {
      case 'approved':
        return 'Your request has been approved. You can now access the property documents.';
      case 'denied':
        return 'Your request has been denied by the property owner.';
      default:
        return 'Your request is pending review by the property owner.';
    }
  };
  
  const viewProperty = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };
  
  return (
    <Container>
      <PageHeader>
        <Title>My Document Access Requests</Title>
        <Subtitle>
          Track the status of your requests to access property documents.
        </Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <FilterContainer>
        <FilterGroup>
          <FilterLabel>Status:</FilterLabel>
          <FilterSelect 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Requests</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="denied">Denied</option>
          </FilterSelect>
        </FilterGroup>
      </FilterContainer>
      
      {loading ? (
        <LoadingSpinner />
      ) : filteredRequests.length === 0 ? (
        <EmptyState>
          <h3>No document access requests found</h3>
          <p>You haven't made any document access requests yet.</p>
          <Button onClick={() => navigate('/browse-properties')}>Browse Properties</Button>
        </EmptyState>
      ) : (
        <RequestsContainer>
          {filteredRequests.map((request) => (
            <RequestCard key={request.id} status={request.status}>
              <RequestHeader>
                <PropertyTitle>{request.property_title}</PropertyTitle>
                <RequestStatus status={request.status}>
                  {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                </RequestStatus>
              </RequestHeader>
              
              <RequestDetails>
                <DetailRow>
                  <DetailLabel>Property Owner:</DetailLabel>
                  <DetailValue>{request.owner_name}</DetailValue>
                </DetailRow>
                <DetailRow>
                  <DetailLabel>Requested On:</DetailLabel>
                  <DetailValue>{formatDate(request.request_date)}</DetailValue>
                </DetailRow>
                {request.status !== 'pending' && (
                  <DetailRow>
                    <DetailLabel>Response Date:</DetailLabel>
                    <DetailValue>{formatDate(request.response_date)}</DetailValue>
                  </DetailRow>
                )}
              </RequestDetails>
              
              <RequestReason>
                <ReasonLabel>Your Request Reason:</ReasonLabel>
                <p>{request.reason}</p>
              </RequestReason>
              
              {request.status !== 'pending' && request.response_note && (
                <RequestReason>
                  <ReasonLabel>Owner's Response:</ReasonLabel>
                  <p>{request.response_note}</p>
                </RequestReason>
              )}
              
              <div style={{ marginTop: '15px' }}>
                <p>{getStatusMessage(request.status)}</p>
                <Button onClick={() => viewProperty(request.property_id)}>
                  View Property
                </Button>
              </div>
            </RequestCard>
          ))}
        </RequestsContainer>
      )}
    </Container>
  );
}

export default MyDocumentRequests; 
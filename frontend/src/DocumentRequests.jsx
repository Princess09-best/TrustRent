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

const SearchInput = styled.input`
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  width: 250px;
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

const ActionContainer = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
`;

const Button = styled.button`
  background-color: ${props => {
    if (props.variant === 'approve') return '#4caf50';
    if (props.variant === 'deny') return '#f44336';
    return props.theme.colors.primary;
  }};
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
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const ResponseForm = styled.div`
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: ${props => props.theme.colors.text};
`;

const FormTextarea = styled.textarea`
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  min-height: 80px;
  resize: vertical;
  margin-bottom: 15px;
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

const SuccessMessage = styled.div`
  color: #2e7d32;
  background-color: #e8f5e9;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
`;

function DocumentRequests() {
  const navigate = useNavigate();
  const { isAuthenticated, userRole } = useAuth();
  
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Response state
  const [responseNotes, setResponseNotes] = useState({});
  const [respondingTo, setRespondingTo] = useState(null);
  const [processingRequest, setProcessingRequest] = useState(false);
  
  useEffect(() => {
    // Check if user is authenticated and has the right role
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (userRole !== 'property_owner') {
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
  
  const handleResponseChange = (requestId, value) => {
    setResponseNotes({
      ...responseNotes,
      [requestId]: value
    });
  };
  
  const handleRespond = async (requestId, decision) => {
    try {
      setProcessingRequest(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.post('/api/document/respond/', {
        request_id: requestId,
        decision: decision,
        response_note: responseNotes[requestId] || ''
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Response submitted:', response.data);
      
      // Update the request in the UI
      setRequests(requests.map(req => 
        req.id === requestId 
          ? { 
              ...req, 
              status: decision,
              response_date: new Date().toISOString(),
              response_note: responseNotes[requestId] || ''
            } 
          : req
      ));
      
      setSuccess(`Request ${decision === 'approved' ? 'approved' : 'denied'} successfully.`);
      setRespondingTo(null);
      
      // Clear response note for this request
      const updatedNotes = { ...responseNotes };
      delete updatedNotes[requestId];
      setResponseNotes(updatedNotes);
      
    } catch (err) {
      console.error('Error responding to request:', err);
      if (err.response) {
        setError(`Failed to respond: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to respond to request. Please try again.');
      }
    } finally {
      setProcessingRequest(false);
    }
  };
  
  // Filter requests based on status and search term
  const filteredRequests = requests.filter(request => {
    const matchesStatus = statusFilter === 'all' || request.status === statusFilter;
    const matchesSearch = 
      request.property_title.toLowerCase().includes(searchTerm.toLowerCase()) || 
      request.requester_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesSearch;
  });
  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };
  
  return (
    <Container>
      <PageHeader>
        <Title>Document Access Requests</Title>
        <Subtitle>
          Manage requests from property seekers who want to access your property documents.
          You can approve or deny these requests based on your discretion.
        </Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      
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
        
        <SearchInput 
          type="text"
          placeholder="Search by property or requester name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </FilterContainer>
      
      {loading ? (
        <LoadingSpinner />
      ) : filteredRequests.length === 0 ? (
        <EmptyState>
          <h3>No document access requests found</h3>
          <p>When property seekers request access to your property documents, they will appear here.</p>
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
                  <DetailLabel>Requester:</DetailLabel>
                  <DetailValue>{request.requester_name}</DetailValue>
                </DetailRow>
                <DetailRow>
                  <DetailLabel>Email:</DetailLabel>
                  <DetailValue>{request.requester_email}</DetailValue>
                </DetailRow>
                <DetailRow>
                  <DetailLabel>Requested On:</DetailLabel>
                  <DetailValue>{formatDate(request.request_date)}</DetailValue>
                </DetailRow>
                {request.status !== 'pending' && (
                  <DetailRow>
                    <DetailLabel>Responded On:</DetailLabel>
                    <DetailValue>{formatDate(request.response_date)}</DetailValue>
                  </DetailRow>
                )}
              </RequestDetails>
              
              <RequestReason>
                <ReasonLabel>Request Reason:</ReasonLabel>
                <p>{request.reason}</p>
              </RequestReason>
              
              {request.status !== 'pending' && request.response_note && (
                <RequestReason>
                  <ReasonLabel>Your Response:</ReasonLabel>
                  <p>{request.response_note}</p>
                </RequestReason>
              )}
              
              {request.status === 'pending' && (
                <>
                  {respondingTo === request.id ? (
                    <ResponseForm>
                      <FormLabel>Response Note (Optional):</FormLabel>
                      <FormTextarea 
                        value={responseNotes[request.id] || ''}
                        onChange={(e) => handleResponseChange(request.id, e.target.value)}
                        placeholder="Add a note to explain your decision (optional)..."
                      />
                      
                      <ActionContainer>
                        <Button 
                          onClick={() => setRespondingTo(null)} 
                          variant="secondary"
                          disabled={processingRequest}
                        >
                          Cancel
                        </Button>
                        <Button 
                          onClick={() => handleRespond(request.id, 'denied')} 
                          variant="deny"
                          disabled={processingRequest}
                        >
                          {processingRequest ? 'Processing...' : 'Deny Request'}
                        </Button>
                        <Button 
                          onClick={() => handleRespond(request.id, 'approved')} 
                          variant="approve"
                          disabled={processingRequest}
                        >
                          {processingRequest ? 'Processing...' : 'Approve Request'}
                        </Button>
                      </ActionContainer>
                    </ResponseForm>
                  ) : (
                    <ActionContainer>
                      <Button onClick={() => setRespondingTo(request.id)}>
                        Respond to Request
                      </Button>
                    </ActionContainer>
                  )}
                </>
              )}
            </RequestCard>
          ))}
        </RequestsContainer>
      )}
    </Container>
  );
}

export default DocumentRequests; 
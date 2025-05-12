import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px;
  background-color: ${props => props.theme.colors.background};
`;

const Title = styled.h1`
  font-size: 2rem;
  color: ${props => props.theme.colors.primary};
  margin-bottom: 10px;
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  color: ${props => props.theme.colors.text};
  margin-bottom: 30px;
  opacity: 0.8;
`;

const PropertyGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
`;

const PropertyCard = styled.div`
  background-color: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`;

const PropertyImage = styled.div`
  height: 200px;
  background-image: url(${props => props.src ? props.src : '/default-property.jpg'});
  background-size: cover;
  background-position: center;
`;

const PropertyContent = styled.div`
  padding: 20px;
`;

const PropertyTitle = styled.h3`
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: ${props => props.theme.colors.text};
`;

const PropertyDetails = styled.div`
  margin-bottom: 15px;
`;

const PropertyDetail = styled.p`
  font-size: 0.9rem;
  margin: 5px 0;
  color: ${props => props.theme.colors.text};
  display: flex;
  align-items: center;
`;

const StatusBadge = styled.span`
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 10px;
  background-color: ${props => {
    switch (props.status) {
      case 'verified':
        return '#28a745';
      case 'pending':
        return '#ffc107';
      case 'rejected':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  }};
  color: white;
`;

const Button = styled.button`
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-top: 10px;
  
  &:hover {
    background-color: ${props => props.theme.colors.primaryDark};
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  
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

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
`;

const EmptyStateTitle = styled.h3`
  font-size: 1.4rem;
  color: ${props => props.theme.colors.text};
  margin-bottom: 15px;
`;

const EmptyStateText = styled.p`
  font-size: 1rem;
  color: ${props => props.theme.colors.textLight};
  margin-bottom: 20px;
`;

function MyProperties() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { currentUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProperties = async () => {
      try {
        setLoading(true);
        
        // Get token from localStorage
        const token = localStorage.getItem('token');
        console.log('Auth status:', { isAuthenticated, hasToken: !!token, user: currentUser?.email });
        
        if (!token) {
          setError('Authentication token not found. Please log in again.');
          setLoading(false);
          return;
        }
        
        // First get user properties from core database
        const response = await axios.get('/api/user/properties/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        console.log('API Response:', response.data);
        
        // Check if the response is an array
        if (Array.isArray(response.data)) {
          setProperties(response.data);
        } else {
          console.error('Unexpected response format:', response.data);
          setProperties([]);
        }
      } catch (err) {
        console.error('Error fetching properties:', err);
        if (err.response) {
          console.error('Response error:', err.response.status, err.response.data);
          setError(`Failed to load properties: ${err.response.data?.error || err.response.statusText}`);
        } else if (err.request) {
          console.error('Request error:', err.request);
          setError('Network error. Server did not respond.');
        } else {
          setError(`Error: ${err.message}`);
        }
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if authenticated
    if (isAuthenticated) {
      fetchProperties();
    } else {
      setLoading(false);
      setError('Please log in to view your properties.');
    }
  }, [isAuthenticated, currentUser]);

  const handleCreateProperty = () => {
    navigate('/create-property');
  };

  const handleViewProperty = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    window.location.reload();
  };

  if (loading) {
    return (
      <Container>
        <Title>My Properties</Title>
        <Subtitle>Loading your properties...</Subtitle>
        <LoadingSpinner />
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Title>My Properties</Title>
        <Subtitle>Something went wrong</Subtitle>
        <EmptyState>
          <EmptyStateTitle>Error Loading Properties</EmptyStateTitle>
          <EmptyStateText>{error}</EmptyStateText>
          <Button onClick={handleRetry}>Try Again</Button>
        </EmptyState>
      </Container>
    );
  }

  return (
    <Container>
      <Title>My Properties</Title>
      <Subtitle>Manage your properties and view their verification status</Subtitle>
      
      <Button onClick={handleCreateProperty}>Create New Property</Button>
      
      {properties.length === 0 ? (
        <EmptyState>
          <EmptyStateTitle>No Properties Found</EmptyStateTitle>
          <EmptyStateText>You haven't created any properties yet. Create your first property to get started.</EmptyStateText>
          <Button onClick={handleCreateProperty}>Create Property</Button>
        </EmptyState>
      ) : (
        <PropertyGrid>
          {properties.map(property => (
            <PropertyCard key={property.id}>
              <PropertyImage src={property.image_url || '/default-property.jpg'} />
              <PropertyContent>
                <PropertyTitle>{property.title}</PropertyTitle>
                <PropertyDetails>
                  <PropertyDetail><strong>Type:</strong> {property.property_type}</PropertyDetail>
                  <PropertyDetail><strong>Location:</strong> {property.location}</PropertyDetail>
                  <PropertyDetail><strong>Created:</strong> {property.created_at ? new Date(property.created_at).toLocaleDateString() : 'Unknown'}</PropertyDetail>
                </PropertyDetails>
                <StatusBadge status={property.verification_status || 'pending'}>
                  {property.verification_status === 'approved' ? 'Verified' : 
                   property.verification_status === 'pending' ? 'Pending Verification' : 
                   property.verification_status === 'rejected' ? 'Rejected' : 'Pending Verification'}
                </StatusBadge>
                <div style={{ marginTop: '15px' }}>
                  <Button onClick={() => handleViewProperty(property.id)}>View Details</Button>
                </div>
              </PropertyContent>
            </PropertyCard>
          ))}
        </PropertyGrid>
      )}
    </Container>
  );
}

export default MyProperties; 
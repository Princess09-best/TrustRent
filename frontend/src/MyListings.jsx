import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';
import { getMediaUrl, handleImageError } from './utils/mediaHelpers';

const Container = styled.div`
  max-width: 1200px;
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
`;

const ListingsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
  margin-top: 20px;
`;

const ListingCard = styled.div`
  background-color: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`;

const ListingImageContainer = styled.div`
  height: 200px;
  overflow: hidden;
  position: relative;
`;

const ListingImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
`;

const ListingContent = styled.div`
  padding: 20px;
`;

const ListingTitle = styled.h3`
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: ${props => props.theme.colors.text};
`;

const ListingPrice = styled.div`
  font-size: 1.4rem;
  font-weight: 600;
  color: ${props => props.theme.colors.primary};
  margin-bottom: 15px;
`;

const ListingDetails = styled.div`
  margin-bottom: 15px;
`;

const ListingDetail = styled.p`
  font-size: 0.9rem;
  margin: 5px 0;
  color: ${props => props.theme.colors.text};
  display: flex;
  align-items: center;
`;

const ListingTypeBadge = styled.span`
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background-color: ${props => props.type === 'rent' ? '#4CAF50' : '#2196F3'};
  color: white;
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
      case 'active':
        return '#28a745';
      case 'pending':
        return '#ffc107';
      case 'inactive':
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
  margin-right: 8px;
  
  &:hover {
    background-color: ${props => props.theme.colors.primaryDark};
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const DangerButton = styled(Button)`
  background-color: #dc3545;
  
  &:hover {
    background-color: #c82333;
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

const ErrorMessage = styled.div`
  padding: 15px;
  background-color: #FEEBEE;
  color: #F44336;
  border-radius: 8px;
  margin-bottom: 20px;
`;

function MyListings() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [refreshKey, setRefreshKey] = useState(0);

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-GH', {
      style: 'currency',
      currency: 'GHS'
    }).format(amount);
  };

  const fetchListings = async () => {
    try {
      setLoading(true);
      
      // Get token from localStorage
      const token = localStorage.getItem('token');
      console.log('Auth status:', { isAuthenticated, hasToken: !!token });
      
      if (!token) {
        setError('Authentication token not found. Please log in again.');
        setLoading(false);
        return;
      }
      
      // Get owner's listings
      const timestamp = new Date().getTime(); // Add timestamp for cache busting
      const response = await axios.get(`/api/my-listings/?t=${timestamp}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log('API Response:', response.data);
      
      // Check if response has the expected format with listings array
      if (response.data && response.data.listings && Array.isArray(response.data.listings)) {
        // Process image URLs
        const processedListings = response.data.listings.map(listing => {
          // Check for images array and use the first image if available
          if (listing.images && listing.images.length > 0) {
            listing.image_url = getMediaUrl(listing.images[0].image);
          }
          
          // Map property title to expected field
          listing.property_title = listing.title;
          
          return listing;
        });
        
        setListings(processedListings);
      } else if (Array.isArray(response.data)) {
        // Handle case where API directly returns an array (for backward compatibility)
        const processedListings = response.data.map(listing => {
          if (listing.image_url) {
            listing.image_url = getMediaUrl(listing.image_url);
          }
          return listing;
        });
        
        setListings(processedListings);
      } else {
        console.error('Unexpected response format:', response.data);
        setListings([]);
      }
    } catch (err) {
      console.error('Error fetching listings:', err);
      if (err.response) {
        setError(`Failed to load listings: ${err.response.data?.error || err.response.statusText}`);
      } else if (err.request) {
        setError('Network error. Server did not respond.');
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchListings();
    } else {
      navigate('/login');
    }
    
    // Set up auto-refresh interval (every 60 seconds)
    const intervalId = setInterval(() => {
      if (isAuthenticated) {
        console.log("Auto-refreshing listings data...");
        fetchListings();
      }
    }, 60000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, [isAuthenticated, navigate, refreshKey]);

  const handleRefresh = () => {
    console.log("Manual refresh triggered");
    setRefreshKey(prevKey => prevKey + 1);
    fetchListings();
  };

  const handleDeactivateListing = async (listingId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication token not found. Please log in again.');
        return;
      }
      
      const response = await axios.post(`/api/listing/${listingId}/deactivate/`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Deactivate response:', response.data);
      
      // Update the listing status in the UI
      setListings(prevListings => 
        prevListings.map(listing => 
          listing.id === listingId ? { ...listing, is_active: false } : listing
        )
      );
      
      // Refresh the listings
      fetchListings();
      
    } catch (err) {
      console.error('Error deactivating listing:', err);
      if (err.response) {
        setError(`Failed to deactivate listing: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to deactivate listing. Please try again.');
      }
    }
  };

  const handleReactivateListing = async (listingId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication token not found. Please log in again.');
        return;
      }
      
      const response = await axios.post(`/api/listing/${listingId}/reactivate/`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Reactivate response:', response.data);
      
      // Update the listing status in the UI
      setListings(prevListings => 
        prevListings.map(listing => 
          listing.id === listingId ? { ...listing, is_active: true } : listing
        )
      );
      
      // Refresh the listings
      fetchListings();
      
    } catch (err) {
      console.error('Error reactivating listing:', err);
      if (err.response) {
        setError(`Failed to reactivate listing: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to reactivate listing. Please try again.');
      }
    }
  };

  const handleEditListing = (listingId) => {
    navigate(`/edit-listing/${listingId}`);
  };

  if (loading) {
    return (
      <Container>
        <Title>My Listings</Title>
        <Subtitle>Loading your property listings...</Subtitle>
        <LoadingSpinner />
      </Container>
    );
  }

  return (
    <Container>
      <PageHeader>
        <Title>My Listings</Title>
        <Subtitle>Manage your property listings</Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <Button onClick={handleRefresh} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Listings'}
        </Button>
        <Button onClick={() => navigate('/my-properties')}>
          Back to My Properties
        </Button>
      </div>
      
      {listings.length === 0 ? (
        <EmptyState>
          <EmptyStateTitle>No Listings Found</EmptyStateTitle>
          <EmptyStateText>You haven't created any property listings yet. List your verified properties to get started.</EmptyStateText>
          <Button onClick={() => navigate('/my-properties')}>Go to My Properties</Button>
        </EmptyState>
      ) : (
        <ListingsGrid>
          {listings.map(listing => (
            <ListingCard key={listing.id}>
              <ListingImageContainer>
                <ListingImage 
                  src={listing.image_url || '/default-property.jpg'} 
                  alt={listing.property_title}
                  onError={handleImageError}
                />
                <ListingTypeBadge type={listing.listing_type}>
                  {listing.listing_type === 'rent' ? 'For Rent' : 'For Sale'}
                </ListingTypeBadge>
              </ListingImageContainer>
              <ListingContent>
                <ListingTitle>{listing.property_title}</ListingTitle>
                <ListingPrice>
                  {formatCurrency(listing.price)}
                  {listing.listing_type === 'rent' ? ' / month' : ''}
                </ListingPrice>
                <ListingDetails>
                  <ListingDetail><strong>Location:</strong> {listing.location}</ListingDetail>
                  <ListingDetail><strong>Type:</strong> {listing.property_type}</ListingDetail>
                  <ListingDetail><strong>Created:</strong> {listing.created_at ? new Date(listing.created_at).toLocaleDateString() : 'Unknown'}</ListingDetail>
                </ListingDetails>
                <StatusBadge status={listing.is_active ? 'active' : 'inactive'}>
                  {listing.is_active ? 'Active' : 'Inactive'}
                </StatusBadge>
                <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                  {listing.is_active ? (
                    <DangerButton onClick={() => handleDeactivateListing(listing.id)}>
                      Deactivate
                    </DangerButton>
                  ) : (
                    <Button onClick={() => handleReactivateListing(listing.id)}>
                      Reactivate
                    </Button>
                  )}
                  <Button onClick={() => handleEditListing(listing.id)}>
                    Edit
                  </Button>
                </div>
              </ListingContent>
            </ListingCard>
          ))}
        </ListingsGrid>
      )}
    </Container>
  );
}

export default MyListings; 
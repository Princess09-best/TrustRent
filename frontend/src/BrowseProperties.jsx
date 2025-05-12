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

const FiltersContainer = styled.div`
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 30px;
`;

const FilterRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
`;

const FilterGroup = styled.div`
  flex: 1;
  min-width: 200px;
`;

const FilterLabel = styled.label`
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: ${props => props.theme.colors.text};
`;

const FilterInput = styled.input`
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 0.9rem;
`;

const FilterSelect = styled.select`
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 0.9rem;
`;

const ButtonRow = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 10px;
`;

const Button = styled.button`
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    background-color: ${props => props.theme.colors.primaryDark};
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ClearButton = styled(Button)`
  background-color: #6c757d;
  
  &:hover {
    background-color: #5a6268;
  }
`;

const PropertiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
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

const PropertyImageContainer = styled.div`
  height: 200px;
  overflow: hidden;
  position: relative;
`;

const PropertyImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
`;

const PropertyContent = styled.div`
  padding: 20px;
`;

const PropertyTitle = styled.h3`
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: ${props => props.theme.colors.text};
`;

const PropertyPrice = styled.div`
  font-size: 1.4rem;
  font-weight: 600;
  color: ${props => props.theme.colors.primary};
  margin-bottom: 15px;
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

const PropertyTypeBadge = styled.span`
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

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-top: 30px;
  gap: 10px;
`;

const PageButton = styled.button`
  padding: 8px 12px;
  border: 1px solid ${props => props.active ? props.theme.colors.primary : '#ddd'};
  background-color: ${props => props.active ? props.theme.colors.primary : 'white'};
  color: ${props => props.active ? 'white' : props.theme.colors.text};
  border-radius: 5px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.5 : 1};
  
  &:hover {
    background-color: ${props => props.active ? props.theme.colors.primary : '#f5f5f5'};
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

function BrowseProperties() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [perPage, setPerPage] = useState(9);
  
  // Filter state
  const [filters, setFilters] = useState({
    location: '',
    type: '',
    minPrice: '',
    maxPrice: '',
    listingType: '',
    search: ''
  });
  
  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-GH', {
      style: 'currency',
      currency: 'GHS'
    }).format(amount);
  };

  const fetchProperties = async () => {
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
      
      // Build query parameters
      const queryParams = new URLSearchParams();
      queryParams.append('page', currentPage);
      queryParams.append('per_page', perPage);
      
      // Add filters if they exist
      if (filters.location) queryParams.append('location', filters.location);
      if (filters.type) queryParams.append('type', filters.type);
      if (filters.minPrice) queryParams.append('min_price', filters.minPrice);
      if (filters.maxPrice) queryParams.append('max_price', filters.maxPrice);
      if (filters.listingType) queryParams.append('listing_type', filters.listingType);
      if (filters.search) queryParams.append('search', filters.search);
      
      // Add timestamp for cache busting
      queryParams.append('t', new Date().getTime());
      
      // Get properties
      const response = await axios.get(`/api/properties/?${queryParams.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log('API Response:', response.data);
      
      if (response.data && response.data.properties && Array.isArray(response.data.properties)) {
        // Process image URLs
        const processedProperties = response.data.properties.map(property => {
          // Check for images array and use the first image if available
          if (property.images && property.images.length > 0) {
            property.image_url = getMediaUrl(property.images[0].image);
          }
          return property;
        });
        
        setProperties(processedProperties);
        
        // Update pagination state
        if (response.data.pagination) {
          setTotalPages(response.data.pagination.total_pages);
          setTotalItems(response.data.pagination.total);
        }
      } else {
        console.error('Unexpected response format:', response.data);
        setProperties([]);
      }
    } catch (err) {
      console.error('Error fetching properties:', err);
      if (err.response) {
        setError(`Failed to load properties: ${err.response.data?.error || err.response.statusText}`);
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
      fetchProperties();
    } else {
      navigate('/login');
    }
  }, [isAuthenticated, navigate, currentPage]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page when applying filters
    fetchProperties();
  };

  const clearFilters = () => {
    setFilters({
      location: '',
      type: '',
      minPrice: '',
      maxPrice: '',
      listingType: '',
      search: ''
    });
    setCurrentPage(1);
    // Fetch properties without filters
    fetchProperties();
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleViewProperty = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

  if (loading) {
    return (
      <Container>
        <Title>Browse Properties</Title>
        <Subtitle>Loading available properties...</Subtitle>
        <LoadingSpinner />
      </Container>
    );
  }

  return (
    <Container>
      <PageHeader>
        <Title>Browse Properties</Title>
        <Subtitle>Find your perfect property</Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <FiltersContainer>
        <form onSubmit={handleFilterSubmit}>
          <FilterRow>
            <FilterGroup>
              <FilterLabel>Location</FilterLabel>
              <FilterInput 
                type="text" 
                name="location" 
                value={filters.location}
                onChange={handleFilterChange}
                placeholder="Enter location"
              />
            </FilterGroup>
            
            <FilterGroup>
              <FilterLabel>Property Type</FilterLabel>
              <FilterSelect 
                name="type" 
                value={filters.type}
                onChange={handleFilterChange}
              >
                <option value="">All Types</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="townhouse">Townhouse</option>
                <option value="villa">Villa</option>
                <option value="studio">Studio</option>
                <option value="commercial">Commercial</option>
              </FilterSelect>
            </FilterGroup>
            
            <FilterGroup>
              <FilterLabel>Listing Type</FilterLabel>
              <FilterSelect 
                name="listingType" 
                value={filters.listingType}
                onChange={handleFilterChange}
              >
                <option value="">All</option>
                <option value="rent">For Rent</option>
                <option value="sale">For Sale</option>
              </FilterSelect>
            </FilterGroup>
          </FilterRow>
          
          <FilterRow>
            <FilterGroup>
              <FilterLabel>Min Price (GHS)</FilterLabel>
              <FilterInput 
                type="number" 
                name="minPrice" 
                value={filters.minPrice}
                onChange={handleFilterChange}
                placeholder="Minimum price"
                min="0"
              />
            </FilterGroup>
            
            <FilterGroup>
              <FilterLabel>Max Price (GHS)</FilterLabel>
              <FilterInput 
                type="number" 
                name="maxPrice" 
                value={filters.maxPrice}
                onChange={handleFilterChange}
                placeholder="Maximum price"
                min="0"
              />
            </FilterGroup>
            
            <FilterGroup>
              <FilterLabel>Search</FilterLabel>
              <FilterInput 
                type="text" 
                name="search" 
                value={filters.search}
                onChange={handleFilterChange}
                placeholder="Search by title or description"
              />
            </FilterGroup>
          </FilterRow>
          
          <ButtonRow>
            <ClearButton type="button" onClick={clearFilters}>
              Clear Filters
            </ClearButton>
            <Button type="submit">
              Apply Filters
            </Button>
          </ButtonRow>
        </form>
      </FiltersContainer>
      
      {properties.length === 0 ? (
        <EmptyState>
          <EmptyStateTitle>No Properties Found</EmptyStateTitle>
          <EmptyStateText>Try adjusting your filters or search criteria.</EmptyStateText>
          <Button onClick={clearFilters}>Clear All Filters</Button>
        </EmptyState>
      ) : (
        <>
          <PropertiesGrid>
            {properties.map(property => (
              <PropertyCard key={property.id} onClick={() => handleViewProperty(property.id)}>
                <PropertyImageContainer>
                  <PropertyImage 
                    src={property.image_url || '/default-property.jpg'} 
                    alt={property.title}
                    onError={handleImageError}
                  />
                  <PropertyTypeBadge type={property.listing_type}>
                    {property.listing_type === 'rent' ? 'For Rent' : 'For Sale'}
                  </PropertyTypeBadge>
                </PropertyImageContainer>
                <PropertyContent>
                  <PropertyTitle>{property.title}</PropertyTitle>
                  <PropertyPrice>
                    {formatCurrency(property.price)}
                    {property.listing_type === 'rent' ? ' / month' : ''}
                  </PropertyPrice>
                  <PropertyDetails>
                    <PropertyDetail><strong>Location:</strong> {property.location}</PropertyDetail>
                    <PropertyDetail><strong>Type:</strong> {property.property_type}</PropertyDetail>
                    <PropertyDetail><strong>Owner:</strong> {property.owner?.name}</PropertyDetail>
                  </PropertyDetails>
                </PropertyContent>
              </PropertyCard>
            ))}
          </PropertiesGrid>
          
          {totalPages > 1 && (
            <PaginationContainer>
              <PageButton 
                onClick={() => handlePageChange(1)} 
                disabled={currentPage === 1}
              >
                First
              </PageButton>
              <PageButton 
                onClick={() => handlePageChange(currentPage - 1)} 
                disabled={currentPage === 1}
              >
                Previous
              </PageButton>
              
              {/* Show page numbers */}
              {[...Array(totalPages).keys()].map(page => {
                // Show current page, and 1 page before and after
                if (
                  page + 1 === 1 || 
                  page + 1 === totalPages || 
                  (page + 1 >= currentPage - 1 && page + 1 <= currentPage + 1)
                ) {
                  return (
                    <PageButton 
                      key={page + 1}
                      active={currentPage === page + 1}
                      onClick={() => handlePageChange(page + 1)}
                    >
                      {page + 1}
                    </PageButton>
                  );
                }
                // Show ellipsis for skipped pages
                if (page + 1 === currentPage - 2 || page + 1 === currentPage + 2) {
                  return <span key={page + 1}>...</span>;
                }
                return null;
              })}
              
              <PageButton 
                onClick={() => handlePageChange(currentPage + 1)} 
                disabled={currentPage === totalPages}
              >
                Next
              </PageButton>
              <PageButton 
                onClick={() => handlePageChange(totalPages)} 
                disabled={currentPage === totalPages}
              >
                Last
              </PageButton>
            </PaginationContainer>
          )}
        </>
      )}
    </Container>
  );
}

export default BrowseProperties; 
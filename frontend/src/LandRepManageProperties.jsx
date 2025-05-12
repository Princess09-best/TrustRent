import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

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

const FilterSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
`;

const SearchInput = styled.input`
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  min-width: 300px;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const StatusFilter = styled.select`
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  min-width: 150px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
`;

const TableHead = styled.thead`
  background-color: ${props => props.theme.colors.primaryLight};
  color: ${props => props.theme.colors.primary};
`;

const TableRow = styled.tr`
  &:nth-child(even) {
    background-color: #f9f9f9;
  }
  
  &:hover {
    background-color: #f5f5f5;
  }
`;

const TableHeader = styled.th`
  padding: 15px;
  text-align: left;
  font-weight: 600;
`;

const TableCell = styled.td`
  padding: 15px;
  border-top: 1px solid #eee;
  vertical-align: middle;
  
  a {
    color: ${props => props.theme.colors.primary};
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

const StatusBadge = styled.span`
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  
  ${props => {
    if (props.status === 'pending') {
      return `
        background-color: #FFF4E5;
        color: #FF9800;
      `;
    } else if (props.status === 'approved') {
      return `
        background-color: #E8F5E9;
        color: #4CAF50;
      `;
    } else if (props.status === 'rejected') {
      return `
        background-color: #FEEBEE;
        color: #F44336;
      `;
    }
    return `
      background-color: #E0E0E0;
      color: #757575;
    `;
  }}
`;

const ActionButton = styled.button`
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  font-weight: 500;
  cursor: pointer;
  margin-right: 8px;
  transition: all 0.2s;
  
  ${props => props.primary ? `
    background-color: ${props.theme.colors.primary};
    color: white;
    
    &:hover {
      background-color: ${props.theme.colors.primaryDark};
    }
  ` : `
    background-color: #f5f5f5;
    color: #555;
    border: 1px solid #ddd;
    
    &:hover {
      background-color: #e0e0e0;
    }
  `}
  
  &:last-child {
    margin-right: 0;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const LoadingMessage = styled.div`
  text-align: center;
  padding: 50px;
  font-size: 1.1rem;
  color: #666;
`;

const ErrorMessage = styled.div`
  padding: 15px;
  background-color: #FEEBEE;
  color: #F44336;
  border-radius: 8px;
  margin-bottom: 20px;
`;

const DetailRow = styled.div`
  margin-bottom: 6px;
  font-size: 0.9rem;
  color: #777;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.colors.primary};
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
  text-decoration: underline;
  
  &:hover {
    color: ${props => props.theme.colors.primaryDark};
  }
`;

const NoData = styled.div`
  text-align: center;
  padding: 50px;
  color: #666;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-top: 20px;
`;

const PropertyCard = styled.div`
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
`;

const PropertyCardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
`;

const PropertyTitle = styled.h3`
  margin: 0;
  font-size: 1.2rem;
  color: ${props => props.theme.colors.primary};
`;

function LandRepManageProperties() {
  const { userRole, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRows, setExpandedRows] = useState({});

  // Fetch properties from the API
  const fetchProperties = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log("Starting fetchProperties function");
      const token = localStorage.getItem('token');
      if (!token) {
        console.log("No token found, redirecting to login");
        navigate('/login');
        return;
      }
      
      console.log("Making API request to /api/property/unverified/");
      const response = await fetch('/api/property/unverified/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log("API response status:", response.status);
      
      if (!response.ok) {
        console.error("API error response:", response.statusText);
        throw new Error('Failed to fetch properties');
      }

      const data = await response.json();
      console.log("API response data:", data);
      
      // Transform the data format if needed
      const formattedProperties = data.map(property => ({
        id: property.id,
        user_property_id: property.id, // This needs to be updated with actual user_property_id
        title: property.title,
        description: property.description,
        location: property.location,
        owner: property.owner,
        created_at: property.created_at,
        verification_status: 'pending',
        documents: property.documents || [],
        images: property.images || []
      }));
      
      console.log("Formatted properties:", formattedProperties);
      setProperties(formattedProperties);
    } catch (err) {
      console.error("Error in fetchProperties:", err);
      setError('Failed to load properties. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const filterProperties = useCallback(() => {
    return properties.filter(property => {
      // First filter by status
      const statusMatch = statusFilter === 'all' || property.verification_status === statusFilter;
      
      // Then filter by search term
      const searchMatch = 
        property.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        property.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        property.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (property.owner && property.owner.full_name && 
         property.owner.full_name.toLowerCase().includes(searchTerm.toLowerCase()));
      
      return statusMatch && searchMatch;
    });
  }, [properties, statusFilter, searchTerm]);

  // Toggle expanded row
  const toggleExpandRow = (id) => {
    setExpandedRows(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Verify property
  const handleVerify = async (id, user_property_id) => {
    try {
      setError('');
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch('/api/property/verify/', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_property_id: user_property_id,
          verification_status: 'approved'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to verify property');
      }

      // Update UI
      setProperties(prev => 
        prev.map(property => 
          property.id === id 
            ? { ...property, verification_status: 'approved' } 
            : property
        )
      );
      
      // Show success message or notification (optional)
      alert('Property verified successfully');
      
      // Refresh the property list
      fetchProperties();
      
    } catch (err) {
      setError(err.message || 'Failed to verify property. Please try again.');
      console.error(err);
    }
  };

  // Reject property
  const handleReject = async (id, user_property_id) => {
    try {
      setError('');
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) {
        return; // User cancelled the prompt
      }

      const response = await fetch('/api/property/reject/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_property_id: user_property_id,
          rejection_reason: reason
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to reject property');
      }

      // Update UI
      setProperties(prev => 
        prev.map(property => 
          property.id === id 
            ? { ...property, verification_status: 'rejected', rejection_reason: reason } 
            : property
        )
      );
      
      // Show success message or notification (optional)
      alert('Property rejected successfully');
      
      // Refresh the property list
      fetchProperties();
      
    } catch (err) {
      setError(err.message || 'Failed to reject property. Please try again.');
      console.error(err);
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  // Check authentication and role on component mount
  useEffect(() => {
    console.log("LandRepManageProperties mounted");
    console.log("Authentication status:", isAuthenticated);
    console.log("User role:", userRole);
    
    if (!isAuthenticated) {
      console.log("Not authenticated, redirecting to login");
      navigate('/login');
      return;
    }

    if (userRole !== 'land_rep' && userRole !== 'land_commission_rep' && userRole !== 'admin' && userRole !== 'sys_admin') {
      console.log("Insufficient permissions, redirecting to dashboard");
      console.log("Current role:", userRole);
      navigate('/dashboard');
      return;
    }

    console.log("Fetching properties...");
    fetchProperties();
  }, [isAuthenticated, userRole, navigate, fetchProperties]);

  // No need for a separate useEffect for filtering since we now compute it on render
  const filteredProperties = filterProperties();

  return (
    <Container>
      <PageHeader>
        <Title>Manage Properties</Title>
        <Subtitle>Review, verify, and manage property listings</Subtitle>
      </PageHeader>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <FilterSection>
        <SearchInput 
          type="text"
          placeholder="Search by title, location, owner..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        
        <StatusFilter 
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </StatusFilter>
      </FilterSection>

      {loading ? (
        <LoadingMessage>Loading properties...</LoadingMessage>
      ) : filteredProperties.length === 0 ? (
        <NoData>
          {searchTerm || statusFilter !== 'all' 
            ? 'No properties match your search criteria' 
            : 'No properties requiring verification at this time'}
        </NoData>
      ) : (
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Property</TableHeader>
              <TableHeader>Location</TableHeader>
              <TableHeader>Owner</TableHeader>
              <TableHeader>Date Created</TableHeader>
              <TableHeader>Documents</TableHeader>
              <TableHeader>Status</TableHeader>
              <TableHeader>Actions</TableHeader>
            </TableRow>
          </TableHead>
          <tbody>
            {filteredProperties.map((property) => (
              <React.Fragment key={property.id}>
                <TableRow>
                  <TableCell>
                    <strong>{property.title}</strong>
                    {expandedRows[property.id] ? (
                      <DetailRow>{property.description}</DetailRow>
                    ) : (
                      <ExpandButton onClick={() => toggleExpandRow(property.id)}>
                        Show details
                      </ExpandButton>
                    )}
                  </TableCell>
                  <TableCell>{property.location}</TableCell>
                  <TableCell>
                    {property.owner?.full_name || 'Unknown'}
                    <DetailRow>{property.owner?.email || 'No email'}</DetailRow>
                  </TableCell>
                  <TableCell>{formatDate(property.created_at)}</TableCell>
                  <TableCell>
                    {property.documents?.length || 0} document(s)
                    {property.images?.length > 0 && 
                      <DetailRow>{property.images.length} image(s)</DetailRow>
                    }
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={property.verification_status}>
                      {property.verification_status}
                    </StatusBadge>
                  </TableCell>
                  <TableCell>
                    {property.verification_status === 'pending' && (
                      <>
                        <ActionButton primary onClick={() => handleVerify(property.id, property.user_property_id)}>
                          Verify
                        </ActionButton>
                        <ActionButton onClick={() => handleReject(property.id, property.user_property_id)}>
                          Reject
                        </ActionButton>
                      </>
                    )}
                    {property.verification_status === 'rejected' && (
                      <ActionButton primary onClick={() => handleVerify(property.id, property.user_property_id)}>
                        Verify
                      </ActionButton>
                    )}
                  </TableCell>
                </TableRow>
                {expandedRows[property.id] && (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <PropertyCard>
                        <PropertyCardHeader>
                          <PropertyTitle>Details for {property.title}</PropertyTitle>
                          <ExpandButton onClick={() => toggleExpandRow(property.id)}>
                            Hide details
                          </ExpandButton>
                        </PropertyCardHeader>
                        
                        <p>{property.description}</p>
                        
                        {property.images?.length > 0 && (
                          <div>
                            <h4>Images:</h4>
                            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', padding: '10px 0' }}>
                              {property.images.map((img, index) => (
                                <img 
                                  key={index} 
                                  src={img} 
                                  alt={`Property ${index+1}`} 
                                  style={{ 
                                    height: '120px', 
                                    borderRadius: '8px',
                                    objectFit: 'cover'
                                  }} 
                                />
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {property.documents?.length > 0 && (
                          <div>
                            <h4>Documents:</h4>
                            <ul>
                              {property.documents.map((doc, index) => (
                                <li key={index}>
                                  <a href={doc} target="_blank" rel="noopener noreferrer">
                                    Document {index+1}
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {property.verification_status === 'rejected' && property.rejection_reason && (
                          <div>
                            <h4>Rejection Reason:</h4>
                            <p style={{ color: '#F44336' }}>{property.rejection_reason}</p>
                          </div>
                        )}
                      </PropertyCard>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}

export default LandRepManageProperties; 
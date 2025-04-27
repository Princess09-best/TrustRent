import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin: 0;
`;

const Tabs = styled.div`
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const Tab = styled.button`
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 3px solid ${props => props.active ? props.theme.colors.primary : 'transparent'};
  color: ${props => props.active ? props.theme.colors.primary : props.theme.colors.black};
  font-weight: ${props => props.active ? '600' : '400'};
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 10px;

  &:hover {
    color: ${props => props.theme.colors.primary};
  }
`;

const SearchContainer = styled.div`
  display: flex;
  margin-bottom: 20px;
  gap: 10px;
`;

const SearchInput = styled.input`
  flex: 1;
  padding: 10px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  font-size: 16px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button`
  padding: 10px 20px;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #006666;
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
`;

const TableHeader = styled.th`
  padding: 12px 15px;
  text-align: left;
  background-color: #f8f8f8;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  color: #555;
`;

const TableRow = styled.tr`
  &:hover {
    background-color: #f5f5f5;
  }
  cursor: pointer;
`;

const TableCell = styled.td`
  padding: 12px 15px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const StatusBadge = styled.span`
  font-size: 12px;
  padding: 4px 8px;
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

const ActionButton = styled.button`
  padding: 6px 12px;
  background-color: ${props => props.primary ? props.theme.colors.primary : 'transparent'};
  color: ${props => props.primary ? 'white' : props.theme.colors.primary};
  border: 1px solid ${props => props.primary ? 'transparent' : props.theme.colors.primary};
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 8px;

  &:hover {
    background-color: ${props => props.primary ? '#006666' : '#e6f2f2'};
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px 0;
  color: #757575;
`;

const ErrorMessage = styled.p`
  color: ${props => props.theme.colors.error};
  margin-top: 5px;
  font-size: 14px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
`;

function LandRepManageProperties() {
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('all'); // all, pending, verified, rejected
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProperties();
  }, [tab]);

  const fetchProperties = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      // Endpoint will vary based on the selected tab
      let endpoint = '/api/land-rep/properties/';
      if (tab !== 'all') {
        endpoint = `/api/land-rep/properties/${tab}/`;
      }

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch properties');
      }

      const data = await response.json();
      setProperties(data);
    } catch (err) {
      setError('Failed to load properties. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (propertyId) => {
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

      // Update the property in the list
      setProperties(prev => 
        prev.map(property => 
          property.id === propertyId 
            ? { ...property, verification_status: 'VERIFIED' } 
            : property
        )
      );
    } catch (err) {
      setError('Failed to verify property. Please try again.');
      console.error(err);
    }
  };

  const handleReject = async (propertyId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) {
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

      // Update the property in the list
      setProperties(prev => 
        prev.map(property => 
          property.id === propertyId 
            ? { ...property, verification_status: 'REJECTED', rejection_reason: reason } 
            : property
        )
      );
    } catch (err) {
      setError('Failed to reject property. Please try again.');
      console.error(err);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredProperties = properties.filter(property => 
    property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    property.owner_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    property.city.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleRowClick = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Container>
        <LoadingSpinner>Loading properties...</LoadingSpinner>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Title>Manage Properties</Title>
      </Header>

      <Tabs>
        <Tab active={tab === 'all'} onClick={() => setTab('all')}>
          All Properties
        </Tab>
        <Tab active={tab === 'pending'} onClick={() => setTab('pending')}>
          Pending Verification
        </Tab>
        <Tab active={tab === 'verified'} onClick={() => setTab('verified')}>
          Verified
        </Tab>
        <Tab active={tab === 'rejected'} onClick={() => setTab('rejected')}>
          Rejected
        </Tab>
      </Tabs>

      <SearchContainer>
        <SearchInput 
          type="text" 
          placeholder="Search by address, owner, or city..."
          value={searchTerm}
          onChange={handleSearch}
        />
      </SearchContainer>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {filteredProperties.length === 0 ? (
        <EmptyState>
          No properties found matching your filters
        </EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <TableHeader>ID</TableHeader>
              <TableHeader>Address</TableHeader>
              <TableHeader>Owner</TableHeader>
              <TableHeader>City</TableHeader>
              <TableHeader>Submitted</TableHeader>
              <TableHeader>Status</TableHeader>
              <TableHeader>Actions</TableHeader>
            </tr>
          </thead>
          <tbody>
            {filteredProperties.map(property => (
              <TableRow key={property.id}>
                <TableCell onClick={() => handleRowClick(property.id)}>{property.id}</TableCell>
                <TableCell onClick={() => handleRowClick(property.id)}>{property.address}</TableCell>
                <TableCell onClick={() => handleRowClick(property.id)}>{property.owner_name}</TableCell>
                <TableCell onClick={() => handleRowClick(property.id)}>{property.city}</TableCell>
                <TableCell onClick={() => handleRowClick(property.id)}>{formatDate(property.created_at)}</TableCell>
                <TableCell onClick={() => handleRowClick(property.id)}>
                  <StatusBadge status={property.verification_status}>
                    {property.verification_status}
                  </StatusBadge>
                </TableCell>
                <TableCell>
                  {property.verification_status === 'PENDING' && (
                    <>
                      <ActionButton primary onClick={() => handleVerify(property.id)}>
                        Verify
                      </ActionButton>
                      <ActionButton onClick={() => handleReject(property.id)}>
                        Reject
                      </ActionButton>
                    </>
                  )}
                  {property.verification_status === 'REJECTED' && (
                    <ActionButton primary onClick={() => handleVerify(property.id)}>
                      Verify
                    </ActionButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}

export default LandRepManageProperties; 
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

const StatusFilter = styled.div`
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
`;

const StatusFilterButton = styled.button`
  padding: 5px 10px;
  background-color: ${props => props.active ? props.theme.colors.primary : '#f5f5f5'};
  color: ${props => props.active ? 'white' : '#333'};
  border: 1px solid ${props => props.active ? props.theme.colors.primary : '#ddd'};
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: ${props => props.active ? props.theme.colors.primary : '#e0e0e0'};
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

function RentalAgreementList() {
  const navigate = useNavigate();
  const [agreements, setAgreements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('all'); // all, owner, tenant
  const [statusFilter, setStatusFilter] = useState('all'); // all, pending, active, terminated, expired
  const [userRole, setUserRole] = useState('');

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
      } catch (err) {
        console.error('Error fetching user info:', err);
        setError('Failed to load user information');
      }
    };

    const fetchAgreements = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Change the endpoint based on the active tab
        let endpoint = '/api/trustchain/rental/';
        if (tab === 'owner') {
          endpoint = '/api/trustchain/rental/owner/';
        } else if (tab === 'tenant') {
          endpoint = '/api/trustchain/rental/tenant/';
        }

        const response = await fetch(endpoint, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch rental agreements');
        }

        let data = await response.json();

        // Apply status filter
        if (statusFilter !== 'all') {
          data = data.filter(agreement => agreement.status === statusFilter.toUpperCase());
        }

        setAgreements(data);
      } catch (err) {
        setError('Failed to load rental agreements. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo();
    fetchAgreements();
  }, [tab, statusFilter, navigate]);

  const handleCreateNew = () => {
    navigate('/rental-agreements/create');
  };

  const handleRowClick = (agreementId) => {
    navigate(`/rental-agreements/${agreementId}`);
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
        <LoadingSpinner>Loading rental agreements...</LoadingSpinner>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Title>Rental Agreements</Title>
        {userRole === 'property_owner' && (
          <Button onClick={handleCreateNew}>Create New</Button>
        )}
      </Header>

      <Tabs>
        <Tab active={tab === 'all'} onClick={() => setTab('all')}>
          All Agreements
        </Tab>
        <Tab active={tab === 'owner'} onClick={() => setTab('owner')}>
          As Owner
        </Tab>
        <Tab active={tab === 'tenant'} onClick={() => setTab('tenant')}>
          As Tenant
        </Tab>
      </Tabs>

      <StatusFilter>
        <StatusFilterButton 
          active={statusFilter === 'all'} 
          onClick={() => setStatusFilter('all')}
        >
          All
        </StatusFilterButton>
        <StatusFilterButton 
          active={statusFilter === 'pending'} 
          onClick={() => setStatusFilter('pending')}
        >
          Pending
        </StatusFilterButton>
        <StatusFilterButton 
          active={statusFilter === 'active'} 
          onClick={() => setStatusFilter('active')}
        >
          Active
        </StatusFilterButton>
        <StatusFilterButton 
          active={statusFilter === 'terminated'} 
          onClick={() => setStatusFilter('terminated')}
        >
          Terminated
        </StatusFilterButton>
        <StatusFilterButton 
          active={statusFilter === 'expired'} 
          onClick={() => setStatusFilter('expired')}
        >
          Expired
        </StatusFilterButton>
      </StatusFilter>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {agreements.length === 0 ? (
        <EmptyState>
          No rental agreements found matching your filters
        </EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <TableHeader>ID</TableHeader>
              <TableHeader>Property</TableHeader>
              <TableHeader>Other Party</TableHeader>
              <TableHeader>Start Date</TableHeader>
              <TableHeader>End Date</TableHeader>
              <TableHeader>Monthly Rent</TableHeader>
              <TableHeader>Status</TableHeader>
            </tr>
          </thead>
          <tbody>
            {agreements.map(agreement => (
              <TableRow key={agreement.agreement_id} onClick={() => handleRowClick(agreement.agreement_id)}>
                <TableCell>{agreement.agreement_id}</TableCell>
                <TableCell>
                  {agreement.property.address}, {agreement.property.city}
                </TableCell>
                <TableCell>
                  {userRole === 'property_owner' 
                    ? `${agreement.tenant.first_name} ${agreement.tenant.last_name}`
                    : `${agreement.owner.first_name} ${agreement.owner.last_name}`
                  }
                </TableCell>
                <TableCell>{formatDate(agreement.start_date)}</TableCell>
                <TableCell>{formatDate(agreement.end_date)}</TableCell>
                <TableCell>{formatCurrency(agreement.monthly_rent)}</TableCell>
                <TableCell>
                  <StatusBadge status={agreement.status}>
                    {agreement.status}
                  </StatusBadge>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}

export default RentalAgreementList; 
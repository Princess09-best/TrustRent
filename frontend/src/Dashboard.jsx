import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 50px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
`;

const WelcomeSection = styled.div`
  margin-bottom: 50px;
  text-align: center;
  background-color: ${props => props.theme.colors.primary};
  padding: 30px;
  border-radius: 12px;
  color: white;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 20px;
  font-size: 2.2rem;
  text-align: center;
`;

const Subtitle = styled.p`
  color: #555;
  font-size: 1.15rem;
  margin-bottom: 40px;
  text-align: center;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
`;

const DashboardLayout = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 40px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const DashboardMainContent = styled.div`
  display: flex;
  flex-direction: column;
`;

const DashboardSidebar = styled.div`
  display: flex;
  flex-direction: column;
`;

const SectionTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 20px;
  color: ${props => props.theme.colors.primary};
  position: relative;
  padding-bottom: 10px;
  
  &:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 50px;
    height: 3px;
    background-color: ${props => props.theme.colors.primary};
  }
`;

const CardsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
`;

const Card = styled(Link)`
  display: flex;
  flex-direction: column;
  padding: 30px;
  background-color: #f9f9f9;
  border-radius: 12px;
  border-left: 5px solid ${props => props.theme.colors.primary};
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  min-height: 180px;
  justify-content: space-between;
  
  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
    background-color: #ffffff;
  }
`;

const CardTitle = styled.h3`
  font-size: 1.4rem;
  margin-bottom: 15px;
  color: ${props => props.theme.colors.primary};
`;

const CardDescription = styled.p`
  font-size: 1rem;
  color: #666;
  line-height: 1.6;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 25px;
  margin-bottom: 30px;
`;

const StatCard = styled.div`
  background: linear-gradient(145deg, ${props => props.theme.colors.primary}, ${props => `${props.theme.colors.primary}CC`});
  color: white;
  padding: 25px 30px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
  }
`;

const StatNumber = styled.div`
  font-size: 2.8rem;
  font-weight: 700;
  margin-bottom: 10px;
`;

const StatLabel = styled.div`
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  font-size: 1.2rem;
  color: ${props => props.theme.colors.primary};
`;

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    properties: 0,
    agreements: 0,
    pendingVerifications: 0,
    pendingProperties: 0
  });

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch user profile
        const response = await fetch('/api/user/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          // If unauthorized, clear token and redirect to login
          if (response.status === 401) {
            localStorage.removeItem('token');
            navigate('/login');
            return;
          }
          throw new Error('Failed to fetch user profile');
        }

        const userData = await response.json();
        setUser(userData);

        // Fetch statistics based on user role
        await fetchRoleBasedStats(userData.role, token);
      } catch (error) {
        console.error('Error fetching user profile:', error);
        // On error, redirect to login
        localStorage.removeItem('token');
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, [navigate]);

  const fetchRoleBasedStats = async (role, token) => {
    try {
      // Different endpoints based on role
      let endpoint = '';
      
      switch(role) {
        case 'admin':
          endpoint = '/api/admin/stats/';
          break;
        case 'land_rep':
          endpoint = '/api/land-rep/stats/';
          break;
        case 'property_owner':
          endpoint = '/api/property/owner-stats/';
          break;
        case 'property_seeker':
          endpoint = '/api/property/seeker-stats/';
          break;
        default:
          return;
      }
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }
      
      const statsData = await response.json();
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching statistics:', error);
      // Set default stats if fetching fails
      setStats({
        properties: 0,
        agreements: 0,
        pendingVerifications: 0,
        pendingProperties: 0
      });
    }
  };

  if (loading) {
    return (
      <Container>
        <LoadingSpinner>Loading dashboard...</LoadingSpinner>
      </Container>
    );
  }

  if (!user) {
    navigate('/login');
    return null;
  }

  // Render different features based on user role
  const renderRoleBasedFeatures = () => {
    const role = user?.role;

    if (role === 'admin' || role === 'sys_admin') {
      return (
        <>
          <Title>Admin Dashboard</Title>
          <Subtitle>Manage users, verify accounts, and oversee system operations</Subtitle>
          
          <DashboardLayout>
            <DashboardMainContent>
              <SectionTitle>Administration</SectionTitle>
              <CardsContainer>
                <Card to="/admin/verify-users">
                  <CardTitle>Verify Users</CardTitle>
                  <CardDescription>
                    Review and approve new user registration requests
                  </CardDescription>
                </Card>
                <Card to="/admin/create-account">
                  <CardTitle>Create Admin Account</CardTitle>
                  <CardDescription>
                    Create new admin or land representative accounts
                  </CardDescription>
                </Card>
                <Card to="/rental-agreements">
                  <CardTitle>View Agreements</CardTitle>
                  <CardDescription>
                    Browse all rental agreements in the system
                  </CardDescription>
                </Card>
                <Card to="/admin/blockchain-verification">
                  <CardTitle>Blockchain Verification</CardTitle>
                  <CardDescription>
                    Verify the integrity of the property blockchain
                  </CardDescription>
                </Card>
              </CardsContainer>
            </DashboardMainContent>
            
            <DashboardSidebar>
              <SectionTitle>System Overview</SectionTitle>
              <StatsContainer style={{ gridTemplateColumns: '1fr' }}>
                <StatCard>
                  <StatNumber>{stats.properties}</StatNumber>
                  <StatLabel>Total Properties</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.agreements}</StatNumber>
                  <StatLabel>Total Agreements</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.pendingVerifications}</StatNumber>
                  <StatLabel>Pending User Verifications</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.pendingProperties}</StatNumber>
                  <StatLabel>Pending Property Verifications</StatLabel>
                </StatCard>
              </StatsContainer>
            </DashboardSidebar>
          </DashboardLayout>
        </>
      );
    }
    
    if (role === 'land_rep') {
      return (
        <>
          <Title>Land Representative Dashboard</Title>
          <Subtitle>Verify properties and ensure compliance with regulations</Subtitle>
          
          <CardsContainer>
            <Card to="/land-rep/manage-properties">
              <CardTitle>Manage Properties</CardTitle>
              <CardDescription>
                Review, verify, and manage property listings
              </CardDescription>
            </Card>
          </CardsContainer>
          
          <StatsContainer>
            <StatCard>
              <StatNumber>{stats.properties}</StatNumber>
              <StatLabel>Total Properties</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.pendingProperties}</StatNumber>
              <StatLabel>Pending Verification</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.verifiedProperties}</StatNumber>
              <StatLabel>Verified Properties</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.rejectedProperties}</StatNumber>
              <StatLabel>Rejected Properties</StatLabel>
            </StatCard>
          </StatsContainer>
        </>
      );
    }
    
    if (role === 'property_owner') {
      return (
        <>
          <Title>Property Owner Dashboard</Title>
          <Subtitle>Manage your properties and rental agreements</Subtitle>
          
          <DashboardLayout>
            <DashboardMainContent>
              <SectionTitle>Quick Actions</SectionTitle>
              <CardsContainer>
                <Card to="/create-property">
                  <CardTitle>Create Property</CardTitle>
                  <CardDescription>
                    List a new property for rent
                  </CardDescription>
                </Card>
                <Card to="/my-properties">
                  <CardTitle>My Properties</CardTitle>
                  <CardDescription>
                    View and manage your property listings
                  </CardDescription>
                </Card>
                <Card to="/rental-agreements">
                  <CardTitle>Rental Agreements</CardTitle>
                  <CardDescription>
                    View and manage your rental agreements
                  </CardDescription>
                </Card>
                <Card to="/document-requests">
                  <CardTitle>Document Requests</CardTitle>
                  <CardDescription>
                    Manage document access requests from property seekers
                  </CardDescription>
                </Card>
                <Card to="/property-transfers">
                  <CardTitle>Property Transfers</CardTitle>
                  <CardDescription>
                    View and manage property ownership transfers
                  </CardDescription>
                </Card>
              </CardsContainer>
            </DashboardMainContent>
            
            <DashboardSidebar>
              <SectionTitle>Overview</SectionTitle>
              <StatsContainer style={{ gridTemplateColumns: '1fr' }}>
                <StatCard>
                  <StatNumber>{stats.total_properties || 0}</StatNumber>
                  <StatLabel>Total Properties</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.verified_properties || 0}</StatNumber>
                  <StatLabel>Verified Properties</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.pending_properties || 0}</StatNumber>
                  <StatLabel>Pending Verification</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.active_listings || 0}</StatNumber>
                  <StatLabel>Active Listings</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.total_agreements || 0}</StatNumber>
                  <StatLabel>Total Agreements</StatLabel>
                </StatCard>
                <StatCard>
                  <StatNumber>{stats.pending_agreements || 0}</StatNumber>
                  <StatLabel>Pending Agreements</StatLabel>
                </StatCard>
              </StatsContainer>
            </DashboardSidebar>
          </DashboardLayout>
        </>
      );
    }
    
    if (role === 'property_seeker') {
      return (
        <>
          <Title>Property Seeker Dashboard</Title>
          <Subtitle>Find properties and manage your rental agreements</Subtitle>
          
          <CardsContainer>
            <Card to="/rental-agreements">
              <CardTitle>Rental Agreements</CardTitle>
              <CardDescription>
                View and manage your rental agreements
              </CardDescription>
            </Card>
            {/* 
              Property search would be added here
              <Card to="/search-properties">
                <CardTitle>Search Properties</CardTitle>
                <CardDescription>
                  Find and view available properties for rent
                </CardDescription>
              </Card>
            */}
          </CardsContainer>
          
          <StatsContainer>
            <StatCard>
              <StatNumber>{stats.agreements}</StatNumber>
              <StatLabel>Your Agreements</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.pendingAgreements}</StatNumber>
              <StatLabel>Pending Agreements</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.activeAgreements}</StatNumber>
              <StatLabel>Active Agreements</StatLabel>
            </StatCard>
            <StatCard>
              <StatNumber>{stats.propertiesViewed}</StatNumber>
              <StatLabel>Properties Viewed</StatLabel>
            </StatCard>
          </StatsContainer>
        </>
      );
    }
    
    return (
      <>
        <Title>Welcome to TrustRent</Title>
        <Subtitle>Please contact support - your account role is not recognized</Subtitle>
      </>
    );
  };

  return (
    <Container>
      <WelcomeSection>
        <h2 style={{ fontSize: '2.2rem', marginBottom: '10px', fontWeight: '600' }}>
          Welcome, {user?.first_name} {user?.last_name}
        </h2>
        <p style={{ fontSize: '1.2rem', opacity: '0.9' }}>
          Here's what you can do with your {user?.role?.replace('_', ' ')} account
        </p>
      </WelcomeSection>
      
      {renderRoleBasedFeatures()}
    </Container>
  );
}

export default Dashboard; 
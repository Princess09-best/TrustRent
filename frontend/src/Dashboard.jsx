import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

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

const Card = styled.div`
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

function Dashboard({ devMode = false, devRole = null }) {
  const navigate = useNavigate();
  const { currentUser, userRole, isAuthenticated, loading: authLoading } = useAuth();
  const [stats, setStats] = useState({
    properties: 0,
    agreements: 0,
    pendingVerifications: 0,
    pendingProperties: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      // If in development mode, create mock data
      if (devMode) {
        // Use the user from auth context if available, otherwise create mock user
        const role = devRole || userRole;
        
        // Set mock stats based on role
        if (role === 'admin') {
          setStats({
            properties: 45,
            agreements: 28,
            pendingVerifications: 7,
            pendingProperties: 12
          });
        } else if (role === 'land_rep') {
          setStats({
            properties: 45,
            pendingProperties: 12,
            verifiedProperties: 30,
            rejectedProperties: 3
          });
        } else if (role === 'property_owner') {
          setStats({
            properties: 5,
            agreements: 3,
            pendingAgreements: 1,
            activeAgreements: 2
          });
        } else if (role === 'property_seeker') {
          setStats({
            agreements: 2,
            pendingAgreements: 1,
            activeAgreements: 1,
            propertiesViewed: 15
          });
        }
        
        setLoading(false);
        return;
      }

      // In production, use the authenticated user from context
      if (!isAuthenticated && !devMode) {
        navigate('/login');
        return;
      }

      try {
        const token = localStorage.getItem('token');
        
        // Fetch dashboard stats from the API
        const response = await fetch('/api/dashboard/stats/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const statsData = await response.json();
          setStats(statsData);
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [navigate, devMode, devRole, isAuthenticated, userRole]);

  if (loading || authLoading) {
    return (
      <Container>
        <LoadingSpinner>Loading dashboard...</LoadingSpinner>
      </Container>
    );
  }

  // Determine which user object to use (dev mock or authenticated user)
  const user = devMode ? 
    { first_name: 'Dev', last_name: 'User', role: devRole || 'property_owner' } : 
    currentUser;

  // Render different features based on user role
  const renderRoleBasedFeatures = () => {
    // Use the role from the dev mode or from the authenticated user
    const role = devMode ? devRole : userRole;
    
    console.log("Current role in Dashboard:", role);

    if (role === 'admin' || role === 'sys_admin') {
      // Admin dashboard content
      return (
        <>
          <Title>Admin Dashboard</Title>
          <Subtitle>Manage users, verify accounts, and oversee system operations</Subtitle>
          
          <DashboardLayout>
            <DashboardMainContent>
              <SectionTitle>Administration</SectionTitle>
              <CardsContainer>
                <Card onClick={() => navigate('/admin/verify-users')}>
                  <CardTitle>Verify Users</CardTitle>
                  <CardDescription>
                    Review and approve new user registration requests
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/admin/create-account')}>
                  <CardTitle>Create Admin Account</CardTitle>
                  <CardDescription>
                    Create new admin or land representative accounts
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/rental-agreements')}>
                  <CardTitle>View Agreements</CardTitle>
                  <CardDescription>
                    Browse all rental agreements in the system
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/admin/blockchain-verification')}>
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
    
    if (role === 'land_rep' || role === 'land_commission_rep') {
      return (
        <>
          <Title>Land Representative Dashboard</Title>
          <Subtitle>Verify properties and ensure compliance with regulations</Subtitle>
          
          <CardsContainer>
            <Card onClick={() => navigate('/land-rep/manage-properties')}>
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
                <Card onClick={() => navigate('/create-property')}>
                  <CardTitle>Create Property</CardTitle>
                  <CardDescription>
                    List a new property for rent
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/my-properties')}>
                  <CardTitle>My Properties</CardTitle>
                  <CardDescription>
                    View and manage your property listings
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/my-listings')}>
                  <CardTitle>My Listings</CardTitle>
                  <CardDescription>
                    Manage your active property listings
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/rental-agreements')}>
                  <CardTitle>Rental Agreements</CardTitle>
                  <CardDescription>
                    View and manage your rental agreements
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/document-requests')}>
                  <CardTitle>Document Requests</CardTitle>
                  <CardDescription>
                    Manage document access requests from property seekers
                  </CardDescription>
                </Card>
                <Card onClick={() => navigate('/property-transfers')}>
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
            <Card onClick={() => navigate('/browse-properties')}>
              <CardTitle>Browse Properties</CardTitle>
              <CardDescription>
                Find and view available properties
              </CardDescription>
            </Card>
            <Card onClick={() => navigate('/verify-ownership')}>
              <CardTitle>Verify Property Ownership</CardTitle>
              <CardDescription>
                Use blockchain to verify property ownership claims
              </CardDescription>
            </Card>
            <Card onClick={() => navigate('/rental-agreements')}>
              <CardTitle>Rental Agreements</CardTitle>
              <CardDescription>
                View and manage your rental agreements
              </CardDescription>
            </Card>
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
        <Title>Welcome to BAWRA</Title>
        <Subtitle>Please contact support - your account role is not recognized</Subtitle>
      </>
    );
  };

  return (
    <Container>
      <WelcomeSection>
        <h2 style={{ fontSize: '2.2rem', marginBottom: '10px', fontWeight: '600' }}>
          Welcome, {currentUser?.first_name && currentUser?.last_name ? 
            `${currentUser.first_name} ${currentUser.last_name}` : 'Dev User'}
        </h2>
        <p style={{ fontSize: '1.2rem', opacity: '0.9' }}>
          Here's what you can do with your {(devMode ? devRole : userRole)?.replace('_', ' ')} account
        </p>
      </WelcomeSection>
      
      {renderRoleBasedFeatures()}
    </Container>
  );
}

export default Dashboard; 
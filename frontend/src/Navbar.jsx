import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import styled from 'styled-components';

const NavbarContainer = styled.nav`
  width: 100%;
  background-color: ${props => props.theme.colors.white};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 15px 20px;
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: ${props => props.theme.colors.primary};
`;

const NavLinks = styled.div`
  display: flex;
  gap: 20px;
`;

const NavLink = styled(Link)`
  color: ${props => props.theme.colors.black};
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  position: relative;
  
  &:hover {
    background-color: #f5f5f5;
  }

  ${props => props.active && `
    color: ${props.theme.colors.primary};
    font-weight: 500;
    
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 2px;
      background-color: ${props.theme.colors.primary};
    }
  `}
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
`;

const UserInfo = styled.div`
  display: flex;
  flex-direction: column;
  font-size: 14px;
`;

const UserName = styled.span`
  font-weight: 500;
`;

const UserRole = styled.span`
  color: #666;
  font-size: 12px;
`;

const LogoutButton = styled.button`
  background-color: transparent;
  border: 1px solid ${props => props.theme.colors.error};
  color: ${props => props.theme.colors.error};
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    background-color: ${props => props.theme.colors.error};
    color: white;
  }
`;

function Navbar() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

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

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  // Determine which links to show based on user role
  const renderNavLinks = () => {
    if (loading || !user) return null;

    const isActive = (path) => location.pathname === path;
    
    // Common links for all users
    const links = [
      <NavLink key="dashboard" to="/dashboard" active={isActive('/dashboard')}>
        Dashboard
      </NavLink>
    ];

    // Role-specific links
    switch(user.role) {
      case 'admin':
        links.push(
          <NavLink key="verify-users" to="/admin/verify-users" active={isActive('/admin/verify-users')}>
            Verify Users
          </NavLink>,
          <NavLink key="create-account" to="/admin/create-account" active={isActive('/admin/create-account')}>
            Create Account
          </NavLink>,
          <NavLink key="blockchain" to="/admin/blockchain-verification" active={isActive('/admin/blockchain-verification')}>
            Blockchain
          </NavLink>
        );
        break;
      case 'land_rep':
        links.push(
          <NavLink key="manage-properties" to="/land-rep/manage-properties" active={isActive('/land-rep/manage-properties')}>
            Manage Properties
          </NavLink>
        );
        break;
      case 'property_owner':
        links.push(
          <NavLink key="create-property" to="/create-property" active={isActive('/create-property')}>
            Create Property
          </NavLink>,
          <NavLink key="rental-agreements" to="/rental-agreements" active={isActive('/rental-agreements')}>
            Rental Agreements
          </NavLink>
        );
        break;
      case 'property_seeker':
        links.push(
          <NavLink key="properties" to="/properties" active={isActive('/properties')}>
            Find Properties
          </NavLink>,
          <NavLink key="rental-agreements" to="/rental-agreements" active={isActive('/rental-agreements')}>
            Rental Agreements
          </NavLink>
        );
        break;
      default:
        break;
    }

    return links;
  };

  return (
    <NavbarContainer>
      <Logo>
        <Link to="/dashboard" style={{ textDecoration: 'none', color: 'inherit' }}>
          TrustRent
        </Link>
      </Logo>
      
      <NavLinks>
        {renderNavLinks()}
      </NavLinks>
      
      <UserSection>
        {!loading && user && (
          <>
            <UserInfo>
              <UserName>{user.first_name} {user.last_name}</UserName>
              <UserRole>{user.role.replace('_', ' ')}</UserRole>
            </UserInfo>
            <LogoutButton onClick={handleLogout}>Logout</LogoutButton>
          </>
        )}
      </UserSection>
    </NavbarContainer>
  );
}

export default Navbar;
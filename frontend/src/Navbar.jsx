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
          setLoading(false);
          return;
        }

        const response = await fetch('/api/users/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user profile');
        }

        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        console.error('Error fetching user profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return null;
  }

  // Don't show navbar on login and register pages
  if (['/login', '/register', '/verification-pending'].includes(location.pathname)) {
    return null;
  }

  if (!user) {
    navigate('/login');
    return null;
  }

  const isActive = (path) => {
    if (path === '/rental-agreements' && location.pathname.startsWith('/rental-agreements')) {
      return true;
    }
    return location.pathname === path;
  };

  return (
    <NavbarContainer>
      <Logo>TrustRent</Logo>
      
      <NavLinks>
        {user.role === 'admin' && (
          <>
            <NavLink to="/admin/verify-users" active={isActive('/admin/verify-users')}>
              Verify Users
            </NavLink>
            <NavLink to="/admin/create-account" active={isActive('/admin/create-account')}>
              Create Admin
            </NavLink>
          </>
        )}
        
        {user.role === 'land_rep' && (
          <NavLink to="/land-rep/manage-properties" active={isActive('/land-rep/manage-properties')}>
            Manage Properties
          </NavLink>
        )}
        
        {user.role === 'property_owner' && (
          <>
            <NavLink to="/create-property" active={isActive('/create-property')}>
              Create Property
            </NavLink>
            <NavLink to="/rental-agreements" active={isActive('/rental-agreements')}>
              Rental Agreements
            </NavLink>
          </>
        )}
        
        {user.role === 'property_seeker' && (
          <NavLink to="/rental-agreements" active={isActive('/rental-agreements')}>
            Rental Agreements
          </NavLink>
        )}
      </NavLinks>
      
      <UserSection>
        <UserInfo>
          <UserName>{user.first_name} {user.last_name}</UserName>
          <UserRole>{user.role.replace('_', ' ')}</UserRole>
        </UserInfo>
        <LogoutButton onClick={handleLogout}>Logout</LogoutButton>
      </UserSection>
    </NavbarContainer>
  );
}

export default Navbar; 
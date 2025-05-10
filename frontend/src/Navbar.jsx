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

function Navbar({ devMode = false, devRole = null }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const fetchUserProfile = async () => {
      // If in development mode, create a mock user
      if (devMode) {
        setUser({
          first_name: 'Dev',
          last_name: 'User',
          email: 'dev@example.com',
          role: devRole || 'property_owner',
          is_verified: true
        });
        setLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await fetch('/api/user/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user profile');
        }

        const userData = await response.json();
        setUser(userData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching user profile:', error);
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, [devMode, devRole]);

  return (
    <NavbarContainer>
      {/* Rest of the component code remains unchanged */}
    </NavbarContainer>
  );
}

export default Navbar;
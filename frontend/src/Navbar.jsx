import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

const NavbarContainer = styled.nav`
  width: 100%;
  background-color: ${props => props.theme.colors.white};
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 15px 0;
  position: sticky;
  top: 0;
  z-index: 1000;
`;

const NavbarContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`;

const Logo = styled(Link)`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.theme.colors.primary};
  text-decoration: none;
  transition: opacity 0.3s;
  
  &:hover {
    opacity: 0.8;
  }
`;

const NavLinks = styled.div`
  display: flex;
  gap: 30px;
  align-items: center;
  
  @media (max-width: 768px) {
    display: ${props => (props.isOpen ? 'flex' : 'none')};
    flex-direction: column;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    background-color: ${props => props.theme.colors.white};
    padding: 20px;
    box-shadow: 0 5px 10px rgba(0, 0, 0, 0.1);
    align-items: flex-start;
  }
`;

const NavLink = styled(Link)`
  color: #333;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
  
  &:hover {
    color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button`
  padding: 8px 16px;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
  
  &:hover {
    background-color: #006666;
  }
`;

const MobileMenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  
  @media (max-width: 768px) {
    display: block;
  }
`;

const Navbar = ({ devMode = false, devRole = null }) => {
  const navigate = useNavigate();
  const { isAuthenticated, userRole, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  // Determine role (from development mode or authenticated user)
  const role = devMode ? devRole : userRole;

  // Render different links based on user role
  const renderRoleBasedLinks = () => {
    if (role === 'admin' || role === 'sys_admin') {
      return (
        <>
          <NavLink to="/admin/verify-users">Verify Users</NavLink>
          <NavLink to="/admin/create-account">Create Admin</NavLink>
          <NavLink to="/admin/blockchain-verification">Blockchain</NavLink>
        </>
      );
    }
    
    if (role === 'land_rep') {
      return (
        <NavLink to="/land-rep/manage-properties">Manage Properties</NavLink>
      );
    }
    
    if (role === 'property_owner') {
      return (
        <>
          <NavLink to="/create-property">Create Property</NavLink>
          <NavLink to="/my-properties">My Properties</NavLink>
        </>
      );
    }
    
    return null;
  };

  return (
    <NavbarContainer>
      <NavbarContent>
        <Logo to="/dashboard">TrustRent</Logo>
        
        <MobileMenuButton onClick={toggleMenu}>
          ☰
        </MobileMenuButton>
        
        <NavLinks isOpen={isMenuOpen}>
          {/* Common links for all authenticated users */}
          {(isAuthenticated || devMode) && (
            <>
              <NavLink to="/dashboard">Dashboard</NavLink>
              <NavLink to="/rental-agreements">Agreements</NavLink>
              {renderRoleBasedLinks()}
              <Button onClick={handleLogout}>Logout</Button>
            </>
          )}
          
          {/* Links for non-authenticated users (should not be visible, as navbar is hidden on landing page) */}
          {!isAuthenticated && !devMode && (
            <>
              <NavLink to="/login">Login</NavLink>
              <NavLink to="/register">Register</NavLink>
            </>
          )}
        </NavLinks>
      </NavbarContent>
    </NavbarContainer>
  );
};

export default Navbar;
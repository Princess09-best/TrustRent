import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

// Create the auth context
export const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Function to check if the user is authenticated
  const checkAuthStatus = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');
    
    if (!token) {
      setIsAuthenticated(false);
      setCurrentUser(null);
      setUserRole(null);
      setLoading(false);
      return;
    }

    try {
      // Get user profile data
      const response = await axios.get('/api/user/profile/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 200) {
        const userData = response.data;
        setCurrentUser(userData);
        setUserRole(userData.role);
        setIsAuthenticated(true);
      } else {
        // If any error, clear the token
        logout();
      }
    } catch (error) {
      setError('Failed to fetch user data. Please login again.');
      logout();
    } finally {
      setLoading(false);
    }
  };

  // Login function
  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/user/login/', { email, password });
      
      // Get token from Authorization header 
      const token = response.headers['authorization']?.split(' ')[1];
      
      if (token) {
        // Store the token
        localStorage.setItem('token', token);
        
        // Get user profile data
        await checkAuthStatus();
        return { success: true };
      } else {
        throw new Error('No token received from server');
      }
    } catch (error) {
      setLoading(false);
      
      if (error.response) {
        // Handle verification pending case
        if (error.response.status === 403 && error.response.data.is_verified === false) {
          return { 
            success: false, 
            redirectTo: '/verification-pending'
          };
        }
        setError(error.response.data.error || 'Invalid credentials. Please try again.');
      } else if (error.request) {
        setError('No response from server. Please check your connection.');
      } else {
        setError('Something went wrong. Please try again.');
      }
      
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed'
      };
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
    setUserRole(null);
    setIsAuthenticated(false);
  };

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Context value
  const value = {
    currentUser,
    userRole,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider; 
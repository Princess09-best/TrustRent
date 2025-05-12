import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: ${props => props.theme.colors.background};
  padding: 20px;
`;

const FormCard = styled.div`
  background: ${props => props.theme.colors.white};
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.black};
  text-align: center;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 600;
`;

const Message = styled.p`
  text-align: center;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 5px;
  background-color: ${props => props.error ? '#ffe6e6' : '#e6fff9'};
  color: ${props => props.error ? props.theme.colors.error : props.theme.colors.success};
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 5px;
  font-size: 14px;
  transition: border-color 0.3s;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 12px;
  background-color: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.white};
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #006666;
  }

  &:active {
    transform: translateY(1px);
  }
`;

const Form = styled.form`
  width: 100%;
`;

const RegisterLink = styled.div`
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  
  a {
    color: ${props => props.theme.colors.primary};
    text-decoration: none;
    font-weight: 500;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, error: authError, isAuthenticated, loading: authLoading } = useAuth();
  
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  // Redirect to the page they were trying to access, or to dashboard
  const from = location.state?.from?.pathname || '/dashboard';

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleChange = (e) => {
    setFormData({ 
      ...formData, 
      [e.target.name]: e.target.value 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(false);
    setLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      
      if (result.success) {
        // Show success message before redirecting
        setError(false);
        setMessage('Login successful! Redirecting to dashboard...');
      } else if (result.redirectTo) {
        // Handle special case redirects (like verification pending)
        navigate(result.redirectTo);
      } else {
        // Display error from the auth context
        setError(true);
        setMessage(authError || 'Login failed. Please try again.');
      }
    } catch (err) {
      setError(true);
      setMessage('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Show loading if auth context is still loading
  if (authLoading) {
    return (
      <Container>
        <FormCard>
          <Title>Loading...</Title>
        </FormCard>
      </Container>
    );
  }

  return (
    <Container>
      <FormCard>
        <Title>Login to Your Account</Title>
        {message && <Message error={error}>{message}</Message>}
        {authError && !message && <Message error={true}>{authError}</Message>}
        <Form onSubmit={handleSubmit}>
          <Input 
            name="email" 
            type="email" 
            placeholder="Email" 
            onChange={handleChange} 
            value={formData.email}
            required 
          />
          <Input 
            name="password" 
            type="password" 
            placeholder="Password" 
            onChange={handleChange} 
            value={formData.password}
            required 
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </Form>
        <RegisterLink>
          Don't have an account? <a href="/register">Register now</a>
        </RegisterLink>
      </FormCard>
    </Container>
  );
};

export default Login;

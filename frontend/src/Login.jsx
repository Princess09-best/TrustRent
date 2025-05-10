import React, { useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';

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
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

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
      const response = await axios.post('/api/user/login/', formData);
      
      // Get token from Authorization header 
      const token = response.headers['authorization']?.split(' ')[1];
      
      if (token) {
        // Store the token
        localStorage.setItem('token', token);
        
        // Show success message briefly before redirecting
        setError(false);
        setMessage('Login successful! Redirecting to dashboard...');
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } else {
        throw new Error('No token received from server');
      }
    } catch (error) {
      setError(true);
      if (error.response) {
        // If the error is due to verification pending, redirect to verification page
        if (error.response.status === 403 && error.response.data.is_verified === false) {
          navigate('/verification-pending');
          return;
        }
        setMessage(error.response.data.error || 'Invalid credentials. Please try again.');
      } else if (error.request) {
        setMessage('No response from server. Please check your connection.');
      } else {
        setMessage('Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <FormCard>
        <Title>Login to Your Account</Title>
        {message && <Message error={error}>{message}</Message>}
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

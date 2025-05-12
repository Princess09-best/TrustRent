import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
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

const Select = styled.select`
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 5px;
  font-size: 14px;
  background-color: ${props => props.theme.colors.white};
  cursor: pointer;

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

const LoginLink = styled.div`
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

const Register = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    firstname: '',
    lastname: '',
    email: '',
    phone_number: '',
    password: '',
    role: 'property_seeker',
    id_type: 'Ghana Card',
    id_value: ''
  });

  const [message, setMessage] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

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
      const response = await axios.post('/api/user/register/', formData, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      setError(false);
      setMessage(response.data.message || 'Registration successful!');
      
      // Clear form after successful registration
      setFormData({
        firstname: '',
        lastname: '',
        email: '',
        phone_number: '',
        password: '',
        role: 'property_seeker',
        id_type: 'Ghana Card',
        id_value: ''
      });

      // Show success message briefly before redirecting
      setTimeout(() => {
        // Navigate based on verification status
        if (response.data.is_verified) {
          navigate('/login');
        } else {
          navigate('/verification-pending');
        }
      }, 1500);
      
    } catch (error) {
      setError(true);
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setMessage(error.response.data.error || 'Registration failed. Please try again.');
      } else if (error.request) {
        // The request was made but no response was received
        setMessage('No response from server. Please check your connection.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setMessage('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <FormCard>
        <Title>Create an Account</Title>
        {message && <Message error={error}>{message}</Message>}
        <Form onSubmit={handleSubmit}>
          <Input 
            name="firstname" 
            placeholder="First Name"
            value={formData.firstname}
            onChange={handleChange} 
            required 
          />
          <Input 
            name="lastname" 
            placeholder="Last Name"
            value={formData.lastname}
            onChange={handleChange} 
            required 
          />
          <Input 
            name="email" 
            placeholder="Email" 
            type="email"
            value={formData.email}
            onChange={handleChange} 
            required 
          />
          <Input 
            name="phone_number"
            placeholder="Phone Number"
            value={formData.phone_number}
            onChange={handleChange} 
            required 
          />
          <Input 
            name="password" 
            placeholder="Password" 
            type="password"
            value={formData.password}
            onChange={handleChange} 
            required 
          />
          <Select 
            name="role"
            value={formData.role}
            onChange={handleChange}
            required
          >
            <option value="property_seeker">Property Seeker</option>
            <option value="property_owner">Property Owner</option>
          </Select>
          <Select 
            name="id_type"
            value={formData.id_type}
            onChange={handleChange}
            required
          >
            <option value="Ghana Card">Ghana Card</option>
            <option value="Voter ID">Voter ID</option>
            <option value="Passport">Passport</option>
            <option value="Driver License">Driver's License</option>
          </Select>
          <Input 
            name="id_value"
            placeholder="ID Number"
            value={formData.id_value}
            onChange={handleChange} 
            required 
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </Button>
        </Form>
        <LoginLink>
          Already have an account? <a href="/login">Login here</a>
        </LoginLink>
      </FormCard>
    </Container>
  );
};

export default Register;

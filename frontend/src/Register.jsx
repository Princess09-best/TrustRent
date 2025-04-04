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

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstname: '',
    lastname: '',
    email: '',
    phone_number: '',
    password: '',
    role: 'property_buyer',
    id_type: 'Ghana Card',
    id_value: ''
  });

  const [message, setMessage] = useState(null);
  const [error, setError] = useState(false);

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

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/register/', formData, {
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
        role: 'property_buyer',
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
          <Select name="role" onChange={handleChange} value={formData.role}>
            <option value="property_buyer">Buyer</option>
            <option value="property_owner">Owner</option>
          </Select>
          <Select name="id_type" onChange={handleChange} value={formData.id_type}>
            <option value="Ghana Card">Ghana Card</option>
            <option value="Passport">Passport</option>
          </Select>
          <Input 
            name="id_value" 
            placeholder="ID Value"
            value={formData.id_value}
            onChange={handleChange} 
            required 
          />
          <Button type="submit">Register</Button>
        </Form>
      </FormCard>
    </Container>
  );
};

export default Register;

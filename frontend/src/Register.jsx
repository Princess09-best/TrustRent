import React, { useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';

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
      const response = await axios.post('http://127.0.0.1:8000/api/register/', formData);
      setMessage(response.data.message || 'Registration successful!');
    } catch (error) {
      setError(true);
      if (error.response && error.response.data) {
        setMessage(error.response.data.error);
      } else {
        setMessage('Something went wrong. Please try again.');
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
            onChange={handleChange} 
            required 
          />
          <Input 
            name="lastname" 
            placeholder="Last Name" 
            onChange={handleChange} 
            required 
          />
          <Input 
            name="email" 
            placeholder="Email" 
            type="email" 
            onChange={handleChange} 
            required 
          />
          <Input 
            name="phone_number" 
            placeholder="Phone Number" 
            onChange={handleChange} 
            required 
          />
          <Input 
            name="password" 
            placeholder="Password" 
            type="password" 
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

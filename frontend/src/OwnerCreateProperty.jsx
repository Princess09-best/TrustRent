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
  max-width: 600px;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.black};
  text-align: center;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 600;
`;

const Message = styled.div`
  text-align: center;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 5px;
  background-color: ${props => props.error ? '#ffe6e6' : '#e6fff9'};
  color: ${props => props.error ? props.theme.colors.error : props.theme.colors.success};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const Label = styled.label`
  color: ${props => props.theme.colors.black};
  font-weight: 500;
  margin-bottom: 5px;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
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
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 5px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 12px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 5px;
  font-size: 14px;
  min-height: 120px;
  resize: vertical;
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
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 10px;

  &:hover {
    background-color: #006666;
  }

  &:active {
    transform: translateY(1px);
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const PriceInput = styled(Input)`
  &::-webkit-inner-spin-button,
  &::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
`;

const CreateProperty = () => {
  const [formData, setFormData] = useState({
    title: '',
    property_type: '1_bedroom',
    description: '',
    location: '',
    price: '',
    owner_id: localStorage.getItem('user_id')
  });

  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);

  const handleChange = (e) => {
    setFormData({ 
      ...formData, 
      [e.target.name]: e.target.value 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError(false);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/create-property/', formData);
      setError(false);
      setMessage(response.data.message || 'Property created successfully.');
      
      // Clear form after successful submission
      setFormData({
        title: '',
        property_type: '1_bedroom',
        description: '',
        location: '',
        price: '',
        owner_id: localStorage.getItem('user_id')
      });
    } catch (error) {
      setError(true);
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Failed to create property. Please try again.");
      }
    }
  };

  return (
    <Container>
      <FormCard>
        <Title>List Your Property</Title>
        {message && <Message error={error}>{message}</Message>}
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <Label>Property Title</Label>
            <Input
              name="title"
              placeholder="e.g., Modern 2 Bedroom Apartment in East Legon"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </FormGroup>

          <FormGroup>
            <Label>Property Type</Label>
            <Select 
              name="property_type"
              value={formData.property_type}
              onChange={handleChange}
            >
              <option value="1_bedroom">1 Bedroom</option>
              <option value="2_bedroom">2 Bedroom</option>
              <option value="3_bedroom">3 Bedroom</option>
              <option value="4_bedroom">4 Bedroom</option>
              <option value="5_bedroom">5 Bedroom</option>
              <option value="gated_house">Full Gated House</option>
            </Select>
          </FormGroup>

          <FormGroup>
            <Label>Description</Label>
            <TextArea
              name="description"
              placeholder="Describe your property in detail..."
              value={formData.description}
              onChange={handleChange}
              required
            />
          </FormGroup>

          <FormGroup>
            <Label>Location</Label>
            <Input
              name="location"
              placeholder="e.g., East Legon, Accra"
              value={formData.location}
              onChange={handleChange}
              required
            />
          </FormGroup>

          <FormGroup>
            <Label>Price (GHS)</Label>
            <PriceInput
              name="price"
              type="number"
              step="0.01"
              placeholder="e.g., 250000.00"
              value={formData.price}
              onChange={handleChange}
              required
            />
          </FormGroup>

          <Button type="submit">List Property</Button>
        </Form>
      </FormCard>
    </Container>
  );
};

export default CreateProperty;

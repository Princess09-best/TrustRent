import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import styled from 'styled-components';
import { useAuth } from './context/AuthContext';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
`;

const PageHeader = styled.div`
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
  padding-bottom: 20px;
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  font-size: 2rem;
  margin-bottom: 10px;
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 1.1rem;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-weight: 600;
  color: #333;
`;

const Input = styled.input`
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const Select = styled.select`
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button`
  padding: 12px 20px;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 10px;
  
  &:hover {
    background-color: ${props => props.theme.colors.primaryDark};
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  padding: 15px;
  background-color: #FEEBEE;
  color: #F44336;
  border-radius: 8px;
  margin-bottom: 20px;
`;

const SuccessMessage = styled.div`
  padding: 15px;
  background-color: #E8F5E9;
  color: #4CAF50;
  border-radius: 8px;
  margin-bottom: 20px;
`;

const PropertyCard = styled.div`
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 5px solid ${props => props.theme.colors.primary};
`;

const PropertyDetail = styled.p`
  margin: 5px 0;
  font-size: 1rem;
  color: #333;
`;

const PropertyTitle = styled.h3`
  margin: 0 0 10px 0;
  color: ${props => props.theme.colors.primary};
`;

function CreatePropertyListing() {
  const { propertyId } = useParams();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    listingType: 'rent',
    price: '',
  });

  // Fetch property details
  useEffect(() => {
    const fetchPropertyDetails = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        
        if (!token) {
          setError('Authentication token not found. Please log in again.');
          setLoading(false);
          return;
        }
        
        const response = await axios.get(`/api/user/properties/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (Array.isArray(response.data)) {
          // Find the property with the matching ID
          const foundProperty = response.data.find(p => p.id === parseInt(propertyId));
          
          if (foundProperty) {
            // Check if property is verified
            if (!foundProperty.is_verified) {
              setError('Property must be verified before it can be listed.');
            } else {
              setProperty(foundProperty);
            }
          } else {
            setError('Property not found.');
          }
        } else {
          setError('Unexpected response format.');
        }
      } catch (err) {
        console.error('Error fetching property:', err);
        setError('Failed to load property details.');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchPropertyDetails();
    } else {
      navigate('/login');
    }
  }, [isAuthenticated, navigate, propertyId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication token not found. Please log in again.');
        return;
      }
      
      // Validate price
      if (!formData.price || isNaN(parseFloat(formData.price)) || parseFloat(formData.price) <= 0) {
        setError('Please enter a valid price.');
        return;
      }
      
      const response = await axios.post('/api/listing/create/', {
        user_property_id: property.user_property_id,
        listing_type: formData.listingType,
        price: parseFloat(formData.price)
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setSuccess('Property listed successfully!');
      
      // Redirect to My Properties page after a short delay
      setTimeout(() => {
        navigate('/my-properties');
      }, 2000);
      
    } catch (err) {
      console.error('Error creating listing:', err);
      if (err.response) {
        setError(err.response.data.error || 'Failed to create listing.');
      } else {
        setError('Failed to create listing. Please try again.');
      }
    }
  };

  if (loading) {
    return (
      <Container>
        <Title>Create Property Listing</Title>
        <p>Loading property details...</p>
      </Container>
    );
  }

  if (error && !property) {
    return (
      <Container>
        <Title>Create Property Listing</Title>
        <ErrorMessage>{error}</ErrorMessage>
        <Button onClick={() => navigate('/my-properties')}>Back to My Properties</Button>
      </Container>
    );
  }

  return (
    <Container>
      <PageHeader>
        <Title>Create Property Listing</Title>
        <Subtitle>List your verified property for rent or sale</Subtitle>
      </PageHeader>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      
      {property && (
        <>
          <PropertyCard>
            <PropertyTitle>{property.title}</PropertyTitle>
            <PropertyDetail><strong>Type:</strong> {property.property_type}</PropertyDetail>
            <PropertyDetail><strong>Location:</strong> {property.location}</PropertyDetail>
            <PropertyDetail><strong>Status:</strong> {property.verification_status === 'approved' ? 'Verified' : property.verification_status}</PropertyDetail>
          </PropertyCard>
          
          <Form onSubmit={handleSubmit}>
            <FormGroup>
              <Label htmlFor="listingType">Listing Type</Label>
              <Select
                id="listingType"
                name="listingType"
                value={formData.listingType}
                onChange={handleChange}
                required
              >
                <option value="rent">For Rent</option>
                <option value="sale">For Sale</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <Label htmlFor="price">
                {formData.listingType === 'rent' ? 'Monthly Rent (GHS)' : 'Sale Price (GHS)'}
              </Label>
              <Input
                id="price"
                name="price"
                type="number"
                min="0"
                step="0.01"
                value={formData.price}
                onChange={handleChange}
                placeholder="Enter price"
                required
              />
            </FormGroup>
            
            <Button type="submit">Create Listing</Button>
          </Form>
        </>
      )}
    </Container>
  );
}

export default CreatePropertyListing; 
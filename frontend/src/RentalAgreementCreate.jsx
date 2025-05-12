import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';

const Container = styled.div`
  max-width: 700px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 20px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const Label = styled.label`
  margin-bottom: 5px;
  font-weight: 500;
`;

const Input = styled.input`
  padding: 10px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  font-size: 16px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Select = styled.select`
  padding: 10px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  font-size: 16px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button`
  padding: 12px;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 10px;

  &:hover {
    background-color: #006666;
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.p`
  color: ${props => props.theme.colors.error};
  margin-top: 5px;
  font-size: 14px;
`;

const SuccessMessage = styled.p`
  color: ${props => props.theme.colors.success};
  margin-top: 15px;
  padding: 10px;
  background-color: rgba(0, 128, 128, 0.1);
  border-radius: 4px;
`;

function RentalAgreementCreate() {
  const navigate = useNavigate();
  const location = useLocation();
  const propertyDetailsState = location.state;
  
  const [properties, setProperties] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loadingData, setLoadingData] = useState(true);

  // Initialize form data with values from location state if available
  const [formData, setFormData] = useState({
    property_id: propertyDetailsState?.propertyId || '',
    tenant_id: '', // Will be the current user if they're a property seeker
    start_date: propertyDetailsState?.startDate || '',
    end_date: propertyDetailsState?.endDate || '',
    monthly_rent: propertyDetailsState?.price || '',
    security_deposit: propertyDetailsState?.price ? propertyDetailsState.price / 2 : '', // Default to half month's rent
    message: propertyDetailsState?.message || ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadingData(true);
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch user profile to determine role
        const userResponse = await axios.get('/api/users/profile/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        const userRole = userResponse.data.role;
        
        // Different behavior based on role
        if (userRole === 'property_owner') {
          // Property owners need to fetch their properties and potential tenants
          
          // Fetch properties owned by the current user
          const propertiesResponse = await axios.get('/api/user/properties/', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          setProperties(propertiesResponse.data || []);
          
          // Fetch potential tenants (property seekers)
          const tenantsResponse = await axios.get('/api/property-seekers/', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          setTenants(tenantsResponse.data || []);
          
        } else if (userRole === 'property_seeker') {
          // Property seekers need to fetch the specific property
          // and set themselves as tenant
          
          if (propertyDetailsState?.propertyId) {
            const propertyResponse = await axios.get(`/api/property/${propertyDetailsState.propertyId}/`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            setProperties([propertyResponse.data]);
            
            // Set tenant ID to current user
            setFormData(prev => ({
              ...prev,
              tenant_id: userResponse.data.id
            }));
          } else {
            setError('Property information is missing. Please go back to the property details page.');
          }
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load necessary data. Please try again.');
      } finally {
        setLoadingData(false);
      }
    };

    fetchData();
  }, [navigate, propertyDetailsState]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.post('/api/trustchain/rental/create/', formData, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      setSuccess(`Rental agreement created successfully! Agreement ID: ${response.data.agreement_id}`);
      
      // Redirect to the signing page after a short delay
      setTimeout(() => {
        navigate(`/rental-agreements/${response.data.agreement_id}/sign`);
      }, 2000);
    } catch (err) {
      console.error('Error creating rental agreement:', err);
      if (err.response) {
        setError(`Failed to create rental agreement: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to create rental agreement. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <p>Loading data...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <Title>Create Rental Agreement</Title>
      <Form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="property_id">Property</Label>
          <Select 
            id="property_id" 
            name="property_id" 
            value={formData.property_id} 
            onChange={handleChange} 
            required
            disabled={propertyDetailsState?.propertyId}
          >
            <option value="">Select a property</option>
            {properties.map(property => (
              <option key={property.id} value={property.id}>
                {property.title || property.address} - {property.location}
              </option>
            ))}
          </Select>
          {properties.length === 0 && (
            <ErrorMessage>No properties available. Please create a property first.</ErrorMessage>
          )}
        </FormGroup>

        {/* Only show tenant selection for property owners */}
        {!propertyDetailsState?.propertyId && (
          <FormGroup>
            <Label htmlFor="tenant_id">Tenant</Label>
            <Select 
              id="tenant_id" 
              name="tenant_id" 
              value={formData.tenant_id} 
              onChange={handleChange} 
              required
            >
              <option value="">Select a tenant</option>
              {tenants.map(tenant => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.firstname || tenant.first_name} {tenant.lastname || tenant.last_name} - {tenant.email}
                </option>
              ))}
            </Select>
            {tenants.length === 0 && (
              <ErrorMessage>Failed to load potential tenants. Please try again.</ErrorMessage>
            )}
          </FormGroup>
        )}

        <FormGroup>
          <Label htmlFor="start_date">Start Date</Label>
          <Input 
            type="date" 
            id="start_date" 
            name="start_date" 
            value={formData.start_date} 
            onChange={handleChange} 
            required 
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="end_date">End Date</Label>
          <Input 
            type="date" 
            id="end_date" 
            name="end_date" 
            value={formData.end_date} 
            onChange={handleChange} 
            required 
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="monthly_rent">Monthly Rent (GHS)</Label>
          <Input 
            type="number" 
            id="monthly_rent" 
            name="monthly_rent" 
            value={formData.monthly_rent} 
            onChange={handleChange} 
            step="0.01" 
            min="0" 
            required 
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="security_deposit">Security Deposit (GHS)</Label>
          <Input 
            type="number" 
            id="security_deposit" 
            name="security_deposit" 
            value={formData.security_deposit} 
            onChange={handleChange} 
            step="0.01" 
            min="0" 
            required 
          />
        </FormGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        <Button type="submit" disabled={loading || properties.length === 0}>
          {loading ? 'Creating...' : 'Create Rental Agreement'}
        </Button>
      </Form>
    </Container>
  );
}

export default RentalAgreementCreate; 
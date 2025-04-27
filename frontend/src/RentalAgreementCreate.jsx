import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

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
  const [properties, setProperties] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    property_id: '',
    tenant_id: '',
    start_date: '',
    end_date: '',
    monthly_rent: '',
    security_deposit: ''
  });

  useEffect(() => {
    // Fetch properties owned by the current user
    const fetchProperties = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch('/api/properties/owned/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch properties');
        }

        const data = await response.json();
        setProperties(data);
      } catch (err) {
        setError('Failed to load properties. Please try again.');
        console.error(err);
      }
    };

    // Fetch potential tenants
    const fetchTenants = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await fetch('/api/users/seekers/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch property seekers');
        }

        const data = await response.json();
        setTenants(data);
      } catch (err) {
        setError('Failed to load potential tenants. Please try again.');
        console.error(err);
      }
    };

    fetchProperties();
    fetchTenants();
  }, [navigate]);

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

      const response = await fetch('/api/trustchain/rental/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create rental agreement');
      }

      const data = await response.json();
      setSuccess(`Rental agreement created successfully! Agreement ID: ${data.agreement_id}`);
      
      // Redirect to the signing page after a short delay
      setTimeout(() => {
        navigate(`/rental-agreements/${data.agreement_id}`);
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to create rental agreement. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
          >
            <option value="">Select a property</option>
            {properties.map(property => (
              <option key={property.id} value={property.id}>
                {property.address} - {property.city}, {property.state}
              </option>
            ))}
          </Select>
        </FormGroup>

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
                {tenant.first_name} {tenant.last_name} - {tenant.email}
              </option>
            ))}
          </Select>
        </FormGroup>

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
          <Label htmlFor="monthly_rent">Monthly Rent ($)</Label>
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
          <Label htmlFor="security_deposit">Security Deposit ($)</Label>
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

        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Rental Agreement'}
        </Button>
      </Form>
    </Container>
  );
}

export default RentalAgreementCreate; 
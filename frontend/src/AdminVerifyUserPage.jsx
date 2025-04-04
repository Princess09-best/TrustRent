import React, { useEffect, useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';

const Container = styled.div`
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.black};
  margin-bottom: 30px;
  font-size: 28px;
  font-weight: 600;
`;

const Message = styled.div`
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 8px;
  background-color: ${props => props.error ? '#ffe6e6' : '#e6fff9'};
  color: ${props => props.error ? props.theme.colors.error : props.theme.colors.success};
  text-align: center;
  font-weight: 500;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background-color: ${props => props.theme.colors.white};
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Th = styled.th`
  background-color: ${props => props.theme.colors.primary};
  color: white;
  padding: 15px;
  text-align: left;
  font-weight: 500;
`;

const Td = styled.td`
  padding: 15px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  color: ${props => props.theme.colors.black};
`;

const Tr = styled.tr`
  &:hover {
    background-color: #f8f9fa;
  }

  &:last-child td {
    border-bottom: none;
  }
`;

const VerifyButton = styled.button`
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;

  &:hover {
    background-color: #006666;
  }

  &:active {
    transform: translateY(1px);
  }
`;

const EmptyMessage = styled.p`
  text-align: center;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  color: ${props => props.theme.colors.black};
  font-size: 16px;
`;

const Badge = styled.span`
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background-color: ${props => {
    switch (props.role) {
      case 'property_owner':
        return '#e6f3ff';
      case 'property_buyer':
        return '#e6ffe6';
      case 'land_commission_rep':
        return '#fff0e6';
      default:
        return '#f0f0f0';
    }
  }};
  color: ${props => {
    switch (props.role) {
      case 'property_owner':
        return '#0066cc';
      case 'property_buyer':
        return '#006600';
      case 'land_commission_rep':
        return '#cc6600';
      default:
        return '#666666';
    }
  }};
`;

const LoadingSpinner = styled.div`
  text-align: center;
  padding: 20px;
  color: ${props => props.theme.colors.primary};
`;

const AdminVerifyUsers = () => {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch unverified users
  useEffect(() => {
    axios.get('http://127.0.0.1:8000/api/get-unverified-users/')
      .then(response => {
        setUsers(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching users:', error);
        setError(true);
        setMessage('Failed to load unverified users');
        setLoading(false);
      });
  }, []);

  const handleVerify = async (userId) => {
    try {
      const response = await axios.patch('http://127.0.0.1:8000/api/verify-user/', {
        user_id: userId
      });

      setError(false);
      setMessage(response.data.message);
      setUsers(prev => prev.filter(user => user.id !== userId));
    } catch (error) {
      setError(true);
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Verification failed. Please try again.");
      }
    }
  };

  const formatRole = (role) => {
    return role.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <Container>
      <Title>Verify User Identities</Title>
      {message && <Message error={error}>{message}</Message>}
      
      {loading ? (
        <LoadingSpinner>Loading unverified users...</LoadingSpinner>
      ) : users.length === 0 ? (
        <EmptyMessage>No unverified users found at this time.</EmptyMessage>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>Email</Th>
              <Th>Role</Th>
              <Th>ID Type</Th>
              <Th>ID Value</Th>
              <Th>Action</Th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <Tr key={user.id}>
                <Td>{user.firstname} {user.lastname}</Td>
                <Td>{user.email}</Td>
                <Td>
                  <Badge role={user.role}>
                    {formatRole(user.role)}
                  </Badge>
                </Td>
                <Td>{user.id_type}</Td>
                <Td>{user.id_value}</Td>
                <Td>
                  <VerifyButton onClick={() => handleVerify(user.id)}>
                    Verify User
                  </VerifyButton>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
};

export default AdminVerifyUsers;

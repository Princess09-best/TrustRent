import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const PropertyDetails = () => {
  const [rentalDetails, setRentalDetails] = useState({
    startDate: '',
    endDate: '',
    message: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showRentalRequestModal, setShowRentalRequestModal] = useState(false);
  const [rentalRequestLoading, setRentalRequestLoading] = useState(false);
  const navigate = useNavigate();

  const handleInitiateRentalRequest = async (e) => {
    e.preventDefault();
    
    if (!rentalDetails.startDate || !rentalDetails.endDate) {
      setError('Please provide start and end dates for the rental period');
      return;
    }
    
    try {
      setRentalRequestLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      // Create rental request
      const response = await axios.post('/api/rental-requests/', {
        property_id: propertyId,
        start_date: rentalDetails.startDate,
        end_date: rentalDetails.endDate,
        message: rentalDetails.message
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setSuccess('Rental request submitted successfully. The property owner will review your request.');
      setShowRentalRequestModal(false);
      
    } catch (err) {
      console.error('Error initiating rental request:', err);
      setError(err.response?.data?.error || 'Failed to initiate rental request. Please try again.');
    } finally {
      setRentalRequestLoading(false);
    }
  };

  return (
    <div>
      {/* Rental request modal */}
    </div>
  );
};

export default PropertyDetails; 
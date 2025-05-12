import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import { useAuth } from './context/AuthContext';
import { getMediaUrl, handleImageError } from './utils/mediaHelpers';

const Container = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 30px;
  background-color: ${props => props.theme.colors.white};
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 2rem;
`;

const StatusBadge = styled.span`
  font-size: 14px;
  padding: 5px 10px;
  border-radius: 20px;
  background-color: ${props => {
    switch (props.status) {
      case 'rent': return '#4CAF50';
      case 'sale': return '#2196F3';
      default: return '#E0E0E0';
    }
  }};
  color: white;
  font-weight: 600;
`;

const Section = styled.div`
  margin-bottom: 30px;
`;

const SectionTitle = styled.h3`
  color: ${props => props.theme.colors.text};
  margin-bottom: 15px;
  font-size: 1.4rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  padding-bottom: 8px;
`;

const DetailRow = styled.div`
  display: flex;
  margin-bottom: 12px;
  flex-wrap: wrap;
`;

const DetailLabel = styled.div`
  width: 180px;
  font-weight: 600;
  color: #555;
`;

const DetailValue = styled.div`
  flex: 1;
  color: ${props => props.theme.colors.text};
`;

const PropertyPrice = styled.div`
  font-size: 1.8rem;
  font-weight: 700;
  color: ${props => props.theme.colors.primary};
  margin: 20px 0;
`;

const Description = styled.div`
  margin: 20px 0;
  line-height: 1.6;
  color: ${props => props.theme.colors.text};
  white-space: pre-line;
`;

const ImagesContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
`;

const MainImageContainer = styled.div`
  width: 100%;
  height: 400px;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
`;

const MainImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
`;

const ThumbnailsContainer = styled.div`
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
`;

const Thumbnail = styled.img`
  width: 100px;
  height: 75px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  border: 3px solid ${props => props.selected ? props.theme.colors.primary : 'transparent'};
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-3px);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 15px;
  margin-top: 30px;
  flex-wrap: wrap;
`;

const Button = styled.button`
  padding: 12px 24px;
  background-color: ${props => props.variant === 'secondary' 
    ? '#6c757d' 
    : props.variant === 'success'
      ? '#28a745'
      : props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    background-color: ${props => props.variant === 'secondary' 
      ? '#5a6268' 
      : props.variant === 'success'
        ? '#218838'
        : props.theme.colors.primaryDark};
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const ContactCard = styled.div`
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const ContactTitle = styled.h4`
  font-size: 1.2rem;
  margin-bottom: 15px;
  color: ${props => props.theme.colors.primary};
`;

const ContactInfo = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 10px;
`;

const ContactLabel = styled.span`
  font-weight: 600;
  margin-right: 10px;
  width: 80px;
`;

const ContactValue = styled.span`
  color: ${props => props.theme.colors.text};
`;

const ErrorMessage = styled.p`
  color: #dc3545;
  margin-top: 15px;
  padding: 10px;
  background-color: #f8d7da;
  border-radius: 6px;
`;

const SuccessMessage = styled.p`
  color: #28a745;
  margin-top: 15px;
  padding: 10px;
  background-color: #d4edda;
  border-radius: 6px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  
  &:after {
    content: " ";
    display: block;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 6px solid ${props => props.theme.colors.primary};
    border-color: ${props => props.theme.colors.primary} transparent;
    animation: spinner 1.2s linear infinite;
  }
  
  @keyframes spinner {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
`;

const ModalTitle = styled.h3`
  font-size: 1.4rem;
  margin-bottom: 20px;
  color: ${props => props.theme.colors.primary};
`;

const ModalButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: ${props => props.theme.colors.text};
`;

const FormInput = styled.input`
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 1rem;
`;

const FormTextarea = styled.textarea`
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;
`;

function PropertyDetails() {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const { currentUser, userRole } = useAuth();
  
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [selectedImage, setSelectedImage] = useState(0);
  
  // Modal states
  const [showContactModal, setShowContactModal] = useState(false);
  const [showDocumentRequestModal, setShowDocumentRequestModal] = useState(false);
  const [showRentalRequestModal, setShowRentalRequestModal] = useState(false);
  
  // Form states
  const [contactMessage, setContactMessage] = useState('');
  const [documentReason, setDocumentReason] = useState('');
  const [rentalDetails, setRentalDetails] = useState({
    startDate: '',
    endDate: '',
    message: ''
  });
  
  // Action loading states
  const [contactLoading, setContactLoading] = useState(false);
  const [documentRequestLoading, setDocumentRequestLoading] = useState(false);
  const [rentalRequestLoading, setRentalRequestLoading] = useState(false);

  useEffect(() => {
    const fetchProperty = async () => {
      try {
        setLoading(true);
        setError('');
        
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await axios.get(`/api/property/${propertyId}/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Property details:', response.data);
        
        // Process images to add full URLs
        if (response.data.images && response.data.images.length > 0) {
          response.data.processedImages = response.data.images.map(img => getMediaUrl(img));
        } else {
          response.data.processedImages = ['/default-property.jpg'];
        }
        
        setProperty(response.data);
      } catch (err) {
        console.error('Error fetching property details:', err);
        if (err.response) {
          setError(`Failed to load property: ${err.response.data?.error || err.response.statusText}`);
        } else {
          setError('Failed to load property details. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProperty();
  }, [propertyId, navigate]);

  const handleRequestDocumentAccess = async (e) => {
    e.preventDefault();
    
    if (!documentReason.trim()) {
      setError('Please provide a reason for requesting document access');
      return;
    }
    
    try {
      setDocumentRequestLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      
      const response = await axios.post('/api/document/request-access/', {
        property_id: propertyId,
        reason: documentReason
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Document request response:', response.data);
      
      setSuccess('Document access request submitted successfully. The property owner will review your request.');
      setShowDocumentRequestModal(false);
      setDocumentReason('');
    } catch (err) {
      console.error('Error requesting document access:', err);
      if (err.response) {
        setError(`Request failed: ${err.response.data?.error || err.response.statusText}`);
      } else {
        setError('Failed to submit document access request. Please try again.');
      }
    } finally {
      setDocumentRequestLoading(false);
    }
  };

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
      
      await axios.post('/api/rental-requests/', {
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

  const handleContactOwner = async (e) => {
    e.preventDefault();
    
    if (!contactMessage.trim()) {
      setError('Please enter a message for the property owner');
      return;
    }
    
    try {
      setContactLoading(true);
      setError('');
      setSuccess('');
      
      // In a real application, you would send the message to the backend
      // For now, we'll just simulate success
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess('Your message has been sent to the property owner. They will contact you soon.');
      setShowContactModal(false);
      setContactMessage('');
    } catch (err) {
      console.error('Error contacting owner:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setContactLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'N/A';
    return new Intl.NumberFormat('en-GH', {
      style: 'currency',
      currency: 'GHS'
    }).format(amount);
  };

  if (loading) {
    return (
      <Container>
        <LoadingSpinner />
      </Container>
    );
  }

  if (error && !property) {
    return (
      <Container>
        <Title>Error Loading Property</Title>
        <ErrorMessage>{error}</ErrorMessage>
        <Button variant="secondary" onClick={() => navigate(-1)}>Go Back</Button>
      </Container>
    );
  }

  if (!property) {
    return (
      <Container>
        <Title>Property Not Found</Title>
        <ErrorMessage>
          The requested property could not be found or you don't have permission to view it.
        </ErrorMessage>
        <Button variant="secondary" onClick={() => navigate(-1)}>Go Back</Button>
      </Container>
    );
  }

  return (
    <Container>
      <Title>
        {property.title}
        <StatusBadge status={property.listing_type}>
          {property.listing_type === 'rent' ? 'For Rent' : 'For Sale'}
        </StatusBadge>
      </Title>

      <ImagesContainer>
        <MainImageContainer>
          <MainImage 
            src={property.processedImages[selectedImage]} 
            alt={property.title}
            onError={handleImageError}
          />
        </MainImageContainer>
        
        {property.processedImages.length > 1 && (
          <ThumbnailsContainer>
            {property.processedImages.map((image, index) => (
              <Thumbnail 
                key={index}
                src={image}
                alt={`Thumbnail ${index + 1}`}
                selected={selectedImage === index}
                onClick={() => setSelectedImage(index)}
                onError={handleImageError}
              />
            ))}
          </ThumbnailsContainer>
        )}
      </ImagesContainer>

      <PropertyPrice>
        {formatCurrency(property.price)}
        {property.listing_type === 'rent' ? ' / month' : ''}
      </PropertyPrice>

      <Section>
        <SectionTitle>Property Details</SectionTitle>
        <DetailRow>
          <DetailLabel>Location:</DetailLabel>
          <DetailValue>{property.location}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Property Type:</DetailLabel>
          <DetailValue>{property.property_type}</DetailValue>
        </DetailRow>
        <DetailRow>
          <DetailLabel>Status:</DetailLabel>
          <DetailValue>{property.status}</DetailValue>
        </DetailRow>
      </Section>

      <Section>
        <SectionTitle>Description</SectionTitle>
        <Description>{property.description}</Description>
      </Section>

      <ContactCard>
        <ContactTitle>Owner Information</ContactTitle>
        <ContactInfo>
          <ContactLabel>Owner:</ContactLabel>
          <ContactValue>{property.owner?.name}</ContactValue>
        </ContactInfo>
        <ContactInfo>
          <ContactLabel>Phone:</ContactLabel>
          <ContactValue>{property.owner?.phone}</ContactValue>
        </ContactInfo>
      </ContactCard>

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      {userRole === 'property_seeker' && (
        <ButtonGroup>
          <Button onClick={() => setShowContactModal(true)}>
            Contact Owner
          </Button>
          <Button onClick={() => setShowDocumentRequestModal(true)}>
            Request Document Access
          </Button>
          {property.listing_type === 'rent' && (
            <Button variant="success" onClick={() => setShowRentalRequestModal(true)}>
              Request Rental Agreement
            </Button>
          )}
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back
          </Button>
        </ButtonGroup>
      )}

      {/* Contact Owner Modal */}
      {showContactModal && (
        <Modal>
          <ModalContent>
            <ModalTitle>Contact Property Owner</ModalTitle>
            <form onSubmit={handleContactOwner}>
              <FormGroup>
                <FormLabel>Your Message</FormLabel>
                <FormTextarea 
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  placeholder="Enter your message to the property owner..."
                  required
                />
              </FormGroup>
              <ModalButtons>
                <Button 
                  variant="secondary" 
                  type="button" 
                  onClick={() => setShowContactModal(false)}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={contactLoading}
                >
                  {contactLoading ? 'Sending...' : 'Send Message'}
                </Button>
              </ModalButtons>
            </form>
          </ModalContent>
        </Modal>
      )}

      {/* Document Request Modal */}
      {showDocumentRequestModal && (
        <Modal>
          <ModalContent>
            <ModalTitle>Request Document Access</ModalTitle>
            <form onSubmit={handleRequestDocumentAccess}>
              <FormGroup>
                <FormLabel>Reason for Request</FormLabel>
                <FormTextarea 
                  value={documentReason}
                  onChange={(e) => setDocumentReason(e.target.value)}
                  placeholder="Explain why you need access to the property documents..."
                  required
                />
              </FormGroup>
              <ModalButtons>
                <Button 
                  variant="secondary" 
                  type="button" 
                  onClick={() => setShowDocumentRequestModal(false)}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={documentRequestLoading}
                >
                  {documentRequestLoading ? 'Submitting...' : 'Submit Request'}
                </Button>
              </ModalButtons>
            </form>
          </ModalContent>
        </Modal>
      )}

      {/* Rental Request Modal */}
      {showRentalRequestModal && (
        <Modal>
          <ModalContent>
            <ModalTitle>Request Rental Agreement</ModalTitle>
            <form onSubmit={handleInitiateRentalRequest}>
              <FormGroup>
                <FormLabel>Start Date</FormLabel>
                <FormInput 
                  type="date"
                  value={rentalDetails.startDate}
                  onChange={(e) => setRentalDetails({...rentalDetails, startDate: e.target.value})}
                  min={new Date().toISOString().split('T')[0]}
                  required
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>End Date</FormLabel>
                <FormInput 
                  type="date"
                  value={rentalDetails.endDate}
                  onChange={(e) => setRentalDetails({...rentalDetails, endDate: e.target.value})}
                  min={rentalDetails.startDate || new Date().toISOString().split('T')[0]}
                  required
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Additional Message (Optional)</FormLabel>
                <FormTextarea 
                  value={rentalDetails.message}
                  onChange={(e) => setRentalDetails({...rentalDetails, message: e.target.value})}
                  placeholder="Any additional information or requests..."
                />
              </FormGroup>
              <ModalButtons>
                <Button 
                  variant="secondary" 
                  type="button" 
                  onClick={() => setShowRentalRequestModal(false)}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={rentalRequestLoading}
                >
                  {rentalRequestLoading ? 'Processing...' : 'Continue to Agreement'}
                </Button>
              </ModalButtons>
            </form>
          </ModalContent>
        </Modal>
      )}
    </Container>
  );
}

export default PropertyDetails; 
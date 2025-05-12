import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  background-color: ${props => props.theme.colors.background};
  padding: 40px 20px;
`;

const FormCard = styled.div`
  background: ${props => props.theme.colors.white};
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 800px;
  margin-bottom: 40px;
`;

const Title = styled.h2`
  color: ${props => props.theme.colors.primary};
  text-align: center;
  margin-bottom: 30px;
  font-size: 28px;
  font-weight: 600;
`;

const StepIndicator = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 2px;
    background-color: ${props => props.theme.colors.border};
    transform: translateY(-50%);
    z-index: 0;
  }
`;

const Step = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
`;

const StepCircle = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: ${props => props.active ? props.theme.colors.primary : props.completed ? props.theme.colors.success : props.theme.colors.border};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-bottom: 10px;
  transition: all 0.3s ease;
`;

const StepLabel = styled.div`
  font-size: 14px;
  color: ${props => props.active ? props.theme.colors.primary : props.completed ? props.theme.colors.success : '#666'};
  font-weight: ${props => props.active || props.completed ? '600' : '400'};
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
  gap: 20px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const Label = styled.label`
  color: ${props => props.theme.colors.black};
  font-weight: 500;
  margin-bottom: 8px;
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

const FileInput = styled.input`
  display: none;
`;

const FileInputLabel = styled.label`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: #f5f5f5;
  border: 1px dashed ${props => props.theme.colors.border};
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 5px;
  
  &:hover {
    background-color: #e9e9e9;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const FilePreview = styled.div`
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const ImagePreview = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
`;

const PreviewImage = styled.div`
  width: 100px;
  height: 100px;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  &:hover button {
    opacity: 1;
  }
`;

const RemoveButton = styled.button`
  position: absolute;
  top: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: rgba(255, 0, 0, 0.7);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
`;

const FileItem = styled.div`
  display: flex;
  align-items: center;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 5px;
  justify-content: space-between;
`;

const FileName = styled.span`
  font-size: 14px;
  color: #333;
  word-break: break-all;
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  gap: 15px;
`;

const Button = styled.button`
  padding: 12px 20px;
  background-color: ${props => props.secondary ? 'transparent' : props.theme.colors.primary};
  color: ${props => props.secondary ? props.theme.colors.primary : 'white'};
  border: ${props => props.secondary ? `1px solid ${props.theme.colors.primary}` : 'none'};
  border-radius: 5px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: ${props => props.fullWidth ? '1' : 'initial'};

  &:hover {
    background-color: ${props => props.secondary ? 'rgba(0, 128, 128, 0.1)' : '#006666'};
  }

  &:active {
    transform: translateY(1px);
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    opacity: 0.7;
  }
`;

const SuccessCard = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px;
`;

const SuccessIcon = styled.div`
  font-size: 60px;
  color: ${props => props.theme.colors.success};
  margin-bottom: 20px;
`;

const SuccessTitle = styled.h3`
  font-size: 24px;
  color: ${props => props.theme.colors.primary};
  margin-bottom: 15px;
`;

const SuccessMessage = styled.p`
  font-size: 16px;
  color: #555;
  margin-bottom: 30px;
  line-height: 1.6;
`;

const InfoText = styled.p`
  font-size: 14px;
  color: #666;
  margin-top: 5px;
  font-style: italic;
`;

const CreateProperty = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [propertyData, setPropertyData] = useState({
    title: '',
    property_type: '1_bedroom',
    description: '',
    location: ''
  });
  
  const [selectedImages, setSelectedImages] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [propertyId, setPropertyId] = useState(null);
  const [userPropertyId, setUserPropertyId] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  
  // Step 1: Create property
  const handlePropertyChange = (e) => {
    setPropertyData({ 
      ...propertyData, 
      [e.target.name]: e.target.value 
    });
  };
  
  const handleCreateProperty = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage('');
    setError(false);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/property/create/', propertyData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Extract property ID from response headers
      const resourceId = response.headers['x-resource-id'];
      const userPropId = response.headers['x-userproperty-id'];
      
      // Extract numeric property ID
      const propIdMatch = resourceId.match(/PROP_(\d+)/);
      const propId = propIdMatch ? propIdMatch[1] : null;
      
      const userPropIdMatch = userPropId.match(/UP_(\d+)/);
      const userPropIdNum = userPropIdMatch ? userPropIdMatch[1] : null;
      
      if (propId) {
        setPropertyId(propId);
        setUserPropertyId(userPropIdNum);
        setCurrentStep(2);
        setMessage('');
      } else {
        throw new Error('Could not extract property ID from response');
      }
    } catch (error) {
      setError(true);
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Failed to create property. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Step 2: Upload images
  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files);
    
    // Validate file types
    const validFiles = files.filter(file => 
      file.type === 'image/jpeg' || 
      file.type === 'image/png' || 
      file.type === 'image/jpg'
    );
    
    if (validFiles.length !== files.length) {
      setMessage('Some files were not added. Only JPEG and PNG images are allowed.');
      setError(true);
    }
    
    // Create preview URLs
    const newImages = validFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setSelectedImages([...selectedImages, ...newImages]);
  };
  
  const handleRemoveImage = (index) => {
    const newImages = [...selectedImages];
    URL.revokeObjectURL(newImages[index].preview);
    newImages.splice(index, 1);
    setSelectedImages(newImages);
  };
  
  const handleUploadImages = async () => {
    if (selectedImages.length === 0) {
      setMessage('Please select at least one image');
      setError(true);
      return;
    }
    
    setIsSubmitting(true);
    setMessage('');
    setError(false);
    
    try {
      const token = localStorage.getItem('token');
      
      // Upload each image
      for (const imageObj of selectedImages) {
        const formData = new FormData();
        formData.append('property_id', propertyId);
        formData.append('image', imageObj.file);
        
        await axios.post('/api/property/upload-image/', formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      }
      
      setCurrentStep(3);
      setMessage('');
    } catch (error) {
      setError(true);
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Failed to upload images. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Step 3: Upload document
  const handleDocumentSelect = (e) => {
    const file = e.target.files[0];
    
    if (!file) return;
    
    // Validate file type
    if (file.type !== 'application/pdf') {
      setMessage('Only PDF documents are allowed.');
      setError(true);
      return;
    }
    
    setSelectedDocument(file);
  };
  
  const handleRemoveDocument = () => {
    setSelectedDocument(null);
  };
  
  const handleUploadDocument = async () => {
    if (!selectedDocument) {
      setMessage('Please select a document');
      setError(true);
      return;
    }
    
    setIsSubmitting(true);
    setMessage('');
    setError(false);
    
    try {
      const token = localStorage.getItem('token');
      
      const formData = new FormData();
      formData.append('property_id', propertyId);
      formData.append('attachment', selectedDocument);
      
      await axios.post('/api/property/upload-document/', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Show completion message
      setIsComplete(true);
    } catch (error) {
      setError(true);
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Failed to upload document. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const goToDashboard = () => {
    navigate('/dashboard');
  };
  
  if (isComplete) {
    return (
      <Container>
        <FormCard>
          <SuccessCard>
            <SuccessIcon>✅</SuccessIcon>
            <SuccessTitle>Property Created Successfully!</SuccessTitle>
            <SuccessMessage>
              Your property has been created and all required documents have been uploaded. 
              It is now pending verification by a land representative.
              <br /><br />
              After verification, you will be able to list your property for rent or sale and set a price.
            </SuccessMessage>
            <Button onClick={goToDashboard}>Go to Dashboard</Button>
          </SuccessCard>
        </FormCard>
      </Container>
    );
  }
  
  return (
    <Container>
      <FormCard>
        <Title>List Your Property</Title>
        
        <StepIndicator>
          <Step>
            <StepCircle active={currentStep === 1} completed={currentStep > 1}>
              {currentStep > 1 ? '✓' : '1'}
            </StepCircle>
            <StepLabel active={currentStep === 1} completed={currentStep > 1}>Property Details</StepLabel>
          </Step>
          
          <Step>
            <StepCircle active={currentStep === 2} completed={currentStep > 2}>
              {currentStep > 2 ? '✓' : '2'}
            </StepCircle>
            <StepLabel active={currentStep === 2} completed={currentStep > 2}>Upload Images</StepLabel>
          </Step>
          
          <Step>
            <StepCircle active={currentStep === 3} completed={currentStep > 3}>
              {currentStep > 3 ? '✓' : '3'}
            </StepCircle>
            <StepLabel active={currentStep === 3} completed={currentStep > 3}>Upload Document</StepLabel>
          </Step>
        </StepIndicator>
        
        {message && <Message error={error}>{message}</Message>}
        
        {currentStep === 1 && (
          <Form onSubmit={handleCreateProperty}>
            <FormGroup>
              <Label>Property Title</Label>
              <Input
                name="title"
                placeholder="e.g., Modern 2 Bedroom Apartment in East Legon"
                value={propertyData.title}
                onChange={handlePropertyChange}
                required
              />
            </FormGroup>

            <FormGroup>
              <Label>Property Type</Label>
              <Select 
                name="property_type"
                value={propertyData.property_type}
                onChange={handlePropertyChange}
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
                value={propertyData.description}
                onChange={handlePropertyChange}
                required
              />
            </FormGroup>

            <FormGroup>
              <Label>Location</Label>
              <Input
                name="location"
                placeholder="e.g., East Legon, Accra"
                value={propertyData.location}
                onChange={handlePropertyChange}
                required
              />
            </FormGroup>

            <InfoText>
              Note: You will be able to set the price and listing type (rent/sale) after your property is verified.
            </InfoText>

            <Button type="submit" fullWidth disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Continue'}
            </Button>
          </Form>
        )}
        
        {currentStep === 2 && (
          <>
            <FormGroup>
              <Label>Property Images (JPEG, PNG - Max 10MB each)</Label>
              <FileInputLabel>
                <span>Click to select images</span>
                <FileInput 
                  type="file" 
                  accept="image/jpeg,image/png,image/jpg"
                  multiple
                  onChange={handleImageSelect}
                />
              </FileInputLabel>
              
              {selectedImages.length > 0 && (
                <ImagePreview>
                  {selectedImages.map((image, index) => (
                    <PreviewImage key={index}>
                      <img src={image.preview} alt={`Preview ${index}`} />
                      <RemoveButton onClick={() => handleRemoveImage(index)}>×</RemoveButton>
                    </PreviewImage>
                  ))}
                </ImagePreview>
              )}
            </FormGroup>
            
            <ButtonGroup>
              <Button 
                type="button" 
                secondary 
                onClick={() => setCurrentStep(1)}
                disabled={isSubmitting}
              >
                Back
              </Button>
              <Button 
                type="button" 
                onClick={handleUploadImages}
                disabled={selectedImages.length === 0 || isSubmitting}
              >
                {isSubmitting ? 'Uploading...' : 'Continue'}
              </Button>
            </ButtonGroup>
          </>
        )}
        
        {currentStep === 3 && (
          <>
            <FormGroup>
              <Label>Property Title Deed (PDF only)</Label>
              <FileInputLabel>
                <span>Click to select document</span>
                <FileInput 
                  type="file" 
                  accept="application/pdf"
                  onChange={handleDocumentSelect}
                />
              </FileInputLabel>
              
              {selectedDocument && (
                <FilePreview>
                  <FileItem>
                    <FileName>{selectedDocument.name}</FileName>
                    <Button 
                      type="button" 
                      secondary 
                      onClick={handleRemoveDocument}
                      style={{ padding: '5px 10px', fontSize: '12px' }}
                    >
                      Remove
                    </Button>
                  </FileItem>
                </FilePreview>
              )}
            </FormGroup>
            
            <ButtonGroup>
              <Button 
                type="button" 
                secondary 
                onClick={() => setCurrentStep(2)}
                disabled={isSubmitting}
              >
                Back
              </Button>
              <Button 
                type="button" 
                onClick={handleUploadDocument}
                disabled={!selectedDocument || isSubmitting}
              >
                {isSubmitting ? 'Uploading...' : 'Complete Listing'}
              </Button>
            </ButtonGroup>
          </>
        )}
      </FormCard>
    </Container>
  );
};

export default CreateProperty;

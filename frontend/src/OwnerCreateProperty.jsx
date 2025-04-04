import React, { useState } from 'react';
import axios from 'axios';

const CreateProperty = () => {
  const [formData, setFormData] = useState({
    title: '',
    property_type: '1 bedroom',
    description: '',
    location: '',
    price: '',
    owner_id: localStorage.getItem('user_id')  // assuming it's stored at login
  });

  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setFormData({ 
      ...formData, 
      [e.target.name]: e.target.value 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/properties/', formData);
      setMessage(response.data.message || 'Property created successfully.');
    } catch (error) {
      if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Failed to create property.");
      }
    }
  };

  return (
    <div style={{ maxWidth: '500px', margin: '0 auto' }}>
      <h2>Create a Property</h2>
      {message && <p><strong>{message}</strong></p>}
      <form onSubmit={handleSubmit}>
        <input name="title" placeholder="Property Title" onChange={handleChange} required /><br />
        <select name="property_type" onChange={handleChange}>
          <option>1 bedroom</option>
          <option>2 bedroom</option>
          <option>3 bedroom</option>
          <option>4 bedroom</option>
          <option>5 bedroom</option>
          <option>Full gated house</option>
        </select><br />
        <textarea name="description" placeholder="Description" onChange={handleChange} required /><br />
        <input name="location" placeholder="Location" onChange={handleChange} required /><br />
        <input name="price" type="number" step="0.01" placeholder="Price" onChange={handleChange} required /><br />
        <button type="submit">Submit Property</button>
      </form>
    </div>
  );
};

export default CreateProperty;

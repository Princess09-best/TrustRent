import json
from datetime import date, timedelta
from unittest import mock
from unittest.mock import patch, MagicMock, call

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from ledger.views import (
    create_rental_agreement,
    sign_rental_agreement,
    get_rental_agreement,
    terminate_rental_agreement
)

User = get_user_model()

class RentalAgreementMockTest(TestCase):
    """Test cases for rental agreement functionality using pure mocks"""
    
    # Add database configuration for multi-db support
    databases = {'default', 'core', 'ledger'}
    
    def setUp(self):
        """Set up test data and request factory"""
        self.factory = APIRequestFactory()
        
        # Create mock users
        self.owner = MagicMock()
        self.owner.id = 1
        self.owner.email = 'owner@example.com'
        self.owner.role = 'property_owner'
        
        self.tenant = MagicMock()
        self.tenant.id = 2
        self.tenant.email = 'tenant@example.com'
        self.tenant.role = 'property_seeker'
        
        # Test data
        self.property_id = 1
        self.agreement_id = 'RENT_test123'
        
    @patch('ledger.views.RentalAgreementService.create_rental_agreement')
    def test_create_rental_agreement(self, mock_service):
        """Test creating a rental agreement"""
        # Set up request
        data = {
            'property_id': self.property_id,
            'tenant_id': self.tenant.id,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=365)).isoformat(),
            'monthly_rent': 1000.00,
            'security_deposit': 2000.00
        }
        # Use format='json' to properly set the request body
        request = self.factory.post('/rental/create/', data=data, format='json')
        force_authenticate(request, user=self.owner)
        
        # Mock service response
        mock_service.return_value = (True, "Rental agreement created", self.agreement_id)
        
        # Call the view with authentication bypass
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True):
            response = create_rental_agreement(request)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['agreement_id'], self.agreement_id)
        
    @patch('ledger.views.RentalAgreementService.sign_agreement')
    def test_sign_rental_agreement(self, mock_service):
        """Test signing a rental agreement"""
        # Create request - no body needed for this endpoint
        request = self.factory.post(f'/rental/{self.agreement_id}/sign/')
        force_authenticate(request, user=self.owner)
        
        # Mock service response
        mock_service.return_value = (True, {
            'agreement_id': self.agreement_id,
            'status': 'active',
            'owner_signature': True,
            'tenant_signature': False
        })
        
        # Mock database authentication to avoid actual db queries
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
             patch('core.auth.CustomJWTAuthentication.authenticate', return_value=(self.owner, None)):
            response = sign_rental_agreement(request, self.agreement_id)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['owner_signature'])
        
    @patch('ledger.views.RentalAgreementService.get_agreement_details')
    def test_get_rental_agreement(self, mock_service):
        """Test retrieving a rental agreement"""
        # Set up request
        request = self.factory.get(f'/rental/{self.agreement_id}/')
        force_authenticate(request, user=self.owner)
        
        # Mock service response
        mock_service.return_value = (True, {
            'agreement_id': self.agreement_id,
            'property': {
                'title': 'Test Property',
                'location': 'Test Location',
                'type': 'residential'
            },
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=365)).isoformat(),
            'monthly_rent': 1000.00,
            'status': 'pending'
        })
        
        # Mock database authentication to avoid actual db queries
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
             patch('core.auth.CustomJWTAuthentication.authenticate', return_value=(self.owner, None)):
            response = get_rental_agreement(request, self.agreement_id)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['agreement_id'], self.agreement_id)
        
    @patch('ledger.views.RentalAgreementService.create_rental_agreement')
    def test_create_rental_agreement_invalid_dates(self, mock_service):
        """Test creating a rental agreement with invalid dates"""
        # Set up request with invalid dates
        data = {
            'property_id': self.property_id,
            'tenant_id': self.tenant.id,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() - timedelta(days=1)).isoformat(),
            'monthly_rent': 1000.00,
            'security_deposit': 2000.00
        }
        # Use format='json' to properly set the request body
        request = self.factory.post('/rental/create/', data=data, format='json')
        force_authenticate(request, user=self.owner)
        
        # Mock service response for validation error
        mock_service.return_value = (False, "Start date cannot be after end date", None)
        
        # Call the view with authentication bypass
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True):
            response = create_rental_agreement(request)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Start date cannot be after end date', response_data['error'])
        
    def test_create_rental_agreement_unauthorized(self):
        """Test creating a rental agreement without proper authorization"""
        # Set up request with tenant as user (who shouldn't have permission)
        data = {
            'property_id': self.property_id,
            'tenant_id': self.tenant.id,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=365)).isoformat(),
            'monthly_rent': 1000.00,
            'security_deposit': 2000.00
        }
        # Use format='json' to properly set the request body
        request = self.factory.post('/rental/create/', data=data, format='json')
        force_authenticate(request, user=self.tenant)  # Tenant trying to create agreement
        
        # Call the view with authentication bypass
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True):
            response = create_rental_agreement(request)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertIn('Only property owners can create rental agreements', response_data['error'])
        
    @patch('ledger.views.RentalAgreementService.terminate_agreement')
    def test_terminate_rental_agreement(self, mock_service):
        """Test terminating a rental agreement"""
        # Set up request with data in format='json'
        data = {'reason': 'Test termination'}
        request = self.factory.post(f'/rental/{self.agreement_id}/terminate/', data=data, format='json')
        force_authenticate(request, user=self.owner)
        
        # Mock service response
        mock_service.return_value = (True, "Agreement terminated successfully")
        
        # Call the view with authentication bypass and mock db authentication
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
             patch('core.auth.CustomJWTAuthentication.authenticate', return_value=(self.owner, None)):
            response = terminate_rental_agreement(request, self.agreement_id)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], "Agreement terminated successfully")
        
    def test_agreement_validation(self):
        """Test validation of agreement parameters"""
        # Set up request with missing required fields
        data = {'property_id': self.property_id}  # Missing tenant_id, dates, etc.
        request = self.factory.post('/rental/create/', data=data, format='json')
        force_authenticate(request, user=self.owner)
        
        # Call the view with authentication bypass
        with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True):
            response = create_rental_agreement(request)
            
        # Render the response before accessing content
        response.render()
        
        # Check the response
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Missing required fields', response_data['error']) 
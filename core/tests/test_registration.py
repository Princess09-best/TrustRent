from django.test import TestCase
from django.urls import reverse
from core.models import User
from core.permissions import UserRole, ROLE_PERMISSIONS
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

class RegistrationTest(TestCase):
    databases = {'default', 'core', 'ledger', 'ops'}  # Allow access to all databases
    
    def setUp(self):
        self.client = APIClient()
        # Create a system admin for testing admin account creation
        self.admin_user = User.objects.create_user(
            firstname="Admin",
            lastname="User",
            email="admin@trustrent.com",
            phone_number="+233123456780",
            password="SecurePass123",  # In real app this would be hashed
            role=UserRole.SYS_ADMIN.value,
            id_type="Ghana Card",
            id_value="GHA-123456789-0",
            is_verified=True,
            is_staff=True,
            is_superuser=True
        )
        # Ensure the role is set correctly
        self.admin_user.role = UserRole.SYS_ADMIN.value
        self.admin_user.save()
        # Set up JWT token for admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)

    def test_regular_user_registration_success(self):
        """Test successful registration of a property owner"""
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "+233123456789",
            "password": "SecurePass123",
            "role": "property_owner",
            "id_type": "Ghana Card",
            "id_value": "GHA-123456789-1"
        }
        response = self.client.post(
            reverse('register_user'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('Registration successful', response.json()['message'])

    def test_regular_user_registration_invalid_role(self):
        """Test registration fails with invalid role"""
        data = {
            "firstname": "Jane",
            "lastname": "Smith",
            "email": "jane.smith@example.com",
            "phone_number": "+233123456788",
            "password": "SecurePass123",
            "role": "land_commission_rep",
            "id_type": "Ghana Card",
            "id_value": "GHA-123456789-2"
        }
        response = self.client.post(
            reverse('register_user'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid role', response.json()['error'])

    def test_admin_create_land_rep_success(self):
        """Test successful creation of land commission rep by admin"""
        # Print debug information
        print(f"Admin user role: {self.admin_user.role}")
        print(f"Admin user permissions: {ROLE_PERMISSIONS.get(self.admin_user.role, [])}")
        
        # Add authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            "firstname": "James",
            "lastname": "Brown",
            "email": "james.brown@landcomm.gov.gh",
            "phone_number": "+233123456787",
            "password": "SecurePass123",
            "role": "land_commission_rep",
            "id_type": "Ghana Card",
            "id_value": "GHA-123456789-3"
        }
        response = self.client.post(
            reverse('create_admin_account'),
            data=json.dumps(data),
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, 201)
        self.assertIn('land_commission_rep account created successfully', response.json()['message'])

    def test_admin_create_land_rep_unauthorized(self):
        """Test creation of land commission rep fails without admin auth"""
        data = {
            "firstname": "James",
            "lastname": "Brown",
            "email": "james.brown@landcomm.gov.gh",
            "phone_number": "+233123456787",
            "password": "SecurePass123",
            "role": "land_commission_rep",
            "id_type": "Ghana Card",
            "id_value": "GHA-123456789-3"
        }
        response = self.client.post(
            reverse('create_admin_account'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Permission denied

    def test_regular_user_registration_validation(self):
        """Test validation rules for regular registration"""
        test_cases = [
            # Invalid email
            {
                "firstname": "John",
                "lastname": "Doe",
                "email": "invalid-email",
                "phone_number": "+233123456789",
                "password": "SecurePass123",
                "role": "property_owner",
                "id_type": "Ghana Card",
                "id_value": "GHA-123456789-1"
            },
            # Invalid phone number
            {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "123456789",  # Missing +233 prefix
                "password": "SecurePass123",
                "role": "property_owner",
                "id_type": "Ghana Card",
                "id_value": "GHA-123456789-1"
            },
            # Invalid Ghana Card format
            {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+233123456789",
                "password": "SecurePass123",
                "role": "property_owner",
                "id_type": "Ghana Card",
                "id_value": "123456789"  # Wrong format
            }
        ]

        for test_case in test_cases:
            response = self.client.post(
                reverse('register_user'),
                data=json.dumps(test_case),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

    def test_duplicate_email_registration(self):
        """Test registration fails with duplicate email"""
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "+233123456789",
            "password": "SecurePass123",
            "role": "property_owner",
            "id_type": "Ghana Card",
            "id_value": "GHA-123456789-1"
        }
        # First registration should succeed
        response1 = self.client.post(
            reverse('register_user'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 201)

        # Second registration with same email should fail
        response2 = self.client.post(
            reverse('register_user'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 400)
        self.assertIn('Email already registered', response2.json()['error']) 
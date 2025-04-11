from django.test import TestCase, Client
from django.urls import reverse
from .models import User
import json
from django.contrib.auth.hashers import make_password

# Create your tests here.

class UserRegistrationTests(TestCase):
    databases = {'core'}  # Specify that this test uses the core database
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register_user')
        self.valid_payload = {
            'firstname': 'John',
            'lastname': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '+233123456789',
            'password': 'securepassword123',
            'role': 'property_owner',
            'id_type': 'Ghana Card',
            'id_value': 'GHA-123456789-0'
        }

    def test_valid_user_registration(self):
        """Test user registration with valid data"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email=self.valid_payload['email']).exists())
        
        data = json.loads(response.content)
        self.assertIn('user_id', data)
        self.assertEqual(data['message'], 'Registration successful! Please wait for account verification.')
        self.assertFalse(data['is_verified'])

    def test_invalid_email_format(self):
        """Test user registration with invalid email format"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['email'] = 'invalid-email'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email=invalid_payload['email']).exists())

    def test_missing_required_fields(self):
        """Test user registration with missing required fields"""
        invalid_payload = self.valid_payload.copy()
        del invalid_payload['email']
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'email is required')

    def test_duplicate_email(self):
        """Test user registration with an email that already exists"""
        # First registration
        self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        # Second registration with same email
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(email=self.valid_payload['email']).count(), 1)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Email already registered')

    def test_invalid_phone_number(self):
        """Test user registration with invalid phone number format"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['phone_number'] = '123'  # Too short
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(phone_number=invalid_payload['phone_number']).exists())

    def test_invalid_id_value_format(self):
        """Test user registration with invalid ID value format"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['id_value'] = '123'  # Invalid Ghana Card format
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(id_value=invalid_payload['id_value']).exists())

    def test_invalid_role(self):
        """Test user registration with invalid role"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['role'] = 'invalid_role'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email=invalid_payload['email']).exists())

    def test_password_requirements(self):
        """Test user registration with weak password"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['password'] = '123'  # Too short
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Password must be', data['error'])

class UserLoginTests(TestCase):
    databases = {'core'}  # Specify that this test uses the core database
    
    def setUp(self):
        # Create a verified user
        self.verified_user = User.objects.create(
            firstname="John",
            lastname="Doe",
            email="verified@example.com",
            phone_number="+233123456789",
            password_hash=make_password("securepassword123"),
            role="property_owner",
            id_type="Ghana Card",
            id_value="GHA-123456789-0",
            is_verified=True
        )

        # Create an unverified user
        self.unverified_user = User.objects.create(
            firstname="Jane",
            lastname="Doe",
            email="unverified@example.com",
            phone_number="+233987654321",
            password_hash=make_password("securepassword123"),
            role="renter",
            id_type="Ghana Card",
            id_value="GHA-987654321-0",
            is_verified=False
        )

        self.client = Client()

    def test_successful_login(self):
        """Test successful login with verified user"""
        response = self.client.post('/api/user/login/', {
            'email': 'verified@example.com',
            'password': 'securepassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Login successful')
        self.assertEqual(data['user_id'], self.verified_user.id)
        self.assertEqual(data['role'], 'property_owner')
        self.assertTrue(data['is_verified'])

    def test_unverified_user_login(self):
        """Test login attempt with unverified user"""
        response = self.client.post('/api/user/login/', {
            'email': 'unverified@example.com',
            'password': 'securepassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Account pending verification. Please wait for verification email.')
        self.assertFalse(data['is_verified'])

    def test_invalid_email(self):
        """Test login attempt with non-existent email"""
        response = self.client.post('/api/user/login/', {
            'email': 'nonexistent@example.com',
            'password': 'securepassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid email or password')

    def test_invalid_password(self):
        """Test login attempt with incorrect password"""
        response = self.client.post('/api/user/login/', {
            'email': 'verified@example.com',
            'password': 'wrongpassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid email or password')

    def test_missing_fields(self):
        """Test login attempt with missing required fields"""
        # Test missing password
        response = self.client.post('/api/user/login/', {
            'email': 'verified@example.com'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Email and password required')

        # Test missing email
        response = self.client.post('/api/user/login/', {
            'password': 'securepassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Email and password required')

    def test_invalid_json(self):
        """Test login attempt with invalid JSON data"""
        response = self.client.post('/api/user/login/', 
            'invalid json data',
            content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON')

class PropertyManagementTests(TestCase):
    databases = {'core'}  # Specify that this test uses the core database
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            firstname='Test',
            lastname='Owner',
            email='owner@example.com',
            phone_number='+233555555555',
            password_hash=make_password('testpass123'),
            role='property_owner',
            id_type='Ghana Card',
            id_value='GHA-123456789-0',
            is_verified=True
        )
        
        # Test property data
        self.property_data = {
            'title': 'Test Property',
            'property_type': 'apartment',
            'description': 'A beautiful test property',
            'location': 'Test Location',
            'price': '1000.00',
            'owner_id': self.user.id
        }

    def test_successful_property_creation(self):
        """Test creating a property with valid data"""
        response = self.client.post('/api/property/create/', 
            self.property_data, 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('property_id', data)
        self.assertIn('user_property_id', data)
        self.assertIn('message', data)

    def test_property_creation_missing_fields(self):
        """Test property creation with missing required fields"""
        invalid_data = self.property_data.copy()
        del invalid_data['title']
        
        response = self.client.post('/api/property/create/', 
            invalid_data, 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Missing fields', data['error'])

    def test_get_unverified_properties(self):
        """Test retrieving unverified properties"""
        # First create a property
        self.client.post('/api/property/create/', 
            self.property_data, 
            content_type='application/json'
        )
        
        response = self.client.get('/api/property/unverified/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(isinstance(data, list))
        if len(data) > 0:
            self.assertIn('user_property_id', data[0])
            self.assertIn('property_title', data[0])
            self.assertIn('verification_status', data[0])

    def test_verify_property(self):
        """Test verifying a property"""
        # First create a property
        create_response = self.client.post('/api/property/create/', 
            self.property_data, 
            content_type='application/json'
        )
        create_data = json.loads(create_response.content)
        
        verify_data = {
            'user_property_id': create_data['user_property_id']
        }
        
        response = self.client.patch('/api/property/verify/',
            verify_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('verified successfully', data['message'])

    def test_reject_property(self):
        """Test rejecting a property"""
        # First create a property
        create_response = self.client.post('/api/property/create/', 
            self.property_data, 
            content_type='application/json'
        )
        create_data = json.loads(create_response.content)
        
        reject_data = {
            'user_property_id': create_data['user_property_id']
        }
        
        response = self.client.patch('/api/property/reject/',
            reject_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('rejected', data['message'])

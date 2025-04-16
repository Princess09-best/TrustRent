from django.test import TestCase, Client
from django.utils import timezone
from core.models import User, Property, UserProperty, PropertyImage
from ops.models import PropertyListing
import json

class PropertyListingTests(TestCase):
    databases = {'default', 'core'}

    def setUp(self):
        # Create test user
        self.user = User.objects.using('core').create(
            firstname='Test',
            lastname='User',
            email='test@example.com',
            phone_number='+233555555555',
            password_hash='hashed_password',
            role='property_owner',
            id_type='Ghana Card',
            id_value='GHA-123456789-0',
            is_verified=True,
            is_active=True,
            created_at=timezone.now()
        )

        # Create property
        self.property = Property.objects.using('core').create(
            title='Test Property',
            property_type='1_bedroom',
            description='A test property',
            location='Test Location',
            price=1000.00,
            status='unlisted',
            created_at=timezone.now()
        )

        # Create user property relationship
        self.user_property = UserProperty.objects.using('core').create(
            owner=self.user,
            property=self.property,
            is_verified=True,
            is_active=True,
            verification_status='approved',
            transaction_hash='',
            created_at=timezone.now()
        )

        # Upload property image
        self.property_image = PropertyImage.objects.using('core').create(
            property=self.property,
            image='test.jpg',
            is_active=True,
            uploaded_at=timezone.now()
        )

        self.client = Client()

    def test_create_listing_success(self):
        """Test creating a property listing with valid data"""
        data = {
            'user_property_id': self.user_property.id,
            'listing_type': 'rent',
            'price': 1000.00  # Add price field
        }
        response = self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Should be 201 for resource creation
        self.assertTrue('X-Listing-Id' in response.headers)  # Check header exists
        self.assertIsNotNone(response.headers['X-Listing-Id'])  # Check header has value
        
        # Check response body
        response_data = response.json()
        self.assertEqual(response_data['message'], 'Property listing created successfully')
        self.assertEqual(response_data['property_title'], 'Test Property')
        self.assertEqual(response_data['listing_type'], 'rent')
        self.assertEqual(response_data['price'], 1000.00)

    def test_create_listing_missing_fields(self):
        """Test creating a property listing with missing required fields"""
        data = {
            'user_property_id': self.user_property.id
        }
        response = self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_create_listing_unverified_property(self):
        """Test creating a listing for an unverified property"""
        # Update property to unverified
        self.user_property.is_verified = False
        self.user_property.save()

        data = {
            'user_property_id': self.user_property.id,
            'listing_type': 'rent'
        }
        response = self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_get_properties_success(self):
        """Test getting all listed properties"""
        # First create a listing
        data = {
            'user_property_id': self.user_property.id,
            'listing_type': 'rent'
        }
        self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = self.client.get('/api/properties/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('properties', response.json())
        self.assertIn('pagination', response.json())
        self.assertTrue(len(response.json()['properties']) > 0)

    def test_get_properties_with_filters(self):
        """Test getting properties with various filters"""
        # First create a listing
        data = {
            'user_property_id': self.user_property.id,
            'listing_type': 'rent'
        }
        self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        # Test with location filter
        response = self.client.get('/api/properties/?location=Test')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()['properties']) > 0)

        # Test with property type filter
        response = self.client.get('/api/properties/?type=1_bedroom')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()['properties']) > 0)

        # Test with price range
        response = self.client.get('/api/properties/?min_price=500&max_price=2000')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()['properties']) > 0)

    def test_get_property_detail_success(self):
        """Test getting detailed property information"""
        # First create a listing
        data = {
            'user_property_id': self.user_property.id,
            'listing_type': 'rent'
        }
        self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = self.client.get(f'/api/properties/{self.property.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.json())
        self.assertIn('property_type', response.json())
        self.assertIn('description', response.json())
        self.assertIn('location', response.json())
        self.assertIn('price', response.json())
        self.assertIn('images', response.json())
        self.assertIn('documents', response.json())

    def test_get_property_detail_not_found(self):
        """Test getting details of a non-existent property"""
        response = self.client.get('/api/properties/999999/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def tearDown(self):
        # Clean up test data
        PropertyListing.objects.filter(user_property=self.user_property).delete()
        self.user_property.delete()
        self.property.delete()
        self.user.delete() 
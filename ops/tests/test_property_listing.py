from django.test import TestCase, Client
from django.db import connections
from django.utils import timezone
import json

class PropertyListingTests(TestCase):
    databases = {'core', 'ops'}

    def setUp(self):
        # Create test user
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO core_user 
                (firstname, lastname, email, phone_number, password_hash, role, id_type, id_value, is_verified, is_active, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, [
                'Test', 'User', 'test@example.com', '+233555555555', 'hashed_password',
                'property_owner', 'Ghana Card', 'GHA-123456789-0', True, True, timezone.now()
            ])
            self.user_id = cursor.fetchone()[0]

            # Create property
            cursor.execute("""
                INSERT INTO core_property 
                (title, property_type, description, location, price, status, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, [
                'Test Property', '1_bedroom', 'A test property', 'Test Location',
                1000.00, 'unlisted', timezone.now()
            ])
            self.property_id = cursor.fetchone()[0]

            # Create user property relationship
            cursor.execute("""
                INSERT INTO core_userproperty 
                (owner_id, property_id, is_verified, is_active, verification_status, transaction_hash, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, [
                self.user_id, self.property_id, True, True, 'approved', '', timezone.now()
            ])
            self.user_property_id = cursor.fetchone()[0]

            # Upload property image
            cursor.execute("""
                INSERT INTO core_propertyimage 
                (property_id, image, is_active, uploaded_at) 
                VALUES (%s, %s, %s, %s)
            """, [
                self.property_id, 'test.jpg', True, timezone.now()
            ])

        self.client = Client()

    def test_create_listing_success(self):
        """Test creating a property listing with valid data"""
        data = {
            'user_property_id': self.user_property_id,
            'listing_type': 'rent'
        }
        response = self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('listing_id', response.json())
        self.assertIn('property_title', response.json())

    def test_create_listing_missing_fields(self):
        """Test creating a property listing with missing required fields"""
        data = {
            'user_property_id': self.user_property_id
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
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_verified = false 
                WHERE id = %s
            """, [self.user_property_id])

        data = {
            'user_property_id': self.user_property_id,
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
            'user_property_id': self.user_property_id,
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
            'user_property_id': self.user_property_id,
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
            'user_property_id': self.user_property_id,
            'listing_type': 'rent'
        }
        self.client.post(
            '/api/listing/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = self.client.get(f'/api/properties/{self.property_id}/')
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
        with connections['core'].cursor() as cursor:
            cursor.execute("DELETE FROM core_userproperty WHERE id = %s", [self.user_property_id])
            cursor.execute("DELETE FROM core_property WHERE id = %s", [self.property_id])
            cursor.execute("DELETE FROM core_user WHERE id = %s", [self.user_id])

        with connections['ops'].cursor() as cursor:
            cursor.execute("DELETE FROM ops_propertylisting WHERE user_property_id = %s", [self.user_property_id]) 